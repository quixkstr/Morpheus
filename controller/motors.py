"""
Motor control for the four dispensing slots.

This is the file the hardware side owns. The server only calls
dispense_one(slot), so everything about how a pill is physically
released lives here. The version below is a stub that just waits,
so the whole system can be tested before the mechanism exists.

When the real mechanism is ready, replace the body of dispense_one().
Two common starting points:

  Servo (one per slot, via the PWM pins or a PCA9685 board):
      from gpiozero import AngularServo
      SERVOS = {1: AngularServo(17), 2: AngularServo(27), ...}
      def dispense_one(slot):
          s = SERVOS[slot]
          s.angle = 90;  time.sleep(0.4)
          s.angle = 0;   time.sleep(0.4)

  Stepper (one per slot, via a driver board such as ULN2003 or A4988):
      step the motor through one gear tooth, then stop.

Raise DispenseError if the slot is empty or jammed so the app can
show it. Slot numbers are 1 to 4.
"""

import time

# How long the stub pretends one pill takes. Tune to match the real mechanism.
STUB_SECONDS = 0.6


class DispenseError(Exception):
    """Raised when a pill could not be released (jam, empty slot, hardware fault)."""


def setup():
    """Called once when the server starts. Initialise pins or driver boards here."""
    pass


def dispense_one(slot: int) -> None:
    """Release exactly one pill from the given slot (1 to 4). Blocks until done."""
    if slot not in (1, 2, 3, 4):
        raise DispenseError(f"No such slot: {slot}")
    time.sleep(STUB_SECONDS)


def shutdown():
    """Called when the server stops. Release pins or park motors here."""
    pass
