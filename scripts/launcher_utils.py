"""
Veyra Sentinel Launcher Utilities
Pure Python helper for cross-platform port checks, HTTP readiness polling, and clean server management.
Eliminates all inline PowerShell and avoids false-positive antivirus triggers.
"""

import sys
import time
import socket
import subprocess
import os
import signal
import urllib.request
import urllib.error


def is_port_available(port: int) -> bool:
    """Returns True if the port is free to bind."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('127.0.0.1', port))
            return True
    except OSError:
        return False


def wait_for_http(url: str, timeout: float = 30.0) -> bool:
    """Polls an HTTP URL until it responds with HTTP 200/304 or times out."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Veyra-HealthCheck/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status in (200, 304):
                    return True
        except (urllib.error.HTTPError, urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            pass
        time.sleep(0.5)
    return False


def free_ports(ports: list[int]):
    """Frees listening ports on Windows by identifying the owning PID via netstat."""
    if sys.platform != "win32":
        return

    try:
        output = subprocess.check_output(["netstat", "-ano", "-p", "tcp"], text=True, errors="ignore")
    except Exception:
        return

    pids_to_kill = set()
    current_pid = os.getpid()

    for line in output.splitlines():
        parts = line.strip().split()
        if len(parts) >= 5 and parts[3] == "LISTENING":
            local_addr = parts[1]
            pid_str = parts[4]
            try:
                pid = int(pid_str)
                if pid <= 4 or pid == current_pid:
                    continue  # Protect System, Idle, and self
                for port in ports:
                    if local_addr.endswith(f":{port}"):
                        pids_to_kill.add(pid)
            except ValueError:
                continue

    for pid in pids_to_kill:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            try:
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass


def main():
    if len(sys.argv) < 2:
        print("Usage: launcher_utils.py [--free-ports port1 port2 ...] [--wait-url url [timeout]] [--check-port port]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "--free-ports":
        ports = [int(p) for p in sys.argv[2:] if p.isdigit()]
        free_ports(ports)
        sys.exit(0)

    elif cmd == "--wait-url":
        if len(sys.argv) < 3:
            sys.exit(1)
        url = sys.argv[2]
        timeout = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0
        success = wait_for_http(url, timeout)
        sys.exit(0 if success else 1)

    elif cmd == "--check-port":
        if len(sys.argv) < 3:
            sys.exit(1)
        port = int(sys.argv[2])
        sys.exit(0 if is_port_available(port) else 1)

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
