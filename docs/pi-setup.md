# Raspberry Pi 4 setup

How to get the Pi broadcasting its own WiFi network and serving the app. After this, a phone joins the `Morpheus` network and opens `http://10.42.0.1`.

Written for the current Raspberry Pi OS (Bookworm or newer), which uses NetworkManager. These steps have not yet been run on our Pi; fix anything that turns out wrong and update this file.

## 1. Flash and first boot

1. Flash Raspberry Pi OS (64-bit) with Raspberry Pi Imager.
2. In the Imager's settings: hostname `morpheus`, username `pi`, enable SSH, and enter your home WiFi so you can reach the Pi during setup.
3. Boot, then connect over SSH (`ssh pi@morpheus.local`) or with a monitor and keyboard.

## 2. Update and install what the server needs

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y git python3-flask python3-gpiozero
```

## 3. Get the code

```bash
cd ~
git clone https://github.com/quixkstr/Morpheus.git
```

This puts the repo at `/home/pi/Morpheus`, which is the path the service file expects. If you use a different username or location, edit the two paths in `controller/morpheus.service`.

## 4. Try the server by hand

```bash
cd ~/Morpheus/controller
sudo python3 server.py
```

From another device on the same network, open `http://morpheus.local` and you should see the app. Tap Dispense: the motor stubs just wait, so you will see the progress run through with nothing moving. Stop the server with Ctrl+C.

## 5. Install the server as a service so it starts on boot

```bash
sudo cp ~/Morpheus/controller/morpheus.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now morpheus
systemctl status morpheus
```

Useful later:

```bash
sudo journalctl -u morpheus -f      # watch the server's log
sudo systemctl restart morpheus     # after changing the code
```

## 6. Turn the Pi into a hotspot

Do this last, and plug in Ethernet first if you want to keep an SSH session, because the Pi drops off your home WiFi when the hotspot starts.

```bash
sudo nmcli device wifi hotspot ifname wlan0 ssid Morpheus password morpheus1
sudo nmcli connection modify Hotspot connection.autoconnect yes connection.autoconnect-priority 100
ip addr show wlan0
```

The password must be at least 8 characters. The last command should show the Pi at `10.42.0.1`.

## 7. Test from a phone

Join the `Morpheus` WiFi network, open `http://10.42.0.1`, and the app should load. The phone will warn that the network has no internet; that is expected.

## Updating the code on the Pi

```bash
cd ~/Morpheus && git pull && sudo systemctl restart morpheus
```

The Pi needs internet for `git pull`. Either plug in Ethernet, or switch back to home WiFi temporarily:

```bash
sudo nmcli connection up "<your home wifi name>"   # back online
sudo nmcli connection up Hotspot                    # back to hotspot
```

## Things to know

- One radio, one network: while the hotspot is on, the Pi has no WiFi internet.
- iPhones sometimes leave a WiFi network that has no internet and fall back to cellular. If the app will not load during a demo, briefly switch cellular data off on the phone.
- The server runs as root so it can use port 80 (so the address is just `http://10.42.0.1`) and the GPIO pins.
- The motor code is all in `controller/motors.py`. The server only ever calls `dispense_one(slot)`.
