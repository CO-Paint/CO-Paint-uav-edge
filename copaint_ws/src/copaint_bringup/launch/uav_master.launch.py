from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node   # ← 추가

def generate_launch_description():
    # 1. Livox Mid-360 런치
    livox_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('livox_ros_driver2'), '/launch_ROS2/msg_MID360s_launch.py'
        ])
    )

    # 2. RealSense D435 런치
    realsense_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('realsense2_camera'), '/launch/rs_launch.py'
        ]),
        launch_arguments={
            'rgb_camera.color_profile': '640x480x15',
            'enable_depth': 'false',
            'enable_infra1': 'false',
            'enable_infra2': 'false',
            'enable_gyro': 'false',
            'enable_accel': 'false',
        }.items()
    )

    # 3. Micro XRCE-DDS Agent
    xrce_agent = ExecuteProcess(
        cmd=['MicroXRCEAgent', 'serial', '--dev', '/dev/ttyAMA0', '-b', '921600'],
        output='screen'
    )

    # 4. Valve Control Node   ← 추가
    valve_control = Node(
        package='valve_control_pkg',
        executable='valve_node',
        name='valve_control_node',
        output='screen',
        parameters=[{
            'port': '/dev/ttyUSB0',
            'baudrate': 9600,
            'dxl_id': 2,
        }]
    )

    flight_control = Node(
        package='flight_control',
        executable='flight_control_node',
        name='flight_control_node',
        output='screen',
        parameters=[{
            'takeoff_altitude': 1.5,
            'cruise_speed': 0.3,
            'accept_radius': 0.15,
            'land_descent_rate': 0.2,
        }]
    )

    return LaunchDescription([
        livox_launch,
        realsense_launch,
        xrce_agent,
        valve_control,
        flight_control,
    ])
