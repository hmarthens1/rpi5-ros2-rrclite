---
layout: default
title: "Lab 01 — Raspberry Pi 5: Ubuntu Server & ROS 2"
---

# Lab 01 — Raspberry Pi 5: Ubuntu Server & ROS 2

**Raspberry Pi 5 · Hiwonder RRC Lite · Ubuntu Server 24.04 LTS · ROS 2 Jazzy (ros-base)**

**Objectives:** Flash Ubuntu Server 24.04 LTS (64-bit) to an SD card and boot the Pi 5 without a monitor. The Pi joins your Wi-Fi router on its own, so you connect over SSH, then give the Pi a **static Wi-Fi address**, update the system and add swap. Then install **ROS 2 Jazzy `ros-base`** and the build tools, check that ROS 2 works on the Pi and between the Pi and your laptop, and build a first workspace. Lab 02 then connects the RRC Lite controller.

---

## Before You Start

You will need:
- A **Raspberry Pi 5** (4, 8 or 16 GB). It has Wi-Fi built in
- A micro-SD card (32 GB or more, class **A2**) and a card reader
- For the bench: the official **27 W (5 V 5 A) USB-C** Pi 5 power supply
- The Pi 5 **Active Cooler** (or another heatsink with a fan). Without one, the Pi 5 slows down (throttles) during long `colcon` builds
- A **Wi-Fi router with internet access**, and a laptop (Windows, macOS or Linux) on it
- Access to the router's admin page (usually `http://192.168.0.1` or `http://192.168.1.1`)
- Optional: a micro-HDMI to HDMI cable, a monitor and a USB keyboard, for when the Pi doesn't show up on the network

### Plan the robot's name and address

| Hostname | wlan0 static IP | Gateway (router) | ROS namespace (later) |
|---|---|---|---|
| `robot01` | `192.168.0.11` | `192.168.0.1` | `/robot01` |

Use the first three numbers of **your** router's address. For more robots, use
`robot02` → `.12`, `robot03` → `.13`, and so on. Part 4.1 checks that the address is free.

> **Why `robot01` and not `rpi5-01`?** ROS names can't contain `-`, and hostnames can't
> contain `_`. A name made only of lowercase letters and digits works as both.

This guide uses **`robot01`** and user **`ubuntu`** in its examples.

### Power: one source at a time

The RRC Lite has a **5 V / 5 A USB-C output with USB-PD** made for the Pi 5 (on its
schematic: a SY8370 converter from the battery, and an IP2723T chip that tells the Pi
how much current it may draw). On the robot, the Pi is powered from there.

| Where you are | Power the Pi from |
|---|---|
| On the bench (Parts 1–10) | the 27 W USB-C supply |
| On the robot | the RRC Lite's **5 V PD output** → a USB-C to USB-C cable → the Pi's USB-C power input. Battery connected, the board's switch **ON** |

Only **one** cable into the Pi's USB-C power input at a time. Lab 02 adds a second
cable for data, from the board's **UART1** port to a Pi USB-A port. That one doesn't
power the Pi.

> **Why 5 A?** With a weaker supply (e.g. a 5 V 3 A phone charger) the Pi 5 limits its USB
> ports to 600 mA in total and prints a warning at boot. A camera or lidar on USB will
> then not work reliably. Check what the Pi negotiated, on the bench and on the robot:
>
> ```bash
> od -An -tu4 --endian=big /proc/device-tree/chosen/power/max_current    # 5000 = 5 A
> vcgencmd get_throttled                                                 # throttled=0x0
> ```
>
> If the robot's output gives less than 5000, add `usb_max_current_enable=1` to
> `/boot/firmware/config.txt` only if you're sure the supply can deliver 5 A.

> **Why Ubuntu 24.04 and not 22.04?** Ubuntu 22.04 doesn't support the Pi 5: its kernel
> is too old for the Pi 5's chips. 24.04 is the first LTS certified for the Pi 5, and
> ROS 2 **Jazzy** is the ROS 2 release with ready-built packages for 24.04.

---

## Part 1 — Flash Ubuntu Server to the SD card

