"""Lab 04 - Hector SLAM for one robot's lidar, on the laptop or on the Pi.

   ros2 launch ~/lab04/hector.launch.py robot:=robot01             [rviz:=true] [odom:=none]
   ros2 service call /reset_map std_srvs/srv/Trigger                # start a new map

hector_mapping matches each scan against the map built so far; it needs no odometry.

  in   /<robot>/scan                    from lidar.launch.py on the Pi
  in   TF <robot>/base_footprint -> <robot>/laser
  out  /map (latched), /slam_out_pose, TF map -> <robot>/base_footprint
       (or map -> <robot>/odom with odom:=<robot>/odom, when a node publishes encoder odometry)

rviz:=true opens RViz with hector.rviz (from the same folder), pointed at this robot's scan.
"""
import os
import tempfile

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

HERE = os.path.dirname(os.path.abspath(__file__))


def nodes(context):
    robot = LaunchConfiguration("robot").perform(context)
    odom = LaunchConfiguration("odom").perform(context)
    base = "%s/base_footprint" % robot
    # no odometry: hector publishes map -> base_footprint itself
    odom = base if odom in ("", "none") else odom
    with open(os.path.join(HERE, "hector.rviz")) as f:
        rviz = f.read().replace("/ROBOT/scan", "/%s/scan" % robot)
    rviz_cfg = os.path.join(tempfile.gettempdir(), "lab04_hector_%s.rviz" % robot)
    with open(rviz_cfg, "w") as f:
        f.write(rviz)
    return [
        Node(package="hector_mapping", executable="hector_mapping", name="hector_mapping", output="screen",
             parameters=[{
                 "scan_topic": "/%s/scan" % robot,
                 "base_frame": base,
                 "odom_frame": odom,
                 "map_frame": "map",
                 "pub_map_odom_transform": True,
                 "map_resolution": 0.05,
                 "map_size": 1024,                  # 51 m square
                 "map_start_x": 0.5,
                 "map_start_y": 0.5,
                 "map_multi_res_levels": 2,
                 "update_factor_free": 0.4,
                 "update_factor_occupied": 0.9,
                 "map_update_distance_thresh": 0.2,
                 "map_update_angle_thresh": 0.06,
                 "laser_min_dist": 0.12,            # the robot's own frame is inside 0.10 m
                 "laser_max_dist": 8.0,             # MS200 is rated 12 m; far returns are noisy
                 "laser_z_min_value": -1.0,
                 "laser_z_max_value": 1.0,
                 "use_tf_scan_transformation": True,
                 "use_tf_pose_start_estimate": False,
                 "map_pub_period": 1.0,
                 "advertise_map_service": True,
                 "scan_subscriber_queue_size": 5,
             }]),
        Node(package="rviz2", executable="rviz2", arguments=["-d", rviz_cfg], output="log",
             condition=IfCondition(LaunchConfiguration("rviz"))),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("robot", default_value="robot01"),
        DeclareLaunchArgument("odom", default_value="none"),
        DeclareLaunchArgument("rviz", default_value="true"),
        OpaqueFunction(function=nodes),
    ])
