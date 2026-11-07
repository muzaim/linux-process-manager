#!/usr/bin/env python3
"""linux-process-manager: a simple CLI to manage running processes on Linux."""

import argparse
import os
import signal
import sys
import time

import psutil

FIELDS = ["pid", "name", "username", "status", "cpu_percent", "memory_percent"]


def collect(name_filter=None):
    procs = []
    for p in psutil.process_iter(FIELDS):
        info = p.info
        if name_filter and name_filter.lower() not in (info["name"] or "").lower():
            continue
        procs.append(info)
    return procs


def print_table(procs, limit=None):
    print(f"{'PID':>7}  {'USER':<12} {'STATUS':<10} {'CPU%':>6} {'MEM%':>6}  NAME")
    for info in procs[:limit] if limit else procs:
        print(
            f"{info['pid']:>7}  {(info['username'] or '?')[:12]:<12} "
            f"{info['status']:<10} {info['cpu_percent'] or 0:>6.1f} "
            f"{info['memory_percent'] or 0:>6.1f}  {info['name']}"
        )


def sample_cpu(interval=0.5):
    """Prime cpu_percent counters so the next read returns real values."""
    for p in psutil.process_iter():
        try:
            p.cpu_percent(None)
        except psutil.Error:
            pass
    time.sleep(interval)


def cmd_list(args):
    sample_cpu()
    procs = collect()
    procs.sort(key=lambda i: i[args.sort] or 0, reverse=args.sort != "pid")
    print_table(procs, args.limit)


def cmd_find(args):
    sample_cpu()
    procs = collect(args.name)
    if not procs:
        print(f"No process matching '{args.name}' found.")
        return 1
    print_table(procs)


def cmd_monitor(args):
    try:
        while True:
            sample_cpu(args.interval)
            procs = collect(args.name)
            procs.sort(key=lambda i: i["cpu_percent"] or 0, reverse=True)
            mem = psutil.virtual_memory()
            os.system("clear")
            print(
                f"CPU: {psutil.cpu_percent():5.1f}%   "
                f"Memory: {mem.percent:5.1f}% "
                f"({mem.used // 2**20} MB / {mem.total // 2**20} MB)   "
                f"Processes: {len(procs)}\n"
            )
            print_table(procs, args.limit)
            print("\nPress Ctrl+C to exit.")
    except KeyboardInterrupt:
        pass


def cmd_kill(args):
    sig = signal.SIGKILL if args.force else signal.SIGTERM
    targets = []
    if args.target.isdigit():
        try:
            targets = [psutil.Process(int(args.target))]
        except psutil.NoSuchProcess:
            print(f"No process with PID {args.target}.")
            return 1
    else:
        targets = [p for p in psutil.process_iter(["name"]) if p.info["name"] == args.target]
        if not targets:
            print(f"No process named '{args.target}'.")
            return 1

    code = 0
    for p in targets:
        try:
            p.send_signal(sig)
            print(f"Sent {sig.name} to {p.pid} ({p.name()}).")
        except psutil.AccessDenied:
            print(f"Permission denied for PID {p.pid}. Try running with sudo.")
            code = 1
        except psutil.NoSuchProcess:
            print(f"PID {p.pid} no longer exists.")
    return code


def cmd_status(args):
    try:
        p = psutil.Process(args.pid)
        with p.oneshot():
            p.cpu_percent(None)
            time.sleep(0.5)
            mem = p.memory_info()
            rows = [
                ("PID", p.pid),
                ("Name", p.name()),
                ("Status", p.status()),
                ("User", p.username()),
                ("Parent PID", p.ppid()),
                ("Started", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.create_time()))),
                ("CPU %", f"{p.cpu_percent(None):.1f}"),
                ("Memory %", f"{p.memory_percent():.1f}"),
                ("RSS", f"{mem.rss // 2**20} MB"),
                ("Threads", p.num_threads()),
            ]
            try:
                rows.append(("Command", " ".join(p.cmdline()) or "-"))
            except psutil.AccessDenied:
                rows.append(("Command", "<access denied>"))
    except psutil.NoSuchProcess:
        print(f"No process with PID {args.pid}.")
        return 1
    except psutil.AccessDenied:
        print(f"Permission denied for PID {args.pid}. Try running with sudo.")
        return 1

    for key, value in rows:
        print(f"{key:<12} {value}")


def main():
    parser = argparse.ArgumentParser(prog="lpm", description="Simple Linux process manager CLI.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="list running processes")
    p.add_argument("-s", "--sort", choices=["pid", "cpu_percent", "memory_percent"], default="cpu_percent")
    p.add_argument("-n", "--limit", type=int, default=20, help="max rows (default: 20)")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("find", help="find processes by name")
    p.add_argument("name")
    p.set_defaults(func=cmd_find)

    p = sub.add_parser("monitor", help="live CPU and memory monitor")
    p.add_argument("name", nargs="?", help="optional name filter")
    p.add_argument("-i", "--interval", type=float, default=2.0, help="refresh seconds (default: 2)")
    p.add_argument("-n", "--limit", type=int, default=15, help="max rows (default: 15)")
    p.set_defaults(func=cmd_monitor)

    p = sub.add_parser("kill", help="kill a process by PID or exact name")
    p.add_argument("target")
    p.add_argument("-f", "--force", action="store_true", help="use SIGKILL instead of SIGTERM")
    p.set_defaults(func=cmd_kill)

    p = sub.add_parser("status", help="show detailed status of a process")
    p.add_argument("pid", type=int)
    p.set_defaults(func=cmd_status)

    args = parser.parse_args()
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
