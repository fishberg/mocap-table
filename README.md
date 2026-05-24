# pose-table-tui

A terminal table that displays live `PoseStamped` poses from ROS 2. For each topic
provided on the command line, it subscribes to that topic
(`geometry_msgs/PoseStamped`), accumulates incoming messages between display
ticks, and shows the averaged pose in a refreshing table.

Modernized and adapted from [the original ROS 1 version](https://github.com/fishberg/uwb-workspace/tree/master/sikorsky/display).

## Prerequisites

- **ROS 2** (Humble or later) sourced in your shell
- **uv** — [install instructions](https://docs.astral.sh/uv/getting-started/installation/)

## Setup

```bash
uv venv --system-site-packages
uv sync
```

`uv venv --system-site-packages` creates `.venv/` with access to the system
ROS 2 packages (`rclpy`, `geometry_msgs`, etc.). `uv sync` then installs the
remaining pip-managed dependencies (`numpy`, `pandas`, `scipy`, `tabulate`)
into that venv.

## Usage

```
uv run pose-table-tui.py TOPIC [TOPIC ...] [--dim {2,3}] [--hz HZ] [--rotation {zyx,xyz}]
```

| Argument | Default | Description |
|---|---|---|
| `TOPIC [TOPIC ...]` | *(required)* | One or more full topic paths to monitor |
| `--dim {2,3}` | `3` | Pose dimensions — `3` shows x/y/z/roll/pitch/yaw, `2` shows x/y/yaw |
| `--hz HZ` | `1.0` | Display refresh rate (Hz); poses are averaged over each interval |
| `--decimals N` | `3` | Number of decimal places shown in the table |
| `--rotation {zyx,xyz}` | `zyx` | Euler rotation convention for decomposing quaternions |

## Example

```bash
# Monitor three topics at 2 Hz, 3D poses
uv run pose-table-tui.py /alpha/world /bravo/world /charlie/world --hz 2

# Monitor two topics with 2D poses only
uv run pose-table-tui.py /alpha/world /bravo/world --dim 2

# Use xyz Euler convention
uv run pose-table-tui.py /dlio/odom-node/pose --rotation xyz
```

Example output:

```
+----------------------+--------+--------+--------+--------+---------+---------+
|                      |      x |      y |      z |   roll |   pitch |     yaw |
|----------------------+--------+--------+--------+--------+---------+---------|
| /alpha/world         |  1.234 |  0.567 |  0.012 |  0.100 |  -0.200 |  45.300 |
| /bravo/world         |  3.456 |  2.345 |  0.023 |  0.050 |   0.100 | -12.500 |
| /charlie/world       |    nan |    nan |    nan |    nan |     nan |     nan |
| /dlio/odom_node/pose |  1.234 |  0.567 |  0.012 |  0.100 |  -0.200 |  45.300 |
+----------------------+--------+--------+--------+--------+---------+---------+
```

`nan` means no messages arrived during the last display interval.
