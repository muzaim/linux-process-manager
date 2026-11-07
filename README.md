# linux-process-manager

A lightweight command-line tool for managing running processes on Linux, written in Python.

## Features

- List running processes, sorted by CPU, memory, or PID
- Find processes by name
- Live CPU and memory monitoring
- Kill processes by PID or name
- Show detailed status of a single process

## Requirements

- Python 3.8+
- [psutil](https://pypi.org/project/psutil/)

## Installation

```bash
git clone https://github.com/muzaim/linux-process-manager.git
cd linux-process-manager
pip install -r requirements.txt
chmod +x lpm.py
```

Optionally, make it available system-wide:

```bash
sudo ln -s "$(pwd)/lpm.py" /usr/local/bin/lpm
```

## Usage

```
lpm <command> [options]
```

| Command   | Description                              |
|-----------|------------------------------------------|
| `list`    | List running processes                   |
| `find`    | Find processes by name                   |
| `monitor` | Live CPU and memory monitor              |
| `kill`    | Kill a process by PID or exact name      |
| `status`  | Show detailed status of a process        |

Run `lpm <command> -h` for command-specific options.

### Examples

List the top 10 processes by memory usage:

```bash
lpm list --sort memory_percent --limit 10
```

Find all processes containing "python":

```bash
lpm find python
```

Monitor the system, refreshing every second:

```bash
lpm monitor -i 1
```

Monitor only processes matching "nginx":

```bash
lpm monitor nginx
```

Gracefully stop a process (SIGTERM), or force kill it (SIGKILL):

```bash
lpm kill 1234
lpm kill firefox --force
```

Show detailed status of a process:

```bash
lpm status 1234
```

Example output:

```
PID          1234
Name         python3
Status       running
User         alice
Parent PID   1
Started      2026-11-08 06:40:12
CPU %        2.5
Memory %     1.3
RSS          48 MB
Threads      4
Command      python3 app.py
```

## Notes

- Killing or inspecting processes owned by other users may require `sudo`.
- `kill` by name matches the exact process name; use `find` first to check what will be affected.

## License

MIT
