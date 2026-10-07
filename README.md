# RPi5 + ROS 2 + RRC Lite

GitHub Pages site with setup instructions for a robot built from a **Raspberry Pi 5** and a
**Hiwonder RRC Lite** motor/servo controller (STM32F407), running **Ubuntu Server 24.04 LTS**
and **ROS 2 Jazzy (ros-base)**.

Adapted from [rpi4-ros2-multirobot](https://github.com/hmarthens1/rpi4-ros2-multirobot).

## Layout

```
index.md                 home page: the hardware, how the Pi talks to the RRC Lite, roadmap
Lab_01/index.md          Pi 5 setup: flash Ubuntu Server 24.04, SSH, networking, swap, ROS 2 Jazzy ros-base
Lab_01/code/
  setup_network.sh         netplan: wlan0 static IP / DHCP, Wi-Fi client/hotspot (runs on the Pi)
  setup_swap.sh            zram + /swapfile                                    (runs on the Pi)
  install_ros2.sh          the Lab 01 ROS 2 install steps in one script        (runs on the Pi)
Lab_02/index.md          the RRC Lite: identify the running firmware, back it up, flash new firmware from Linux
Lab_02/code/
  99-rrclite.rules         udev rule: /dev/rrclite, dialout group, ModemManager off (runs on the Pi)
  rrclite_probe.py         talks the RRC Lite serial protocol: listen, beep, battery, IMU
  flash_rrclite.sh         stm32flash wrapper: DTR/RTS boot sequence (or BOOT/RST buttons), back up, write, verify
Lab_02/img/
  autodownload.png         the auto-download circuit, cropped from Hiwonder's schematic
```

## Publishing

Settings → Pages → *Deploy from a branch* → `main` / `(root)`.
The theme (`pages-themes/hacker`) is loaded with `jekyll-remote-theme`, so no build workflow is needed.
