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


class MocapTopicHandler:
    def __init__(self, node: Node, agent_id: str, dim: int = 3):
        self.agent_id = agent_id
        self.dim = dim
        self.keys = KEYS_3D if dim == 3 else KEYS_2D
        self._lock = threading.Lock()
        self._buffer: list[dict] = []

        node.create_subscription(PoseStamped, f'/{agent_id}/world', self._callback, 10)

    def _callback(self, msg: PoseStamped) -> None:
        q = msg.pose.orientation
        rx, ry, rz = np.rad2deg(Rot.from_quat([q.x, q.y, q.z, q.w]).as_euler('xyz'))

        reading = {'x': msg.pose.position.x, 'y': msg.pose.position.y, 'yaw': rz}
        if self.dim == 3:
            reading['z'] = msg.pose.position.z
            reading['roll'] = rx
            reading['pitch'] = ry

        with self._lock:
            self._buffer.append(reading)

    def snapshot(self) -> dict:
        """Drain the buffer and return averaged values. Returns NaN if no data arrived."""
        with self._lock:
            buf, self._buffer = self._buffer, []

        if not buf:
            return {k: np.nan for k in self.keys}
        return {k: np.mean([r[k] for r in buf]) for k in self.keys}


def build_dataframe(handlers: list[MocapTopicHandler]) -> pd.DataFrame:
    rows = {h.agent_id: h.snapshot() for h in handlers}
    keys = handlers[0].keys
    return pd.DataFrame.from_dict(rows, orient='index', columns=keys)


class MocapTableTui(Node):
    def __init__(self, agent_ids: list[str], dim: int, hz: float, decimals: int):
        super().__init__('mocap_table_tui')
        self.handlers = [MocapTopicHandler(self, aid, dim) for aid in agent_ids]
        self.decimals = decimals
        self.create_timer(1.0 / hz, self._display_tick)

    def _display_tick(self) -> None:
        df = build_dataframe(self.handlers)
        output = tabulate(df, headers='keys', tablefmt='psql', floatfmt=f'.{self.decimals}f')
        print(CLEAR_SCREEN + output, end='', flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description='Display live mocap poses in a terminal table.')
    parser.add_argument('ids', type=str, nargs='+', help='Agent IDs to monitor (topic: /ID/world)')
    parser.add_argument('--dim', type=int, choices=[2, 3], default=3, help='Pose dimensions (default: 3)')
    parser.add_argument('--hz', type=float, default=1.0, help='Display refresh rate in Hz (default: 1.0)')
    parser.add_argument('--decimals', type=int, default=3, help='Decimal places to display (default: 3)')
    args = parser.parse_args()

    rclpy.init()
    node = MocapTableTui(args.ids, args.dim, args.hz, args.decimals)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
