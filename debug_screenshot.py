import os
import subprocess
import platform

def check_env():
    print(f"Platform: {platform.platform()}")
    print(f"XDG_SESSION_TYPE: {os.environ.get('XDG_SESSION_TYPE')}")
    print(f"DISPLAY: {os.environ.get('DISPLAY')}")
    print(f"WAYLAND_DISPLAY: {os.environ.get('WAYLAND_DISPLAY')}")

    tools = ["gnome-screenshot", "scrot", "grim", "spectacle", "import"]
    for tool in tools:
        try:
            res = subprocess.run(["which", tool], capture_output=True, text=True)
            if res.returncode == 0:
                print(f"Tool {tool} is installed at: {res.stdout.strip()}")
            else:
                print(f"Tool {tool} is NOT found.")
        except Exception as e:
            print(f"Error checking {tool}: {e}")

if __name__ == "__main__":
    check_env()
    
    # Try mss
    print("\n--- Trying MSS ---")
    try:
        import mss
        with mss.mss() as sct:
            sct.shot()
            print("MSS Success (saved to monitor-1.png or similar)")
            if os.path.exists("monitor-1.png"): os.remove("monitor-1.png")
    except Exception as e:
        print(f"MSS Error: {e}")

    # Try gnome-screenshot
    print("\n--- Trying gnome-screenshot ---")
    try:
        res = subprocess.run(["gnome-screenshot", "-f", "test_gnome.png"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            print("gnome-screenshot Success")
            if os.path.exists("test_gnome.png"): os.remove("test_gnome.png")
        else:
            print(f"gnome-screenshot Failed: {res.stderr}")
    except Exception as e:
        print(f"gnome-screenshot Exception: {e}")
