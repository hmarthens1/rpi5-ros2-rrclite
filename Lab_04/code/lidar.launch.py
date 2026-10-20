"""Lab 04 - the MS200 lidar on the Pi: scan + the lidar's place on the robot.

   ros2 launch ~/lab04/lidar.launch.py      [port:=/dev/lidar] [x:=0.0] [z:=0.12] [yaw:=0.0] [robot:=<hostname>]

  ms200_node.py                       /<hostname>/scan   (sensor_msgs/LaserScan, 10 Hz)
  static_transform_publisher          <hostname>/base_footprint -> <hostname>/laser

Everything is in namespace /<hostname> and the frames carry the hostname, so two robots on
the same ROS_DOMAIN_ID don't mix (Lab 01, Part 9.3). Measure x/z/yaw on your robot.
"""
import os
import socket

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

HERE = os.path.dirname(os.path.abspath(__file__))


def nodes(context):
    ns = LaunchConfiguration("robot").perform(context)
    return [
        ExecuteProcess(
            cmd=["python3", os.path.join(HERE, "ms200_node.py"), "--ros-args",
                 "-r", "__ns:=/" + ns,
                 "-p", ["port:=", LaunchConfiguration("port")],
                 "-p", "frame_id:=%s/laser" % ns],
            output="screen"),
        Node(package="tf2_ros", executable="static_transform_publisher", namespace=ns,
             arguments=["--x", LaunchConfiguration("x"), "--z", LaunchConfiguration("z"),
                        "--yaw", LaunchConfiguration("yaw"),
                        "--frame-id", ns + "/base_footprint", "--child-frame-id", ns + "/laser"]),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("robot", default_value=socket.gethostname()),
        DeclareLaunchArgument("port", default_value="/dev/lidar"),
        DeclareLaunchArgument("x", default_value="0.0"),       # lidar centre ahead of the base, m
        DeclareLaunchArgument("z", default_value="0.12"),      # lidar height above the floor, m
        DeclareLaunchArgument("yaw", default_value="0.0"),     # rad, if 0 deg of the lidar isn't the front
        OpaqueFunction(function=nodes),
    ])
