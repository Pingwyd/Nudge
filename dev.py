"""Dev runner with hot-reload. Watches src/ for .py changes and restarts."""
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

WATCH_DIR = Path(__file__).parent / "src"
PROJECT_DIR = Path(__file__).parent


def ts():
    return datetime.now().strftime("%H:%M:%S")


def get_mtimes():
    times = {}
    for p in WATCH_DIR.rglob("*.py"):
        times[str(p)] = p.stat().st_mtime
    return times


def start_app():
    return subprocess.Popen(
        [sys.executable, "main.py"],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        cwd=str(PROJECT_DIR),
    )


def kill_app(proc):
    subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
        capture_output=True,
    )


def watch_and_restart(proc):
    prev = get_mtimes()
    while True:
        time.sleep(0.5)
        rc = proc.poll()
        if rc is not None:
            return False, rc
        current = get_mtimes()
        changed = [f for f in current if current[f] != prev.get(f)]
        if changed:
            print(f"\n[{ts()}] Changed: {', '.join(Path(f).name for f in changed)}")
            print(f"[{ts()}] Restarting...\n")
            kill_app(proc)
            proc.wait()
            time.sleep(2)
            return True, 0
        prev = current


def main():
    print(f"[{ts()}] Dev server started. Watching src/ for changes...\n")
    while True:
        proc = start_app()
        should_restart, rc = watch_and_restart(proc)
        if not should_restart:
            if rc != 0:
                print(f"[{ts()}] App crashed (exit code {rc}). Waiting for changes...\n")
                prev = get_mtimes()
                while True:
                    time.sleep(1)
                    current = get_mtimes()
                    changed = [f for f in current if current[f] != prev.get(f)]
                    if changed:
                        print(f"[{ts()}] Detected change, restarting...\n")
                        break
                    prev = current
            else:
                break


if __name__ == "__main__":
    main()
