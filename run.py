#!/usr/bin/env python3
"""
Veyra Sentinel — Universal Cross-Platform Launcher
Runs backend (FastAPI/Uvicorn) and frontend (Vite/React) concurrently on Windows, Linux, and macOS.
"""

import sys
import os
import shutil
import subprocess
import time
import webbrowser
from pathlib import Path

# Add scripts directory to path for launcher_utils
ROOT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from launcher_utils import is_port_available, wait_for_http, free_ports
except ImportError:
    def is_port_available(p): return True
    def wait_for_http(u, t=30): return True
    def free_ports(p): pass


def main():
    print("=" * 65)
    print("  HEXARK - Veyra Sentinel Universal Launcher")
    print("=" * 65)

    # Pre-flight: Check Python version
    if sys.version_info < (3, 10):
        print("[!] Warning: Python 3.10+ is recommended.")

    # Pre-flight: Check Node / npm
    npm_cmd = shutil.which("npm")
    if not npm_cmd:
        print("[ERROR] npm is not found in your system PATH!")
        print("        Please install Node.js v18+ from https://nodejs.org/")
        sys.exit(1)

    # Check backend dependencies
    try:
        import uvicorn
        import fastapi
    except ImportError:
        print("[*] Installing backend dependencies via pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(ROOT_DIR / "requirements.txt")], check=False)

    # Check frontend dependencies
    node_modules = ROOT_DIR / "frontend" / "node_modules"
    if not node_modules.exists():
        print("[*] Installing frontend packages via npm install...")
        subprocess.run([npm_cmd, "install"], cwd=str(ROOT_DIR / "frontend"), shell=(sys.platform == "win32"), check=False)

    # Free lingering ports from previous runs
    free_ports([8000, 8001, 5173])

    # Determine backend port
    backend_port = 8000 if is_port_available(8000) else 8001
    env_local = ROOT_DIR / "frontend" / ".env.local"
    env_local.write_text(f"VITE_API_BASE_URL=http://127.0.0.1:{backend_port}\n", encoding="utf-8")

    print(f"\n[*] Starting Veyra Backend on port {backend_port}...")
    backend_cmd = [
        sys.executable, "-m", "uvicorn", "backend.app.main:app",
        "--host", "127.0.0.1",
        "--port", str(backend_port),
        "--reload"
    ]
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(ROOT_DIR))

    print(f"[*] Waiting for backend at http://127.0.0.1:{backend_port}/v1/health ...")
    if wait_for_http(f"http://127.0.0.1:{backend_port}/v1/health", timeout=30):
        print("    [OK] Backend is online!")
    else:
        print("    [*] Backend is warming up...")

    print("\n[*] Starting Veyra Frontend on port 5173...")
    frontend_proc = subprocess.Popen([npm_cmd, "run", "dev"], cwd=str(ROOT_DIR / "frontend"), shell=(sys.platform == "win32"))

    print("[*] Waiting for frontend at http://127.0.0.1:5173 ...")
    if wait_for_http("http://127.0.0.1:5173", timeout=30):
        print("    [OK] Frontend is online!")
    else:
        print("    [*] Frontend is warming up...")

    app_url = "http://127.0.0.1:5173/Veyra-Know-When-Forecasts-May-Fail/"
    print(f"\n[*] Opening {app_url} in your browser...")
    webbrowser.open(app_url)

    print("\n" + "+" + "-" * 63 + "+")
    print("|   VEYRA SENTINEL is now running!                              |")
    print(f"|   Backend:  http://127.0.0.1:{backend_port} (Docs: /docs)               |")
    print("|   Frontend: http://127.0.0.1:5173/Veyra-Know-When-Forecasts-May-Fail/ |")
    print("|                                                               |")
    print("|   Press Ctrl+C or Enter to stop all servers...                |")
    print("+" + "-" * 63 + "+\n")

    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        print("\n[*] Stopping servers...")
        try:
            backend_proc.terminate()
            backend_proc.wait(timeout=3)
        except Exception:
            backend_proc.kill()

        try:
            frontend_proc.terminate()
            frontend_proc.wait(timeout=3)
        except Exception:
            frontend_proc.kill()

        free_ports([8000, 8001, 5173])
        if env_local.exists():
            try:
                env_local.unlink()
            except Exception:
                pass
        print("[OK] All servers stopped cleanly.")


if __name__ == "__main__":
    main()
