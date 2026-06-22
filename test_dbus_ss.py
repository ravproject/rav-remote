import subprocess
import os

def test_dbus():
    print("--- Trying DBus GNOME Screenshot ---")
    out_path = os.path.abspath("test_dbus.png")
    cmd = [
        "gdbus", "call", "--session",
        "--dest", "org.gnome.Shell.Screenshot",
        "--object-path", "/org/gnome/Shell/Screenshot",
        "--method", "org.gnome.Shell.Screenshot.Screenshot",
        "true", "false", f"file://{out_path}"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print(f"STDOUT: {res.stdout}")
        print(f"STDERR: {res.stderr}")
        if os.path.exists(out_path):
            print("DBus Success!")
            os.remove(out_path)
        else:
            print("DBus Failed (no file).")
    except Exception as e:
        print(f"DBus Exception: {e}")

if __name__ == "__main__":
    test_dbus()
