# mocap-table-tui

A terminal table that displays live mocap poses from ROS 2. For each agent ID
provided on the command line, it subscribes to `/<ID>/world`
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
uv run mocap-table-tui.py ID [ID ...] [--dim {2,3}] [--hz HZ]
```

| Argument | Default | Description |
|---|---|---|
| `ID [ID ...]` | *(required)* | One or more agent IDs to monitor |
| `--dim {2,3}` | `3` | Pose dimensions — `3` shows x/y/z/roll/pitch/yaw, `2` shows x/y/yaw |
| `--hz HZ` | `1.0` | Display refresh rate (Hz); poses are averaged over each interval |

## Example

```bash
# Monitor three agents at 2 Hz, 3D poses
uv run mocap-table-tui.py alpha bravo charlie --hz 2

# Monitor two agents with 2D poses only
uv run mocap-table-tui.py alpha bravo --dim 2
```

Example output:

```
+--------+--------+--------+--------+--------+---------+---------+
|        |      x |      y |      z |   roll |   pitch |     yaw |
|--------+--------+--------+--------+--------+---------+---------|
| alpha  |  1.234 |  0.567 |  0.012 |  0.100 |  -0.200 |  45.300 |
| bravo  |  3.456 |  2.345 |  0.023 |  0.050 |   0.100 | -12.500 |
| charlie|    nan |    nan |    nan |    nan |     nan |     nan |
+--------+--------+--------+--------+--------+---------+---------+
```

`nan` means no messages arrived during the last display interval.

## Topic convention

Each agent ID maps to the topic `/<ID>/world`, expected to publish
`geometry_msgs/PoseStamped` messages in the world frame.
