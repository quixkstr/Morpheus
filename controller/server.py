"""
Morpheus controller server.

Runs on the Raspberry Pi. It does two jobs:
  1. Serves the app (index.html in the repo root) so a phone on the
     Pi's WiFi can open it at http://10.42.0.1
  2. Accepts dispense requests from the app and drives the motors.

Endpoints
  GET  /          the app
  POST /dispense  body: {"dispense": [{"slot": 1, "count": 2}, ...]}
                  starts dispensing in the background; 409 if already busy
  GET  /status    current progress, polled by the app while dispensing
  POST /reset     clears a finished or failed job so a new one can start

Run by hand for testing:   sudo python3 controller/server.py
On the Pi it runs as a systemd service; see docs/pi-setup.md
"""

import threading
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

import motors

ROOT = Path(__file__).resolve().parent.parent  # repo root, where index.html lives
PORT = 80
MAX_PER_SLOT = 10
SLOTS = (1, 2, 3, 4)

app = Flask(__name__, static_folder=None)

# Shared progress record. Only the worker thread writes it while a job runs.
state = {
    "state": "idle",          # idle | dispensing | done | error
    "job": [],                # [{"slot": 1, "count": 2}, ...]
    "dispensed": {s: 0 for s in SLOTS},
    "current_slot": None,
    "error": None,
    "updated": time.time(),
}
lock = threading.Lock()


def touch(**changes):
    with lock:
        state.update(changes)
        state["updated"] = time.time()


def snapshot():
    with lock:
        return {
            **state,
            "dispensed": {str(k): v for k, v in state["dispensed"].items()},
        }


def worker(job):
    try:
        for item in job:
            slot = item["slot"]
            for _ in range(item["count"]):
                touch(current_slot=slot)
                motors.dispense_one(slot)
                with lock:
                    state["dispensed"][slot] += 1
                    state["updated"] = time.time()
        touch(state="done", current_slot=None)
    except motors.DispenseError as e:
        touch(state="error", error=str(e), current_slot=None)
    except Exception as e:  # anything unexpected still gets reported to the app
        touch(state="error", error=f"Controller fault: {e}", current_slot=None)


def parse_job(body):
    """Validate the request body and return a clean job list, or raise ValueError."""
    if not isinstance(body, dict) or not isinstance(body.get("dispense"), list):
        raise ValueError('Body must be {"dispense": [...]}')
    job, seen = [], set()
    for item in body["dispense"]:
        try:
            slot, count = int(item["slot"]), int(item["count"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("Each item needs an integer slot and count")
        if slot not in SLOTS:
            raise ValueError(f"Slot must be 1 to 4, got {slot}")
        if slot in seen:
            raise ValueError(f"Slot {slot} listed twice")
        if not 0 <= count <= MAX_PER_SLOT:
            raise ValueError(f"Count for slot {slot} must be 0 to {MAX_PER_SLOT}")
        seen.add(slot)
        if count:
            job.append({"slot": slot, "count": count})
    if not job:
        raise ValueError("Nothing to dispense")
    return job


@app.get("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.get("/status")
def status():
    return jsonify(snapshot())


@app.post("/dispense")
def dispense():
    try:
        job = parse_job(request.get_json(silent=True))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    with lock:
        if state["state"] == "dispensing":
            return jsonify({"error": "Already dispensing"}), 409
        state.update(
            state="dispensing",
            job=job,
            dispensed={s: 0 for s in SLOTS},
            current_slot=None,
            error=None,
            updated=time.time(),
        )
    threading.Thread(target=worker, args=(job,), daemon=True).start()
    return jsonify(snapshot()), 202


@app.post("/reset")
def reset():
    with lock:
        if state["state"] == "dispensing":
            return jsonify({"error": "Cannot reset while dispensing"}), 409
        state.update(state="idle", job=[], dispensed={s: 0 for s in SLOTS},
                     current_slot=None, error=None, updated=time.time())
    return jsonify(snapshot())


@app.after_request
def no_cache(resp):
    # The phone should always load the newest index.html after a git pull.
    resp.headers["Cache-Control"] = "no-store"
    return resp


if __name__ == "__main__":
    motors.setup()
    try:
        app.run(host="0.0.0.0", port=PORT, threaded=True)
    finally:
        motors.shutdown()
