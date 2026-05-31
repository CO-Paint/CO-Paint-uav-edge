#!/usr/bin/env python3
"""
Valve Control Node - CO-Paint
==============================
다이나믹셀 EX-106(Wheel 모드)으로 분사 스프레이 밸브를 제어한다.

전원 ON 시점 위치 = home_raw (닫힘 기준)
- OPEN: CW 회전 (raw 감소) → home_raw - RAW_100DEG 도달 시 정지
- CLOSE: CCW 회전 (raw 증가) → home_raw 도달 시 정지

설계 원칙:
- 명령만 충실히 수행. FSM/안전 로직은 마스터 노드 책임.
- 논블로킹: 이동 루프는 백그라운드 스레드, ROS 콜백은 즉시 반환.
- 시리얼 포트는 lock으로 직렬화.
"""

import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy,
)

from std_msgs.msg import String

from dynamixel_sdk import PortHandler, PacketHandler


# ── 다이나믹셀 설정 ──────────────────────────────────
ADDR_TORQUE_ENABLE    = 24
ADDR_MOVING_SPEED     = 32
ADDR_PRESENT_POSITION = 36

TORQUE_ENABLE = 1
MAX_RAW       = 4095
MAX_ANGLE     = 251.0

RAW_100DEG = round(100 / MAX_ANGLE * MAX_RAW)  # 1633
SPEED_CW   = 1024 + 180   # CW 열기 (raw 감소)
SPEED_CCW  = 180          # CCW 닫기 (raw 증가)
SPEED_STOP = 0

# ── 상태 문자열 ──────────────────────────────────────
STATUS_CLOSED  = 'CLOSED'
STATUS_OPEN    = 'OPEN'
STATUS_MOVING  = 'MOVING'
STATUS_ERROR   = 'ERROR'


class ValveControlNode(Node):
    def __init__(self):
        super().__init__('valve_control_node')

        # ---- 파라미터 ----
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 9600)
        self.declare_parameter('dxl_id', 2)
        self.declare_parameter('command_topic', '/valve/command')
        self.declare_parameter('status_topic', '/valve/status')

        self.port_name = self.get_parameter('port').value
        self.baudrate = int(self.get_parameter('baudrate').value)
        self.dxl_id = int(self.get_parameter('dxl_id').value)

        # ---- QoS: 명령은 RELIABLE + TRANSIENT_LOCAL (유실 방지) ----
        cmd_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # ---- 다이나믹셀 초기화 ----
        self.port = PortHandler(self.port_name)
        self.packet = PacketHandler(1.0)
        self.lock = threading.Lock()    # 시리얼 포트 직렬화
        self.connected = False
        self.home_raw = None
        self.is_open = False
        self._moving = False

        # ---- ROS 인터페이스 ----
        self.status_pub = self.create_publisher(
            String, self.get_parameter('status_topic').value, cmd_qos)
        self.create_subscription(
            String, self.get_parameter('command_topic').value,
            self.command_cb, cmd_qos)

        # ---- 연결 시도 ----
        if self._connect_dynamixel():
            self.get_logger().info(
                f'Valve Control Node started. home_raw={self.home_raw}, '
                f'open_target={self.home_raw - RAW_100DEG}')
            self._publish_status(STATUS_CLOSED)
        else:
            self._publish_status(STATUS_ERROR)

    # ================= 다이나믹셀 연결 =================
    def _connect_dynamixel(self) -> bool:
        if not self.port.openPort():
            self.get_logger().error(f'Failed to open port: {self.port_name}')
            return False
        if not self.port.setBaudRate(self.baudrate):
            self.get_logger().error(f'Failed to set baudrate: {self.baudrate}')
            self.port.closePort()
            return False

        result, _ = self.packet.write1ByteTxRx(
            self.port, self.dxl_id, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
        if result != 0:
            self.get_logger().error('Failed to enable torque')
            self.port.closePort()
            return False

        home, res, _ = self.packet.read2ByteTxRx(
            self.port, self.dxl_id, ADDR_PRESENT_POSITION)
        if res != 0:
            self.get_logger().error('Failed to read home position')
            self.port.closePort()
            return False

        self.home_raw = home
        self.connected = True
        return True

    # ================= ROS 콜백 =================
    def command_cb(self, msg: String):
        cmd = msg.data.strip().upper()
        self.get_logger().info(f'Received valve command: {cmd}')

        if not self.connected:
            self.get_logger().warn('Command ignored: dynamixel not connected')
            return
        if self._moving:
            self.get_logger().warn(f'Command ignored: valve is moving')
            return

        if cmd == 'OPEN':
            if self.is_open:
                self.get_logger().info('Already OPEN, skip')
                return
            target = self.home_raw - RAW_100DEG
            threading.Thread(
                target=self._move_until,
                args=(SPEED_CW, target, True),
                daemon=True,
            ).start()
        elif cmd == 'CLOSE':
            if not self.is_open:
                self.get_logger().info('Already CLOSED, skip')
                return
            threading.Thread(
                target=self._move_until,
                args=(SPEED_CCW, self.home_raw, False),
                daemon=True,
            ).start()
        else:
            self.get_logger().warn(f'Unknown command ignored: {cmd}')

    # ================= 이동 로직 (백그라운드 스레드) =================
    def _move_until(self, speed: int, target_raw: int, opening: bool):
        self._moving = True
        self._publish_status(STATUS_MOVING)
        decreasing = (speed >= 1024)

        with self.lock:
            self.packet.write2ByteTxRx(
                self.port, self.dxl_id, ADDR_MOVING_SPEED, speed)

        while self.connected:
            with self.lock:
                raw, result, _ = self.packet.read2ByteTxRx(
                    self.port, self.dxl_id, ADDR_PRESENT_POSITION)
            if result != 0:
                self.get_logger().error('Position read failed during move')
                break
            if decreasing and raw <= target_raw:
                break
            if not decreasing and raw >= target_raw:
                break
            time.sleep(0.03)

        with self.lock:
            self.packet.write2ByteTxRx(
                self.port, self.dxl_id, ADDR_MOVING_SPEED, SPEED_STOP)

        self._moving = False
        self.is_open = opening
        new_status = STATUS_OPEN if opening else STATUS_CLOSED
        self._publish_status(new_status)
        self.get_logger().info(f'Valve -> {new_status}')

    def _publish_status(self, status: str):
        self.status_pub.publish(String(data=status))

    # ================= 종료 =================
    def shutdown(self):
        self.connected = False
        if self.port.is_open:
            with self.lock:
                self.packet.write2ByteTxRx(
                    self.port, self.dxl_id, ADDR_MOVING_SPEED, SPEED_STOP)
            self.port.closePort()


def main(args=None):
    rclpy.init(args=args)
    node = ValveControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()