"""Verify the built exe starts and shows the window."""
import subprocess
import time
import sys

exe_path = sys.argv[1] if len(sys.argv) > 1 else "dist/Nudge/Nudge.exe"
print(f"Launching {exe_path}...")
proc = subprocess.Popen([exe_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(3)
if proc.poll() is not None:
    print(f"Process exited with code {proc.returncode}")
    stdout, stderr = proc.communicate()
    print("STDOUT:", stdout.decode()[:500])
    print("STDERR:", stderr.decode()[:500])
    sys.exit(1)
else:
    print("Process running — build OK")
    proc.terminate()
    sys.exit(0)
