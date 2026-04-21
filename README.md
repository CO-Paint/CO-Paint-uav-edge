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
* **Hardware:** Raspberry Pi 5, Pixhawk (PX4 v1.14+)

### 2. Mandatory Drivers
* **Livox-SDK2:** - Ubuntu 24.04(GCC 13)에서 빌드 시, `sdk_core/comm/define.h` 및 `logger_handler/file_manager.h`에 `#include <cstdint>` 추가가 필요합니다.
* **Intel RealSense SDK (librealsense):** - D435 인식 및 ROS 2 토픽 발행을 위해 필요합니다.
* **Micro-XRCE-DDS-Agent:** https://github.com/eProsima/Micro-XRCE-DDS
  - 픽스호크와의 고속 UART 통신(921600 bps)을 위해 빌드 및 설치되어야 합니다.

### 3. Networking Setup (Crucial)
안정적인 데이터 전송을 위해 다음과 같은 포트 구성을 권장합니다.
* **eth0 (내장 랜포트):** Livox Mid-360 (Static IP: `192.168.1.50`)
* **USB-Ethernet (USB 2.0 포트):** GCS/Router 연결 (DHCP 추천)

---

## 🚀 Getting Started

### USB Reset Fix (Important)
라즈베리파이 부팅 시 USB 랜 젠더가 인식되지 않는 고질적인 하드웨어 버그를 해결하기 위해, `crontab`에 아래 리셋 스크립트 등록이 필요합니다.

```bash
# crontab -e 실행 후 하단에 추가
@reboot sleep 15 && echo "usb2" > /sys/bus/usb/drivers/usb/unbind && sleep 3 && echo "usb2" > /sys/bus/usb/drivers/usb/bind
```

### Build & Workspace Setup

# CO-Paint 통합 워크스페이스 빌드
cd ~/copaint_ws && colcon build --symlink-install
```

### Execution
센서 데이터 발행 및 픽스호크 통신 에이전트를 한 번에 실행합니다.
```bash
source ~/ws_livox/install/setup.bash
source ~/copaint_ws/install/setup.bash

ros2 launch copaint_bringup uav_master.launch.py
```
