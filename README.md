# 🎨 CO-Paint UAV Onboard System

이 저장소는 **CO-Paint(Tethered UAV-UGV Automated Painting System)** 프로젝트의 드론 측 메인 컨트롤러(Raspberry Pi 5) 소프트웨어 스택을 담고 있습니다. Livox Mid-360 LiDAR, Intel RealSense D435 센서 데이터를 처리하고 Micro XRCE-DDS를 통해 Pixhawk(PX4)와 실시간으로 통신합니다.

## 📂 Repository Structure

* `copaint_ws/`: 프로젝트 전용 메인 워크스페이스 (통합 런치 및 제어 노드)
* `ws_livox/`: Livox ROS Driver 2 워크스페이스
* `Livox-SDK2/`: Livox LiDAR 통신을 위한 기본 드라이버 및 SDK
* `Micro-XRCE-DDS-Agent/`: Pixhawk(PX4)와 ROS 2 간의 통신 브릿지

## 🛠 Prerequisites & Dependencies

### 1. System Environment
* **OS:** Ubuntu 24.04 LTS (Noble Numbat)
* **ROS 2:** Jazzy 
* **Hardware:** Raspberry Pi 5, Pixhawk (PX4 v1.16+)

### 2. Mandatory Drivers
* **Livox-SDK2:**
  - https://github.com/Livox-SDK/Livox-SDK2
  - Ubuntu 24.04(GCC 13)에서 빌드 시, `sdk_core/comm/define.h` 및 `logger_handler/file_manager.h`에 `#include <cstdint>` 추가가 필요합니다.
* **Livox ROS2 Driver:**
  - https://github.com/Livox-SDK/livox_ros_driver2
  - ros2 토픽형태로 livox의 데이터를 발송하기위해 필수적입니다.
* **Intel RealSense SDK (librealsense):**
  - ```bash
    sudo apt install ros-$ROS_DISTRO-librealsense2*
    sudo apt install ros-$ROS_DISTRO-realsense2-*
    ```
  - D435 인식 및 ROS 2 토픽 발행을 위해 필요합니다.
* **Micro-XRCE-DDS-Agent:**
  - https://github.com/eProsima/Micro-XRCE-DDS
  - 픽스호크와의 고속 UART 통신(921600 bps)을 위해 빌드 및 설치되어야 합니다.

## 🚀 Getting Started

### Build & Workspace Setup

# CO-Paint 통합 워크스페이스 빌드
```bash
cd ~/copaint_ws && colcon build --symlink-install
```

### Execution
센서 데이터 발행 및 픽스호크 통신 에이전트를 한 번에 실행합니다.
```bash
source ~/ws_livox/install/setup.bash
source ~/copaint_ws/install/setup.bash

ros2 launch copaint_bringup uav_master.launch.py
```
