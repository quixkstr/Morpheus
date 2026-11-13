/*
  Morpheus pill dispenser: Arduino side.

  The Raspberry Pi sends one command per pill over USB serial and
  waits for the reply before sending the next.

      Pi -> Arduino    D2                dispense one pill from slot 2
      Arduino -> Pi    OK 2              done
      Arduino -> Pi    ERR 2 not wired   failed, with a short reason

  Test without the Pi: open the Serial Monitor at 9600 baud, line
  ending set to "Newline", and type D1.

  TO CONNECT YOUR MOTOR CODE: put your working 90 degree rotation
  inside rotate90() near the bottom. Nothing else needs to change.
*/

const long BAUD = 9600;          // must match BAUD in controller/motors.py

// One pill = this many 90 degree turns of the mechanism.
const int TURNS_PER_PILL = 1;

// Which slots have a motor connected. For the one-motor prototype only
// slot 1 is true. Set the others to true as their motors are added.
//                              slot:   1      2      3      4
const bool SLOT_WIRED[4] =          { true, false, false, false };

String line = "";

void setup() {
  Serial.begin(BAUD);
  pinMode(LED_BUILTIN, OUTPUT);
  setupMotors();
  Serial.println("READY");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      handle(line);
      line = "";
    } else if (c != '\r' && line.length() < 16) {
      line += c;
    }
  }
}

void handle(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;

  if (cmd == "PING") {
    Serial.println("READY");
    return;
  }

  if (cmd.length() == 2 && cmd[0] == 'D' && cmd[1] >= '1' && cmd[1] <= '4') {
    int slot = cmd[1] - '0';
    if (!SLOT_WIRED[slot - 1]) {
      Serial.print("ERR ");
      Serial.print(slot);
      Serial.println(" not wired");
      return;
    }
    for (int i = 0; i < TURNS_PER_PILL; i++) {
      rotate90(slot);
    }
    Serial.print("OK ");
    Serial.println(slot);
    return;
  }

  Serial.println("ERR unknown command");
}

/* ------------------------------------------------------------------
   Motor code. This is the part the hardware side owns.
   ------------------------------------------------------------------ */

// Runs once at power-up. Set pin modes or create stepper objects here.
void setupMotors() {
}

// Turn the given slot's mechanism 90 degrees and return when it has
// finished moving. The reply to the Pi is sent after this returns, so
// do not return early.
//
// PLACEHOLDER: this only flashes the on-board LED so the Pi link can
// be tested with no motor attached. Replace the body with your working
// rotation code. With one motor, you can ignore the slot number; with
// four, use it to pick which motor to step.
void rotate90(int slot) {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(400);
  digitalWrite(LED_BUILTIN, LOW);
  delay(200);
}
