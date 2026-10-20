---
layout: default
title: "Lab 04 — Lidar & Hector SLAM"
---

# Lab 04 — Lidar & Hector SLAM

**Raspberry Pi 5 · Oradar MS200 lidar · ROS 2 Jazzy · Hector SLAM (ROS 2 port) · RViz**

**Objectives:** Connect a 360° lidar to the Pi and understand what it sends: the serial
link, the packet layout and its CRC. Give it a fixed device name, run this lab's driver
to publish a ROS 2 `LaserScan`, and place the lidar on the robot with a TF frame. Then
build **Hector SLAM** from source, on the laptop or on the Pi, and draw a map of a room in
RViz by moving the robot through it. Finish by saving the map in the format Nav2 loads.

---

## Before You Start

- **Labs 01 and 02 are done**: the Pi runs ROS 2 Jazzy on `ROS_DOMAIN_ID=17`, and the
  laptop sees its topics (Lab 01, Part 9.2)
- An **Oradar MS200** lidar (the one in Hiwonder's MentorPi kits) with its USB adapter
  board (a **CH340** USB-serial chip, USB ID `1a86:7523`), mounted on top of the robot with
  nothing taller than it around it
- On the laptop: ROS 2 with **RViz** (`ros-jazzy-desktop` on Ubuntu 24.04). ROS 2 **Humble**
  on Ubuntu 22.04 works too, with Cyclone DDS on both sides (Part 6.3)
- For mapping, a room with some furniture, and either a way to drive the robot slowly
  (Part 7.2) or your hands: Hector SLAM needs **no odometry**, so you can carry the robot

Get the lab's files, on the **Pi**:

```bash
mkdir -p ~/lab04 && cd ~/lab04
for f in 99-ms200-lidar.rules ms200_node.py lidar.launch.py hector.launch.py hector.rviz; do
  curl -fsSLO {{ site.github.url }}/Lab_04/code/$f
done
```

and the same into `~/lab04` on the **laptop** (it needs `hector.launch.py` and `hector.rviz`).

| File | What it is | Runs on |
|---|---|---|
| ⬇️ [99-ms200-lidar.rules](code/99-ms200-lidar.rules) | udev rule: `/dev/lidar`, `dialout` group (Part 2) | Pi |
| ⬇️ [ms200_node.py](code/ms200_node.py) | the lidar driver: MS200 packets → `sensor_msgs/LaserScan` (Part 3) | Pi |
| ⬇️ [lidar.launch.py](code/lidar.launch.py) | the driver + the lidar's TF frame, in namespace `/<hostname>` (Part 3) | Pi |
| ⬇️ [hector.launch.py](code/hector.launch.py) | Hector SLAM with this robot's frames and topics, + RViz (Part 7) | laptop or Pi |
| ⬇️ [hector.rviz](code/hector.rviz) | RViz layout: map, scan, SLAM pose, TF | laptop |

---

## Part 1 — The lidar

### 1.1 What it is

| | Oradar MS200 |
|---|---|
| Principle | time of flight (dToF), a laser and a sensor on a spinning head |
| Range | 0.03–12 m (on this lab's robot: returns under 0.10 m are the robot's own frame) |
| Speed | about **10 turns per second**, 4500 measurements per second → ~450 points per turn (0.8°) |
| Interface | UART at **230 400 baud**, sends on its own as soon as it has power; the adapter board makes it `/dev/ttyUSB0` |
| Power | 5 V from the USB cable |

### 1.2 Find it

Plug the adapter into a Pi USB port and:

```bash
lsusb | grep 1a86               # ... ID 1a86:7523 QinHeng Electronics CH340 serial converter
sudo dmesg | grep ch341         # ch341-uart converter now attached to ttyUSB0
ls -l /dev/ttyUSB*
```

> **More than one CH340?** Hiwonder's voice module and many other add-ons use the same
> chip, so the lidar isn't always `ttyUSB0`. Unplug the others to find out which one it is;
> Part 2 then names it by its USB port.

### 1.3 What it sends

The MS200 uses the same 47-byte packet as the LDROBOT LD06:

```
 0x54 0x2C | speed   | start angle | 12 × (distance, intensity) | end angle | timestamp | CRC-8
  header     u16 °/s   u16 0.01°     u16 mm      u8               u16 0.01°   u16 ms      1 byte
```

| Field | Meaning |
|---|---|
| `0x54 0x2C` | start of a packet (`0x2C` = 12 points) |
| speed | how fast the head turns, degrees per second (~3600 = 10 turns/s) |
| start / end angle | angle of the first and last of the 12 points; the ones in between are spread evenly |
| distance | millimetres, `0` = no return |
| CRC-8 | over the first 46 bytes, polynomial `0x4D`, initial value 0 |

Look at the raw bytes (the Pi's user is in `dialout` since Lab 02):

```bash
python3 - <<'EOF'
import serial
s = serial.Serial('/dev/ttyUSB0', 230400, timeout=1)
d = s.read(470)
i = d.find(b'\x54\x2c'); p = d[i:i+47]
print(p.hex(' '))
print('speed', int.from_bytes(p[2:4], 'little'), 'deg/s,',
      'start', int.from_bytes(p[4:6], 'little') / 100, 'deg,',
      'first distance', int.from_bytes(p[6:8], 'little'), 'mm')
EOF
```

Put your hand 20 cm from the lidar and run it again a few times: one of the 12 distances
in some of the packets reads about `200`.

> **Angles grow clockwise** (seen from above), and ROS measures angles
> **counter-clockwise** (REP 103: x forward, y left, z up). The driver turns one into the
> other (Part 3.1).

---

## Part 2 — A fixed name: `/dev/lidar`

`ttyUSB0` today can be `ttyUSB1` after the next boot, when another USB-serial device is
found first. The udev rule gives the lidar the name `/dev/lidar`. It matches the CH340's ID
**and the USB port** it's plugged into, because another CH340 has the same ID.

Find your port:

```bash
udevadm info -q property /dev/ttyUSB0 | grep ID_PATH=
# ID_PATH=platform-xhci-hcd.1-usb-0:1:1.0
```

Put that value in the rule (`ENV{ID_PATH}==…`) if yours is different, then install it:

```bash
cd ~/lab04
nano 99-ms200-lidar.rules
sudo cp 99-ms200-lidar.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger --subsystem-match=tty
ls -l /dev/lidar                 # /dev/lidar -> ttyUSB0
```

The rule follows the **port**, so the lidar must stay in the same USB socket. Moving it
means editing `ID_PATH` again.

---

## Part 3 — The driver: scan → ROS 2

### 3.1 What `ms200_node.py` does

| Step | Why |
|---|---|
| Reads 230 400 baud, looks for `0x54 0x2C`, checks the CRC | a packet with a bad CRC is dropped and the search starts one byte later |
| Collects points until the angle wraps past 0° | one wrap = one turn of the head = one scan |
| Turns clockwise angles into counter-clockwise (`clockwise:=true`) | ROS convention (Part 1.3) |
| Puts each point into one of **450 fixed bins** (0.8° each) | a `LaserScan` has one constant `angle_increment`; scan matchers such as Hector rely on it. A bin without a return is `+inf` |
| Drops distances outside `range_min`…`range_max` (0.10–12 m) | under 0.10 m the lidar sees the robot's own frame |
| Publishes `scan` with sensor-data QoS (best effort) | the usual QoS for sensors: a late scan is useless, so it isn't resent |

| Parameter | Default | |
|---|---|---|
| `port` | `/dev/lidar` | |
| `frame_id` | `laser` | `lidar.launch.py` sets `<hostname>/laser` |
| `clockwise` | `true` | set `false` if the map comes out mirrored |
| `rays` | 450 | bins per turn |
| `range_min`, `range_max` | 0.10, 12.0 m | |

It is plain Python with `pyserial` (installed in Lab 02): no workspace or build needed.

### 3.2 Where the lidar sits: TF

The scan is measured in the frame **`robot01/laser`**. For a map, ROS has to know where
that frame is on the robot. `lidar.launch.py` starts a **static transform** from the
robot's base (on the floor, between the wheels/tracks) to the lidar:

```
robot01/base_footprint ──(x, z, yaw: fixed)──> robot01/laser
```

Measure on your robot: `x` = how far the lidar's centre is ahead of the middle between the
wheels, `z` = how high the lidar's window is above the floor. Defaults: `x:=0.0 z:=0.12`.

Frame names carry the hostname, like topics (Lab 01, Part 9.3): TF is one shared tree for
everyone on the domain, so `base_footprint` alone would mix two robots.

### 3.3 Run it

```bash
cd ~/lab04
ros2 launch ./lidar.launch.py                      # add x:=0.05 z:=0.15 ... for your robot
```

In a second SSH session:

```bash
ros2 topic hz /robot01/scan                         # average rate: 10.0
ros2 topic echo --once /robot01/scan --field angle_increment                        # 0.01396 (0.8 deg)
ros2 run tf2_ros tf2_echo robot01/base_footprint robot01/laser
```

The driver prints `scans N, crc errors M` every 10 s. On this lab's robot: 10 Hz, **0 CRC
errors**, about **9 % of one Pi 5 core**.

### 3.4 Which way is the front?

The lidar's 0° must point where the robot drives. Check it now — a wrong yaw gives a map
that looks fine but a robot that drives sideways in it.

On the **laptop**, start RViz with *Fixed Frame* `robot01/base_footprint`, add a *LaserScan*
display for `/robot01/scan` (*Reliability*: **Best Effort**) and a *TF* display. Put a box
50 cm **in front** of the robot, then 50 cm to its **left**:

| The box shows up | Means | Fix |
|---|---|---|
| on the red x axis, then on the green y axis | correct | — |
| at another angle | the lidar's 0° isn't the front | `yaw:=` that angle in radians (e.g. `yaw:=1.5708` for 90°) |
| in front correctly, but **right** instead of left | the scan is mirrored | `-p clockwise:=false` on the driver (edit `lidar.launch.py`) |

On this lab's robot both checks were correct with the defaults (0° = front, checked against
the depth camera's image as well).

---

## Part 4 — How Hector SLAM works

**SLAM** = simultaneous localization and mapping: build a map of an unknown place and,
at the same time, know where you are in it.

**Hector SLAM** (TU Darmstadt, 2011) does it with the lidar alone:

1. The map is an **occupancy grid**: 5 cm cells, each with a probability of being a wall.
2. For every new scan, it searches for the robot pose (x, y, θ) at which the scan's points
   fall best on the walls already in the map: **scan matching** (a Gauss-Newton
   optimisation on the interpolated grid).
3. It adds the scan to the map at that pose: cells along each ray become *free*, the cell
   at its end *occupied*.
4. It does this on a **coarse and a fine grid** (`map_multi_res_levels`), so the match
   doesn't get stuck when the robot moved more than a few cells since the last scan.

| | Hector SLAM | for comparison: slam_toolbox / Cartographer |
|---|---|---|
| Needs odometry | **no** | yes (strongly recommended) |
| Loop closure (fixing a map when you come back to the start) | **no** | yes |
| Load | very light: ~3 % of one Pi 5 core here | heavier |
| Fails when | the robot turns fast, or in long featureless corridors | — |

No odometry means you can map before the motors even work, or with the robot in your
hands. No loop closure means the map of a big loop can come back with a small step where
the ends meet; for a room or an apartment it isn't a problem.

What it publishes:

| Output | |
|---|---|
| `/map` | `nav_msgs/OccupancyGrid`, **latched** (transient local), every 1 s |
| `/slam_out_pose` | the robot's pose in the map |
| TF `map → robot01/base_footprint` | where the robot is (or `map → robot01/odom` when wheel odometry is there, Part 7.4) |
| `/reset_map` (service), `/syscommand` `"reset"` | clear the map and start again |

---

## Part 5 — Get Hector SLAM

Hector SLAM was written for ROS 1 and has **no official ROS 2 release**. This lab uses
[RobotX-Workshops/hector_slam_ros2](https://github.com/RobotX-Workshops/hector_slam_ros2), a
port of `hector_mapping` for Jazzy (BSD-2 licence, like the original). It also builds on
**Humble without changes**.

Build it where SLAM will run: on the **laptop** to map with RViz (Part 6), on the **Pi**
to keep the robot independent of Wi-Fi (Part 8). Doing both is fine.

```bash
mkdir -p ~/hector_ws/src && cd ~/hector_ws/src
git clone https://github.com/RobotX-Workshops/hector_slam_ros2.git
git -C hector_slam_ros2 checkout 87a9651          # the version this lab was tested with
cd ~/hector_ws
source /opt/ros/$ROS_DISTRO/setup.bash
rosdep install --from-paths src --ignore-src -y   # laser_geometry, tf2_eigen, Eigen, ...
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release
echo 'source ~/hector_ws/install/setup.bash' >> ~/.bashrc
```

| Package | |
|---|---|
| `hector_mapping` | the SLAM node — the one this lab uses |
| `hector_nav_msgs` | its message and service types |
| `hector_slam_launch` | the port's example launch file, frames `base_link`/`laser` (not used here) |

> **Use `Release`.** A debug build of the scan matcher is several times slower; on the Pi it
> can fall behind the 10 Hz scan.

---

## Part 6 — Distributed: lidar on the Pi, SLAM on the laptop

```
 Pi:     ms200_node ──/robot01/scan (10 Hz, ~36 KB/s)──┐       Wi-Fi, DDS
         static TF base_footprint → laser ─────────────┤
                                                       ▼
 laptop: hector_mapping ──/map, TF map → base_footprint──> RViz
```

### 6.1 Why the laptop

| | |
|---|---|
| Bandwidth | one scan is 450 ranges + 450 intensities, ~3.6 KB: about 36 KB/s, nothing for Wi-Fi |
| Latency | measured on this lab's robot: a scan reaches the laptop **~6 ms** after it's published (the scan itself takes 100 ms) |
| Convenience | RViz, and you can change parameters and restart SLAM without touching the robot |
| Compute | **not** the reason: the Pi 5 runs Hector easily (Part 8) |

### 6.2 Same domain, same middleware

Both machines: the same `ROS_DOMAIN_ID` (17) and the same `RMW_IMPLEMENTATION` (Lab 01,
Part 9.2). Check from the laptop while `lidar.launch.py` runs on the Pi:

```bash
ros2 topic hz /robot01/scan          # 10 Hz on the laptop too
```

### 6.3 A Humble laptop with the Jazzy robot

ROS doesn't promise that different distributions talk to each other, but for standard
messages (`LaserScan`, `OccupancyGrid`, TF, `Twist`) Humble and Jazzy do, over **Cyclone
DDS**. Fast DDS differs a lot between the two (2.6 and 2.14), and on this lab's robot some
messages arrived garbled with it. So use Cyclone on both:

```bash
# Pi
sudo apt install -y ros-jazzy-rmw-cyclonedds-cpp
# laptop
sudo apt install -y ros-humble-rmw-cyclonedds-cpp
# both, in ~/.bashrc after ROS_DOMAIN_ID; then a new terminal, and ros2 daemon stop
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

Restart anything already running on the Pi (a launch file, a systemd service): it keeps
the middleware it started with. A `serdata.cpp` warning on the Humble side now and then is
harmless (a type that differs between the distributions, such as `/parameter_events`).

---

## Part 7 — Make a map

### 7.1 Start it

**Pi:**

```bash
ros2 launch ~/lab04/lidar.launch.py
```

**Laptop:**

```bash
ros2 launch ~/lab04/hector.launch.py robot:=robot01
```

RViz opens with the map, the scan (red), the SLAM pose (green arrow) and the TF frames. Within
a second the room around the robot appears: walls black, seen floor white, the rest grey.

The settings in `hector.launch.py` that differ from Hector's defaults:

| Parameter | Value | Why |
|---|---|---|
| `scan_topic`, `base_frame` | `/robot01/scan`, `robot01/base_footprint` | this robot's names |
| `odom_frame` | = `base_frame` (`odom:=none`) | no odometry: Hector publishes `map → base_footprint` itself |
| `map_resolution`, `map_size` | 0.05 m, 1024 | a 51 m × 51 m map, robot starting in the middle (`map_start_x/y` 0.5) |
| `map_multi_res_levels` | 2 | coarse + fine grid (Part 4) |
| `laser_min_dist`, `laser_max_dist` | 0.12 m, 8 m | ignore the robot's own frame, and far returns, which are noisy on the MS200 |
| `map_update_distance_thresh`, `…angle_thresh` | 0.2 m, 0.06 rad | add a scan to the map after this much motion (defaults 0.4 m / 0.9 rad are for faster robots) |
| `map_pub_period` | 1 s | how often `/map` is sent |

### 7.2 Move the robot through the room

- **Slowly**: under ~0.2 m/s, and turn **slower than about 30°/s**. Fast turns are where
  Hector loses track: between two scans the view changes too much to match.
- Keep the lidar level, and keep yourself out of the scan as much as you can (walk behind
  the robot).
- Go along walls and through doors; come back toward the start at the end.

To drive it: the ROS 2 robot software in
[rpi5-robot-board](https://github.com/hmarthens1/rpi5-robot-board) gives the robot a
`/robot01/cmd_vel` topic (and teleop from a PC app); or simply **carry or push** the
robot at walking pace. Hector only needs the lidar.

> **Start over** at any time: `ros2 service call /reset_map std_srvs/srv/Trigger`
> (or `ros2 topic pub --once /syscommand std_msgs/String "data: reset"`).

### 7.3 Signs of trouble in RViz

| What you see | Cause | Fix |
|---|---|---|
| The map doubles: two copies of a wall at an angle | lost track during a turn | reset, turn slower |
| The map is mirrored, or the robot moves "backward" | scan direction or lidar yaw wrong | Part 3.4 |
| Walls get thicker and fuzzy | someone walking next to the robot, or a lidar that wobbles | |
| In a long, bare corridor the robot "stands still" while it moves | every scan looks the same along the corridor | doors, furniture or boxes along the way |

### 7.4 With wheel odometry

Once a robot node publishes encoder odometry as TF `robot01/odom → robot01/base_footprint`,
start Hector with `odom:=robot01/odom`. Hector then publishes `map → robot01/odom`, the
correction on top of the odometry, which is how ROS expects it (REP 105) and what Nav2 needs.

Don't use `odom:=none` while something else publishes `… → robot01/base_footprint`: a frame
can only have **one** parent in TF.

### 7.5 Save the map

`map_saver_cli` from Nav2 writes the map Nav2 loads later: a `.pgm` image and a `.yaml`
with the resolution and origin.

```bash
sudo apt install -y ros-$ROS_DISTRO-nav2-map-server
mkdir -p ~/maps
ros2 run nav2_map_server map_saver_cli -f ~/maps/room1
ls ~/maps                     # room1.pgm  room1.yaml
```

It reads the latched `/map` once, so Hector can keep running. Open `room1.pgm` with any
image viewer: white = free, black = occupied, grey = never seen.

---

## Part 8 — SLAM on the Pi

When the robot drives **by itself**, SLAM belongs on the robot: if Wi-Fi drops while the
laptop does the localization, the robot no longer knows where it is. The laptop then only
watches.

Build Hector on the Pi (Part 5, same commands; ~3 % of a core at run time). Then on the Pi:

```bash
ros2 launch ~/lab04/lidar.launch.py &
ros2 launch ~/lab04/hector.launch.py robot:=$(hostname) rviz:=false
```

On the laptop, RViz alone shows the same picture:

```bash
sed 's#/ROBOT/scan#/robot01/scan#' ~/lab04/hector.rviz > /tmp/hector_robot01.rviz
rviz2 -d /tmp/hector_robot01.rviz
```

and `map_saver_cli` works from either machine.

This is how the lab's robot explores on its own: Hector, **Nav2** and a frontier explorer
all on the Pi, the laptop only watching. In one unattended run indoors it mapped **47 m²
in 12.6 minutes**, chose its 30 goals itself, drove back to its start and saved the map,
with the Pi at about 1.5 of its 4 cores (`mentorpi_nav` in
[rpi5-robot-board](https://github.com/hmarthens1/rpi5-robot-board)).

---

## Troubleshooting

| Problem | Try this |
|---------|---------|
| No `/dev/ttyUSB*` | Data cable? Try another port; `sudo dmesg -w` while plugging in. `brltty` on desktop Ubuntu grabs CH340s: `sudo apt remove brltty` |
| No `/dev/lidar`, but `ttyUSB0` is there | `ID_PATH` in the rule isn't your port (Part 2), or the lidar moved to another socket |
| `ms200_node`: `no data for 0.5 s` | The head isn't spinning (power: try a powered USB hub, or another port), or wrong port: is that CH340 the lidar? |
| `crc errors` going up fast | Wrong baud rate, or a different lidar model; check the raw bytes (Part 1.3) |
| `/robot01/scan` on the Pi but not on the laptop | Domain ID and middleware (Part 6.2); `ros2 daemon stop` on both. In RViz set the scan's *Reliability* to **Best Effort** |
| Hector: `lookupTransform robot01/base_footprint to robot01/laser timed out` | `lidar.launch.py` (the static TF) isn't running, or `robot:=` doesn't match the Pi's hostname |
| Hector: `Transform failed during publishing of map_odom transform` | `odom:=robot01/odom` but nothing publishes odometry: use `odom:=none` |
| RViz: *Frame [map] does not exist* | Hector hasn't received a scan yet: check the two rows above |
| The map is good but the robot arrow points sideways | Lidar yaw (Part 3.4) |
| `map_saver_cli` times out | Hector isn't running, or a different domain/middleware; `ros2 topic info /map -v` |

---

## Completion Checklist

- [ ] You can find the lidar on the USB bus and decode a packet by hand (Part 1)
- [ ] `/dev/lidar` exists after a reboot (Part 2)
- [ ] `ros2 topic hz /robot01/scan` shows 10 Hz, on the Pi **and** on the laptop
- [ ] The box test passes: front on +x, left on +y (Part 3.4)
- [ ] Hector SLAM is built (laptop, Pi, or both)
- [ ] A map of a room in RViz, without a doubled wall
- [ ] `room1.pgm` and `room1.yaml` saved
- [ ] Optional: the same map with Hector running on the Pi (Part 8)
