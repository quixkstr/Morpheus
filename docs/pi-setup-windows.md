# Raspberry Pi 4 setup from a Windows PC

The same setup as `pi-setup.md`, written for someone doing it from a Windows 10 or 11 computer. The commands that run on the Pi itself are identical; what differs is how you flash the card and how you connect to the Pi.

These steps have not yet been run on our Pi; fix anything that turns out wrong and update this file.

## What you need

- The Pi 4, its power supply, and a microSD card (16 GB or more)
- A microSD card reader (built into many laptops, or a USB one)
- Your home or phone-hotspot WiFi name and password, so the Pi can get online during setup

## 1. Flash the microSD card

1. Download Raspberry Pi Imager for Windows from https://www.raspberrypi.com/software/ and install it.
2. Put the microSD card in the reader and plug it in. If Windows offers to format the card, click Cancel.
3. Open Raspberry Pi Imager and choose:
   - **Device:** Raspberry Pi 4
   - **OS:** Raspberry Pi OS (64-bit)
   - **Storage:** your microSD card (check the size matches so you do not overwrite another drive)
4. Click Next, then **Edit Settings** when asked about OS customisation:
   - General tab: hostname `morpheus`, username `pi` with a password you will remember, your WiFi name and password, and your country for the WiFi region.
   - Services tab: enable SSH with password authentication.
5. Save, confirm, and let it write and verify. Windows may pop up "You need to format the disk" messages while it writes; close them without formatting.
6. When Imager says it is done, remove the card.

## 2. Boot the Pi and connect to it

1. Put the card in the Pi and plug in the power. Give it two or three minutes on first boot.
2. Open **Windows Terminal** or **PowerShell** (search for either in the Start menu; Windows includes an SSH client, so nothing extra to install) and run:

   ```powershell
   ssh pi@morpheus.local
   ```

   Type `yes` when asked about the host key, then the password you set.

3. If `morpheus.local` is not found, Windows is not resolving the Pi's name. Either:
   - Log in to your router and look for a device called `morpheus` in the connected devices list, then use its address: `ssh pi@192.168.x.x`, or
   - Install Apple's Bonjour Print Services for Windows, which adds `.local` name lookup, then try again.

   If you prefer a graphical client, PuTTY works the same way: host `morpheus.local` (or the address), port 22, user `pi`.

Everything from here on is typed into that SSH window and runs on the Pi, so it is the same as the main guide.

## 3. Update and install what the server needs

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y git python3-flask python3-serial
```

## 4. Get the code

```bash
cd ~
git clone https://github.com/quixkstr/Morpheus.git
```

This puts the repo at `/home/pi/Morpheus`, the path the service file expects.

## 5. Try the server by hand

```bash
cd ~/Morpheus/controller
sudo python3 server.py
```

On your Windows PC, open a browser to `http://morpheus.local` (or `http://192.168.x.x` using the Pi's address) and the app should appear. Tap Dispense: the motor stubs just wait, so the progress runs through with nothing moving. Back in the SSH window, press Ctrl+C to stop the server.

## 6. Install the server as a service so it starts on boot

```bash
sudo cp ~/Morpheus/controller/morpheus.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now morpheus
systemctl status morpheus
```

Press `q` to leave the status screen. Useful later:

```bash
sudo journalctl -u morpheus -f      # watch the server's log (Ctrl+C to stop)
sudo systemctl restart morpheus     # after changing the code
```

## 7. Turn the Pi into a hotspot

Do this last. The Pi drops off your WiFi when the hotspot starts, so your SSH window will freeze and disconnect; that is expected. Plug an Ethernet cable from the Pi to your router first if you want to stay connected.

```bash
sudo nmcli device wifi hotspot ifname wlan0 ssid Morpheus password morpheus1
sudo nmcli connection modify Hotspot connection.autoconnect yes connection.autoconnect-priority 100
```

The password must be at least 8 characters. The Pi's address on its own network is `10.42.0.1`.

## 8. Test from a phone or the PC

Join the `Morpheus` WiFi network and open `http://10.42.0.1`. The app should load. Windows and phones will warn that the network has no internet; that is expected.

To get back into the Pi over SSH while it is a hotspot, join the `Morpheus` network on your PC and run `ssh pi@10.42.0.1`.

## Updating the code on the Pi

```bash
cd ~/Morpheus && git pull && sudo systemctl restart morpheus
```

The Pi needs internet for `git pull`. Either plug in Ethernet, or switch back to your WiFi temporarily:

```bash
sudo nmcli connection up "<your wifi name>"   # back online
sudo nmcli connection up Hotspot              # back to hotspot
```

## Windows-specific things to know

- Do not open the microSD card in File Explorer after flashing and click Format, even if Windows suggests it. The card has Linux partitions Windows cannot read, which is normal.
- If `ssh` is "not recognized" in PowerShell, turn on the OpenSSH Client: Settings, System, Optional features, Add a feature, OpenSSH Client. Or use PuTTY.
- Copying a command from this file and pasting into Windows Terminal: right-click pastes. Make sure a multi-line block pasted all at once did not get cut off.
- If your PC is on a VPN, `.local` names and the `10.42.0.1` address may not reach the Pi. Turn the VPN off while setting up.

## Connecting the Arduino

The motors are driven by an Arduino Uno plugged into the Pi by USB. See `arduino-link.md` for uploading the sketch and connecting it.