### 1.1 Install Raspberry Pi Imager

Download and install **[Raspberry Pi Imager](https://www.raspberrypi.com/software/)** on your laptop.
Insert the SD card into the card reader and plug it in.

### 1.2 Choose the device, OS and storage

| Setting | Choose |
|---|---|
| **Device** | Raspberry Pi 5 |
| **OS** | Other general-purpose OS → Ubuntu → **Ubuntu Server 24.04.x LTS (64-bit)** |
| **Storage** | your SD card |

> Pick **Server**, not Desktop, and **24.04 LTS**, not a newer non-LTS release. ROS 2
> Jazzy packages exist for 24.04 only.

### 1.3 OS customisation: this replaces the monitor setup

When Imager asks **"Would you like to apply OS customisation settings?"**, choose
**Edit settings**. Newer Imager versions show these as steps in the wizard instead.

| Tab | Setting | Value |
|---|---|---|
| General | Hostname | `robot01` |
| General | Username / password | `ubuntu` / a password you will remember |
| General | Wireless LAN | **your router's** SSID + password + **Wireless LAN country** (e.g. `CA`) |
| General | Locale | your time zone and keyboard layout |
| Services | Enable SSH | ✅ *Use password authentication* |

Click **Save**, then **Yes**, then **Write**. The write and verify take about 5–10 minutes.

> **Check the Wi-Fi name and password twice.** A typo means the Pi never joins the router.
> The SSID is case-sensitive.

---

## Part 2 — First Boot

1. Insert the SD card into the Pi 5 (the slot is on the underside, opposite the USB ports).
2. Connect the **USB-C** supply. The status LED next to the SD slot lights; it flickers green while the SD card is read.

**Wait 3–5 minutes.** On first boot Ubuntu's `cloud-init` applies your Imager settings:
it creates your user, sets the hostname, joins your Wi-Fi and enables SSH. It may reboot
once. If you log in too early, you get `Permission denied` or no answer at all. Wait, then
try again.

> **Monitor?** You don't need one. To watch the boot, use **HDMI0**, the micro-HDMI port
> next to the USB-C socket, and a USB keyboard. Log in at the text console with your
> Imager user. `ip -br addr` shows the Pi's address.

### 2.1 Hostname skipped in Imager?

If you skipped the hostname, the Pi boots as **`ubuntu`**. Fix it at the console (or over
SSH, Part 3):

```bash
sudo hostnamectl set-hostname robot01
sudo sed -i 's/^127\.0\.1\.1.*/127.0.1.1 robot01/' /etc/hosts
echo "preserve_hostname: true" | sudo tee /etc/cloud/cloud.cfg.d/99-preserve-hostname.cfg
sudo reboot
```

The second line keeps `sudo` from warning *"unable to resolve host"*, the third stops
cloud-init from setting the old name again on the next boot.

---

## Part 3 — Connect from your laptop

### 3.1 Find the Pi's IP address

| Way | How | Look for |
|---|---|---|
| **Router admin page** (easiest) | `http://192.168.0.1` → *Connected devices* / *DHCP clients* | `robot01`, or a Pi MAC address |
| **Linux / macOS laptop** | `nmap -sn 192.168.0.0/24`, then `ip neigh` (Linux) or `arp -a` (macOS) | a line with a Pi MAC |
| **Windows laptop** | PowerShell: `arp -a` | a `192.168.0.x` entry with a Pi MAC |
| **At the Pi** | monitor + keyboard, `ip -br addr` | `wlan0  UP  192.168.0.3/24` |

**How to recognise the Pi:** its MAC address starts with a Raspberry Pi prefix, on the Pi 5
usually `2c:cf:67` or `d8:3a:dd` (also `dc:a6:32`, `e4:5f:01`, `88:a2:9e`, `28:cd:c1`).

### 3.2 SSH in

```bash
ssh ubuntu@<PI_IP>          # e.g. ssh ubuntu@192.168.0.3
```

Type `yes` to accept the host key the first time, then your password.

> **"REMOTE HOST IDENTIFICATION HAS CHANGED"** after re-flashing, or after the Pi moves to
> its static address, is expected: `ssh-keygen -R <PI_IP>`.

#### `Permission denied (publickey)`: turn on password login

The Pi accepts only SSH keys, because Imager's *Use password authentication* wasn't
applied. At the Pi's console (monitor + keyboard):

```bash
echo "PasswordAuthentication yes" | sudo tee /etc/ssh/sshd_config.d/01-password-auth.conf
sudo systemctl restart ssh
sudo sshd -T | grep -i passwordauthentication     # -> passwordauthentication yes
```

The SSH server uses the **first** value it reads, in file-name order, so `01-…` wins over
cloud-init's `50-cloud-init.conf`. Once SSH keys work (3.3) you can delete the file again.

### 3.3 Log in without a password (SSH keys)

On your **laptop**:

```bash
ssh-keygen -t ed25519                  # once; press Enter to accept the defaults
ssh-copy-id ubuntu@<PI_IP>             # macOS / Linux
```

On Windows (PowerShell), where `ssh-copy-id` doesn't exist:

```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh ubuntu@<PI_IP> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

For a graphical editor on the Pi's files, VS Code's **Remote - SSH** extension connects to
`ubuntu@<PI_IP>` (or `robot01` once Part 4.2 is done).

### 3.4 Get the lab scripts onto the Pi

```bash
mkdir -p ~/lab01 && cd ~/lab01
for f in setup_network.sh setup_swap.sh install_ros2.sh; do
  curl -fsSLO {{ site.github.url }}/Lab_01/code/$f
done
ls
```

The scripts: ⬇️ [setup_network.sh](code/setup_network.sh) ·
⬇️ [setup_swap.sh](code/setup_swap.sh) · ⬇️ [install_ros2.sh](code/install_ros2.sh)

> **`curl: (6) Could not resolve host`**: the Pi has no internet yet (`ping -c3 8.8.8.8`).
> Download the scripts on the laptop and copy them: `scp *.sh ubuntu@<PI_IP>:~/lab01/`

---

## Part 4 — Networking

Ubuntu Server sets up the network with **netplan** YAML files in `/etc/netplan/`. On first
boot, cloud-init wrote `/etc/netplan/50-cloud-init.yaml` with the Wi-Fi you gave Imager,
using DHCP.

### 4.1 Static IP on wlan0

The router's DHCP address can change after a reboot. A static address never does.

**Step 1 — your router's details.** On the Pi:

```bash
ip -br addr show wlan0     # current address and prefix, e.g. 192.168.0.3/24
ip route | grep default    # the router: "default via 192.168.0.1 dev wlan0"
```

**Step 2 — make sure the address is free.** In the router's admin page, find the **DHCP
address pool**. `192.168.0.11` must be **outside** it (e.g. pool `.100`–`.199`). If the pool
covers the whole network, move its start to `.100`. Then, on the Pi:

```bash
ping -c2 192.168.0.11      # "Destination Host Unreachable" or 100% loss = free
```

**Step 3 — set it.** Both methods change the address of the connection you are using, so
**the SSH session freezes** when you apply it. Wait about 20 seconds and connect to the new address.

#### Method A — write the netplan file by hand

```bash
sudo nano /etc/netplan/99-wlan0-static.yaml
```

```yaml
network:
  version: 2
  wifis:
    wlan0:
      dhcp4: false
      addresses: [192.168.0.11/24]
      routes:
        - to: default
          via: 192.168.0.1
      nameservers:
        addresses: [192.168.0.1, 8.8.8.8]
```

The file starts with `99-`, so it is read last: netplan merges it over `50-cloud-init.yaml`,
which still provides the Wi-Fi name and password. **Spaces, never Tab**, 2 per level.

```bash
sudo chmod 600 /etc/netplan/99-wlan0-static.yaml
echo "network: {config: disabled}" | sudo tee /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
sudo netplan generate          # no output = no mistakes
sudo netplan apply             # the SSH session freezes here
```

Undo: `sudo rm /etc/netplan/99-wlan0-static.yaml && sudo netplan apply`.

#### Method B — the `setup_network.sh` script

⬇️ [setup_network.sh](code/setup_network.sh). Edit the SETTINGS block, then run it:

```bash
cd ~/lab01
nano setup_network.sh
```

```bash
WIFI_MODE="keep"                  # keep the Wi-Fi network from Imager
WIFI_IPV4="static"
WIFI_ADDRESS="192.168.0.11/24"
WIFI_GATEWAY="192.168.0.1"        # <- your router
DNS_SERVERS="192.168.0.1,8.8.8.8"
```

```bash
sudo bash setup_network.sh
```

It refuses an address that another device already uses, backs up the old netplan files,
checks the new file before applying it, and keeps going if the SSH session drops.
`--show` prints the current config, `--restore` puts the old one back.

**Reconnect** from the laptop, then check on the Pi:

```bash
ssh-keygen -R 192.168.0.11     # only if SSH complains about a changed host key
ssh ubuntu@192.168.0.11
ip -br addr show wlan0         # -> wlan0  UP  192.168.0.11/24
ping -c3 google.com            # internet and DNS work?
```

### 4.2 Reach the Pi by name

```bash
sudo apt update
sudo apt install -y avahi-daemon
```

Now `ssh ubuntu@robot01.local` works. On the laptop, add to `~/.ssh/config`:

```
Host robot01
    HostName 192.168.0.11
    User ubuntu
```

Then `ssh robot01`, `scp` and VS Code all use the short name.

### 4.3 The router must let ROS 2 through

ROS 2 finds other machines with **multicast** on the local network. The router must keep
the Pi and the laptop on the same subnet, with *AP isolation* / *client isolation* **off**.
Home and lab routers do this by default; campus and guest Wi-Fi usually doesn't.

### 4.4 Turn off Wi-Fi power saving

The Pi's Wi-Fi dozes between packets, which delays ROS 2 traffic. Turn it off at every boot:

```bash
sudo apt install -y iw
sudo tee /etc/systemd/system/wifi-powersave-off.service >/dev/null <<'EOF'
[Unit]
Description=Turn off Wi-Fi power saving on wlan0
Wants=sys-subsystem-net-devices-wlan0.device
After=sys-subsystem-net-devices-wlan0.device

[Service]
Type=oneshot
ExecStart=/usr/sbin/iw dev wlan0 set power_save off
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now wifi-powersave-off.service
iw dev wlan0 get power_save       # -> Power save: off
```

---

## Part 5 — Update the System and the Clock

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

> **`Could not get lock /var/lib/dpkg/lock-frontend`**: on first boot,
> `unattended-upgrades` installs security updates in the background. Wait a few minutes.

Check the clock. A wrong date makes `apt` reject repositories (*"Release file is not valid
yet"*) and makes ROS 2 timestamps wrong:

```bash
timedatectl                                        # "System clock synchronized: yes"
sudo timedatectl set-timezone America/Vancouver    # your zone: timedatectl list-timezones
```

> **The Pi 5 has a real-time clock**, but it only keeps time while the Pi is off if a
> battery is plugged into the **BAT** connector. Without one, the Pi needs internet (NTP)
> after every power-on to get the right time.

### 5.1 Pi 5 firmware (EEPROM)

The Pi 5 boots from firmware in an EEPROM on the board. A recent version fixes boot and
power issues. Check it, and update it if the tool offers to:

```bash
sudo apt install -y rpi-eeprom
sudo rpi-eeprom-update          # shows CURRENT and LATEST
sudo rpi-eeprom-update -a       # only if an update is available, then:
sudo reboot
```

---

## Part 6 — Memory Swap

Installing ROS 2 from `apt` needs little memory. **Building** C++ packages with `colcon`
can run a 4 GB Pi out of memory, and Ubuntu Server has no swap by default.

⬇️ [setup_swap.sh](code/setup_swap.sh)

```bash
cd ~/lab01
sudo bash setup_swap.sh
```

This sets up **zram** (compressed swap in RAM: fast, no SD card wear) and a **2 GB
`/swapfile`** as a safety net. `--status` shows it, `--uninstall` removes it.

---

## Part 7 — Prepare for ROS 2

### 7.1 UTF-8 locale

```bash
locale                                    # look for UTF-8
sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### 7.2 Universe repository and tools

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository -y universe
sudo apt install -y curl git htop usbutils iw python3-serial
sudo apt install -y raspi-utils || sudo apt install -y libraspberrypi-bin
```

| Tool | Used for |
|---|---|
| `usbutils` | `lsusb`: lists USB devices. Lab 02 uses it to find the RRC Lite |
| `iw` | Wi-Fi signal, country and power-saving state |
| `python3-serial` | `pyserial`, which Hiwonder's ROS 2 package and Lab 02's scripts use |
| `raspi-utils` | `vcgencmd`: under-voltage and throttling flags, temperature |

> **`pip install` says `externally-managed-environment`.** Ubuntu 24.04 blocks `pip` from
> changing the system's Python. Install Python libraries with `apt` (`python3-<name>`)
> whenever one exists, as above.

Check power and temperature:

```bash
vcgencmd get_throttled          # throttled=0x0 = no under-voltage, no throttling
vcgencmd measure_temp           # under ~70 °C at idle with the Active Cooler
```

---

## Part 8 — Install ROS 2 Jazzy (ros-base)

> **ros-base, not desktop.** `ros-jazzy-ros-base` has the communication libraries,
> messages and command-line tools. `ros-jazzy-desktop` adds RViz, rqt and other GUI tools
> that a headless Pi can't show. Run those on the laptop.

### Pick a `ROS_DOMAIN_ID`

ROS 2 machines on the same network find each other automatically. Only machines with the
same **domain ID** (0–101) see each other's topics. Pick one number for the robot **and**
your laptop, different from anyone else's ROS 2 on that network (the default, 0, is what
everyone else uses). This lab uses **`17`**.

Pick **one** way to install:

| | Option A — `install_ros2.sh` | Option B — step by step |
|---|---|---|
| What | one script runs 8.1–8.5 | you type each command |
| Best for | a second robot, or a re-install | the first time, to see what each step does |

Both follow the official
[ROS 2 Jazzy — Ubuntu (deb packages)](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html) guide.

### Option A — the script

⬇️ [install_ros2.sh](code/install_ros2.sh)

```bash
cd ~/lab01
nano install_ros2.sh                 # set ROS_DOMAIN_ID in the SETTINGS block
sudo bash install_ros2.sh
```

It is safe to run again. To change only the domain ID later:
`sudo bash install_ros2.sh --env-only`. When it finishes, **open a new SSH session** and
go to [Part 9](#part-9--test-ros-2).

### Option B — by hand

#### 8.1 Add the ROS 2 apt repository

The **`ros2-apt-source`** package installs the repository's signing key and address, and
keeps both up to date:

```bash
sudo apt update && sudo apt install -y curl
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
echo $ROS_APT_SOURCE_VERSION              # e.g. 1.3.0 - empty means the lookup failed
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
```

> Older guides use `curl … ros.key` and a hand-written `ros2.list` file. That key expired
> in June 2025. Use the package above.

#### 8.2 Upgrade first

```bash
sudo apt update
sudo apt full-upgrade -y
```

The new repository can bring updates of system packages. Installing ROS 2 on an
out-of-date system can make apt want to **remove** important packages.

#### 8.3 Install ros-base and the development tools

```bash
sudo apt install -y ros-jazzy-ros-base ros-dev-tools
sudo apt install -y ros-jazzy-demo-nodes-cpp ros-jazzy-demo-nodes-py
```

| Package | What you get |
|---|---|
| `ros-jazzy-ros-base` | the ROS 2 libraries, standard messages, `ros2` command line, launch, message generators |
| `ros-dev-tools` | `colcon` (build tool), `rosdep` (installs dependencies), `vcstool`, compilers |
| `ros-jazzy-demo-nodes-*` | `talker` and `listener`, for Part 9 |

#### 8.4 rosdep

`rosdep` installs the system packages that a ROS package depends on. `init` needs `sudo`,
`update` must **not** use it:

```bash
sudo rosdep init
rosdep update
```

#### 8.5 Environment in `~/.bashrc`

Add these lines to the end of `~/.bashrc` (`nano ~/.bashrc`), with your domain ID:

```bash
# >>> ROS 2 (install_ros2.sh) >>>
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=17
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
[ -f ~/ros2_ws/install/setup.bash ] && source ~/ros2_ws/install/setup.bash
[ -f /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash ] && source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash
# <<< ROS 2 (install_ros2.sh) <<<
```

| Line | Why |
|---|---|
| `source /opt/ros/jazzy/setup.bash` | puts `ros2` and the ROS libraries on the path |
| `ROS_DOMAIN_ID=17` | your number from above |
| `ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET` | find other machines on the network, not only this Pi. Jazzy replaces Humble's `ROS_LOCALHOST_ONLY` with this |
| `~/ros2_ws/install/setup.bash` | your own packages, once the workspace is built (Part 10) |
| `colcon-argcomplete` | Tab completion for `colcon` |

Then **log out and SSH in again**, or `source ~/.bashrc`. Check:

```bash
printenv | grep ROS
# ROS_VERSION=2
# ROS_DISTRO=jazzy
# ROS_DOMAIN_ID=17
# ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
```

---

## Part 9 — Test ROS 2

### 9.1 On the Pi

Open **two** SSH sessions to `robot01`. In the first:

```bash
ros2 run demo_nodes_cpp talker
# [INFO] [talker]: Publishing: 'Hello World: 1'
```

In the second:

```bash
ros2 run demo_nodes_py listener
# [INFO] [listener]: I heard: [Hello World: 1]
```

That tests both the C++ and the Python side. Useful commands while the talker runs:

```bash
ros2 node list                 # /talker
ros2 topic list                # /chatter, /parameter_events, /rosout
ros2 topic hz /chatter         # ~1 Hz
```

> **One SSH session only?** `sudo apt install tmux` splits one session into several, or run
> `ros2 run demo_nodes_cpp talker &`, then the listener, then `kill %1`.

### 9.2 From your laptop

The laptop needs ROS 2 **Jazzy** on the same network with the same `ROS_DOMAIN_ID`:

- **Ubuntu 24.04 laptop:** install `ros-jazzy-desktop` with the steps from Part 8
- **Windows / macOS:** a Ubuntu 24.04 virtual machine with **bridged** networking (NAT hides it from the Pi)

```bash
# on the laptop, while robot01 runs the talker
export ROS_DOMAIN_ID=17
ros2 topic echo /chatter
```

> **Nothing received?** In order: same `ROS_DOMAIN_ID` on both? Can they `ping` each
> other? Does multicast pass (`ros2 multicast receive` on one side, `ros2 multicast send` on
> the other)? Then `ros2 daemon stop` on both and try again.

> **Use the same middleware everywhere.** Jazzy's default is Fast DDS (`rmw_fastrtps_cpp`).
> If the laptop sets `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`, unset it, or install
> `ros-jazzy-rmw-cyclonedds-cpp` on the Pi and set the same variable there.

### 9.3 A namespace for the robot

Every node and topic of this robot will live under `/<hostname>/…`, so a second robot
running the same code never mixes with it:

```bash
ros2 run demo_nodes_cpp talker --ros-args -r __ns:=/$(hostname)
ros2 topic list                # -> /robot01/chatter
```

---

## Part 10 — A first workspace

Your own ROS 2 packages live in a **workspace**, built with `colcon`. Lab 02 puts
Hiwonder's RRC Lite package here.

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python hello_robot --node-name hello
cd ~/ros2_ws
colcon build --symlink-install
source ~/.bashrc
ros2 run hello_robot hello            # -> Hi from hello_robot.
```

| Folder | Contents |
|---|---|
| `src/` | your packages' source code. The only folder you edit |
| `build/` | intermediate build files |
| `install/` | the built packages. `install/setup.bash` loads them |
| `log/` | build logs |

---

## Troubleshooting

| Problem | Try this |
|---------|---------|
| Nothing happens at power-on | Check the supply and the SD card. A red-only LED with no green flicker = the SD card isn't readable: re-flash it |
| Boot warning about the power supply / USB current limited | Use the 27 W (5 V 5 A) Pi 5 supply, or on the robot the RRC Lite's 5 V PD output with the battery charged. Check `max_current` (*Power*) |
| `vcgencmd get_throttled` isn't `0x0` | `0x50005` or similar = under-voltage now / since boot: better supply. `0x80008` = soft temperature limit: fit the Active Cooler |
| The Pi never appears on the router | Wrong Wi-Fi name, password or country in Imager. Check at the console (`networkctl status wlan0`), or re-flash |
| `Permission denied (publickey)` | Password login is off: Part 3.2 |
| `sudo: unable to resolve host ...` | `/etc/hosts` still has the old name (Part 2.1) |
| `netplan generate` error about indentation | A Tab or a wrong number of spaces in the YAML |
| Pi unreachable after setting the static IP | Wait a minute and try the new address. Still nothing: monitor + keyboard, then undo (Method A) or `sudo bash ~/lab01/setup_network.sh --restore` (Method B). A cable from the Pi to the router gives eth0 a DHCP address to SSH into |
| `Release file ... is not valid yet` | The clock is wrong: `timedatectl`, internet connection (Part 5) |
| `ROS_APT_SOURCE_VERSION` is empty | The GitHub lookup failed. Wait a minute, or set it by hand from the [releases page](https://github.com/ros-infrastructure/ros-apt-source/releases) |
| `NO_PUBKEY` / `EXPKEYSIG` for packages.ros.org | An old `ros2.list` / `ros.key`: `sudo rm /etc/apt/sources.list.d/ros2.list /usr/share/keyrings/ros-archive-keyring.gpg`, then Part 8.1 |
| `Unable to locate package ros-jazzy-ros-base` | The repository is missing, or the image is not 24.04 `noble` / `arm64`: `apt policy ros-jazzy-ros-base`, `dpkg --print-architecture` |
| apt wants to **remove** many packages | Stop (answer `n`). `sudo apt full-upgrade` first (Part 8.2) |
| `ros2: command not found` | `source ~/.bashrc`, and check the block from Part 8.5 |
| `rosdep update` was run with `sudo` | `sudo chown -R $USER: ~/.ros`, then `rosdep update` |
| Talker and listener work on the Pi, the laptop sees nothing | Domain ID, a VM with NAT instead of bridged networking, a different RMW, the laptop's firewall or VPN, or the router isolates clients (4.3) |
| `pip install` → `externally-managed-environment` | Use `sudo apt install python3-<name>` (Part 7.2) |
| Build killed / `c++: fatal error: Killed signal` | Out of memory: Part 6, then `colcon build --parallel-workers 1` |

---

## Completion Checklist

- [ ] SD card flashed with Ubuntu Server 24.04 LTS (64-bit), hostname, user, SSH and Wi-Fi set in Imager
- [ ] `hostname` prints `robot01`, and `ssh robot01` works from the laptop with an SSH key
- [ ] Static IP on wlan0 (`192.168.0.11`), outside the router's DHCP pool; `ping google.com` works on the Pi
- [ ] `avahi-daemon` installed, Wi-Fi power saving off
- [ ] System updated, clock synchronised, EEPROM firmware up to date
- [ ] `vcgencmd get_throttled` → `throttled=0x0`
- [ ] Swap configured: `sudo bash setup_swap.sh --status`
- [ ] `ros-jazzy-ros-base`, `ros-dev-tools` and the demo nodes installed; `rosdep` initialised
- [ ] `~/.bashrc` sources ROS 2 and sets `ROS_DOMAIN_ID`
- [ ] Talker → listener works on the Pi, and the laptop hears the Pi's talker
- [ ] `~/ros2_ws` builds and `ros2 run hello_robot hello` works

**Next:** [Lab 02 — RRC Lite Firmware](../Lab_02/)
