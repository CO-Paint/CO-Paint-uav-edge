from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # 1. Livox Mid-360 런치
    livox_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('livox_ros_driver2'), '/launch_ROS2/msg_MID360s_launch.py' #/home/ubuntu1347/ws_livox/src/livox_ros_driver2/launch_ROS2/msg_MID360s_launch.py
        ])
    )

    # 2. RealSense D435 런치 (Depth/IR 끄기, 640x480@15fps)
    realsense_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('realsense2_camera'), '/launch/rs_launch.py'
        ]),
        launch_arguments={
            'rgb_camera.profile': '640x480x15',
            'enable_depth': 'false',
            'enable_infra1': 'false',
            'enable_infra2': 'false',
            'enable_gyro': 'false',
            'enable_accel': 'false',
        }.items()
    )

    # 3. Micro XRCE-DDS Agent (픽스호크 통신 브릿지)
    xrce_agent = ExecuteProcess(
        cmd=['MicroXRCEAgent', 'serial', '--dev', '/dev/ttyAMA0', '-b', '921600'],
        output='screen'
    )

    return LaunchDescription([
        livox_launch,
        realsense_launch,
        xrce_agent
    ])