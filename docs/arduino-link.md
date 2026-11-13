# Pi to Arduino link

The Arduino Uno R3 drives the stepper motors. The Pi tells it what to do over the USB cable that connects them.

```
phone (app)  --WiFi-->  Pi (controller/server.py)  --USB-->  Arduino (arduino/morpheus)  -->  motors
```

The Pi side has been tested against a simulated Arduino only. It has not yet been run against the real board.

## Messages

Plain text, one message per line, 9600 baud. The Pi sends one command per pill and waits for the reply before sending the next, so the app's progress display follows the real mechanism.

| Direction | Message | Meaning |
|---|---|---|
| Pi to Arduino | `D2` | Dispense one pill from slot 2 |
| Arduino to Pi | `OK 2` | Done |
| Arduino to Pi | `ERR 2 not wired` | Failed. The reason is shown in the app. |
| Pi to Arduino | `PING` | Arduino answers `READY` (for testing) |

If the Arduino does not answer within 10 seconds, the Pi reports a fault to the app.

## Arduino: add the motor code and upload

1. Open `arduino/morpheus/morpheus.ino` in the Arduino IDE.
2. Put your working 90 degree rotation code inside `rotate90()`, and any pin setup inside `setupMotors()`. As uploaded, `rotate90()` only flashes the on-board LED, so the link can be tested with no motor.
3. Check the two settings at the top:
   - `TURNS_PER_PILL`: how many 90 degree turns release one pill (1 by default).
   - `SLOT_WIRED`: which slots have a motor. Only slot 1 is on for the prototype.
4. Upload to the Uno.
5. Test from the IDE before involving the Pi: open the Serial Monitor at 9600 baud with line ending "Newline", type `D1`, and the mechanism should turn once and print `OK 1`. `D2` should print `ERR 2 not wired`.

Close the Serial Monitor before plugging the Uno into the Pi. Only one program can use the port at a time.

## Pi: install and connect

```bash
sudo apt install -y python3-serial
cd ~/Morpheus && git pull
sudo systemctl restart morpheus
```

Plug the Uno into any USB port on the Pi. Check the Pi sees it:

```bash
ls /dev/ttyACM* /dev/ttyUSB*
sudo journalctl -u morpheus -n 20
```

A genuine Uno appears as `/dev/ttyACM0`; most clones appear as `/dev/ttyUSB0`. The log should say `Arduino connected on ...`. The server finds the port by itself. To force one, add this line under `[Service]` in `/etc/systemd/system/morpheus.service`, then run `sudo systemctl daemon-reload && sudo systemctl restart morpheus`:

```
Environment=MORPHEUS_PORT=/dev/ttyACM0
```

Then open the app, set pill 1 to a count of 2, and dispense. The mechanism should turn twice.

## Going from one motor to four

Nothing changes in the app, the server, or the messages. On the Arduino:

1. Wire the extra motors.
2. Make `rotate90(slot)` step the motor for the slot it is given.
3. Set that slot to `true` in `SLOT_WIRED` and upload.

## Things to know

- **Power the motors separately.** Do not run stepper motors from the Uno's 5V pin or from USB power. Give the driver board its own supply and connect that supply's ground to an Arduino GND pin. Otherwise the Uno can reset mid-dispense, which shows up in the app as "The Arduino did not answer".
- **The Uno restarts when the Pi opens the port.** The Pi waits two seconds for it to boot and then keeps the port open, so this only happens once when the server starts.
- **Plugging in later is fine.** The server starts without an Arduino and tries to connect on each dispense.
- **`rotate90()` must not return until the motor has stopped,** because `OK` is sent as soon as it returns.
