#!/usr/bin/env python3

import argparse
import threading

import numpy as np
import pandas as pd
import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from scipy.spatial.transform import Rotation as Rot
from tabulate import tabulate

KEYS_3D = ['x', 'y', 'z', 'roll', 'pitch', 'yaw']
KEYS_2D = ['x', 'y', 'yaw']
CLEAR_SCREEN = '\033[2J\033[H'


class PoseStampedTopicHandler:
    def __init__(self, node: Node, topic: str, dim: int = 3, rotation: str = 'zyx'):
        self.topic = topic
        self.dim = dim
        self.rotation = rotation
        self.keys = KEYS_3D if dim == 3 else KEYS_2D
        self._lock = threading.Lock()
        self._buffer: list[dict] = []

        node.create_subscription(PoseStamped, topic, self._callback, 10)

    def _callback(self, msg: PoseStamped) -> None:
        q = msg.pose.orientation
        reading = {
            'x': msg.pose.position.x,
            'y': msg.pose.position.y,
            'quat': [q.x, q.y, q.z, q.w],
        }
        if self.dim == 3:
            reading['z'] = msg.pose.position.z

        with self._lock:
            self._buffer.append(reading)

    def snapshot(self) -> dict:
        """Drain the buffer and return averaged values. Returns NaN if no data arrived."""
        with self._lock:
            buf, self._buffer = self._buffer, []

        if not buf:
            return {k: np.nan for k in self.keys}

        rx, ry, rz = np.rad2deg(
            Rot.from_quat([r['quat'] for r in buf]).mean().as_euler(self.rotation)
        )
        result = {
            'x': np.mean([r['x'] for r in buf]),
            'y': np.mean([r['y'] for r in buf]),
            'yaw': rz,
        }
        if self.dim == 3:
            result['z'] = np.mean([r['z'] for r in buf])
            result['roll'] = rx
            result['pitch'] = ry

        return result


def build_dataframe(handlers: list[PoseStampedTopicHandler]) -> pd.DataFrame:
    rows = {h.topic: h.snapshot() for h in handlers}
    keys = handlers[0].keys
    return pd.DataFrame.from_dict(rows, orient='index', columns=keys)


class PoseTableTui(Node):
    def __init__(self, topics: list[str], dim: int, hz: float, decimals: int, rotation: str):
        super().__init__('pose_table_tui')
        self.handlers = [PoseStampedTopicHandler(self, t, dim, rotation) for t in topics]
        self.decimals = decimals
        self.create_timer(1.0 / hz, self._display_tick)

    def _display_tick(self) -> None:
        df = build_dataframe(self.handlers)
        output = tabulate(df, headers='keys', tablefmt='psql', floatfmt=f'.{self.decimals}f')
        print(CLEAR_SCREEN + output, end='', flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description='Display live PoseStamped topics in a terminal table.')
    parser.add_argument('topics', type=str, nargs='+', help='Topics to monitor (full topic paths)')
    parser.add_argument('--dim', type=int, choices=[2, 3], default=3, help='Pose dimensions (default: 3)')
    parser.add_argument('--hz', type=float, default=1.0, help='Display refresh rate in Hz (default: 1.0)')
    parser.add_argument('--decimals', type=int, default=3, help='Decimal places to display (default: 3)')
    parser.add_argument('--rotation', choices=['zyx', 'xyz'], default='zyx',
                        help='Euler rotation convention for decomposing quaternions (default: zyx)')
    args = parser.parse_args()

    rclpy.init()
    node = PoseTableTui(args.topics, args.dim, args.hz, args.decimals, args.rotation)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
