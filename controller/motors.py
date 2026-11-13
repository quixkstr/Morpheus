"""
Motor control for the four dispensing slots.

The motors are driven by an Arduino Uno plugged into the Pi by USB.
This file is the Pi's side of that link: the server calls
dispense_one(slot), and this sends one command to the Arduino and
waits for its reply.

Messages (plain text, one per line, 9600 baud):
    Pi -> Arduino    D2                dispense one pill from slot 2
    Arduino -> Pi    OK 2              done
    Arduino -> Pi    ERR 2 not wired   failed; the reason is shown in the app

The Arduino side is arduino/morpheus/morpheus.ino.

The server starts even when no Arduino is plugged in. Each dispense
tries to connect if needed, so the Arduino can be plugged in later
without restarting anything.
"""

import glob
import os
import time

import serial  # sudo apt install python3-serial

BAUD = 9600
REPLY_TIMEOUT = 10.0   # seconds to wait for the Arduino to finish one pill
BOOT_WAIT = 2.0        # an Uno restarts when its port is opened; let it boot

# Set MORPHEUS_PORT to force a port, e.g. MORPHEUS_PORT=/dev/ttyACM0
PORT_OVERRIDE = os.environ.get("MORPHEUS_PORT")

_link = None


class DispenseError(Exception):
    """Raised when a pill could not be released (jam, empty slot, no Arduino)."""


def find_port():
    """Return the Arduino's serial port, or None if nothing is plugged in."""
    if PORT_OVERRIDE:
        return PORT_OVERRIDE
    # A genuine Uno appears as ttyACM*, most clones as ttyUSB*.
    for pattern in ("/dev/serial/by-id/*rduino*", "/dev/ttyACM*", "/dev/ttyUSB*"):
        found = sorted(glob.glob(pattern))
        if found:
            return found[0]
    return None


def connect():
    """Open the link to the Arduino if it is not already open."""
    global _link
    if _link is not None and _link.is_open:
        return _link
    port = find_port()
    if port is None:
        raise DispenseError("Arduino not found. Check the USB cable.")
    try:
        _link = serial.Serial(port, BAUD, timeout=REPLY_TIMEOUT)
    except serial.SerialException as e:
        _link = None
        raise DispenseError(f"Could not open the Arduino on {port}: {e}")
    time.sleep(BOOT_WAIT)
    _link.reset_input_buffer()  # discard the Arduino's start-up message
    return _link


def disconnect():
    global _link
    if _link is not None:
        try:
            _link.close()
        except Exception:
            pass
    _link = None


def setup():
    """Called once when the server starts."""
    try:
        connect()
        print(f"Arduino connected on {_link.port}")
    except DispenseError as e:
        print(f"Warning: {e} The server will keep trying on each dispense.")


def dispense_one(slot: int) -> None:
    """Release exactly one pill from the given slot (1 to 4). Blocks until done."""
    if slot not in (1, 2, 3, 4):
        raise DispenseError(f"No such slot: {slot}")

    link = connect()
    try:
        link.reset_input_buffer()
        link.write(f"D{slot}\n".encode("ascii"))
        link.flush()
        reply = link.readline().decode("ascii", errors="replace").strip()
    except (serial.SerialException, OSError) as e:
        disconnect()  # unplugged mid-job; reconnect on the next try
        raise DispenseError(f"Lost the connection to the Arduino: {e}")

    if not reply:
        raise DispenseError(f"The Arduino did not answer for slot {slot}.")
    if reply == f"OK {slot}":
        return
    if reply.startswith("ERR"):
        reason = reply[3:].strip()
        if reason.startswith(str(slot)):
            reason = reason[len(str(slot)):].strip()
        raise DispenseError(f"Slot {slot}: {reason or 'the Arduino reported a fault'}")
    raise DispenseError(f"Unexpected reply from the Arduino: {reply!r}")


def shutdown():
    """Called when the server stops."""
    disconnect()
