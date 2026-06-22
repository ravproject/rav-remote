import subprocess
import sys
import json

def run_audit():
    print("Running pip-audit...")
    try:
        # Check if pip-audit is installed
        subprocess.run(["pip-audit", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("pip-audit not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pip-audit"], check=True)

    result = subprocess.run(
        ["pip-audit", "--requirement", "requirements.txt", "--format", "json"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ No vulnerabilities found in dependencies.")
        return True
    else:
        try:
            vulnerabilities = json.loads(result.stdout)
            print(f"❌ Found {len(vulnerabilities)} vulnerabilities!")
            for v in vulnerabilities:
                print(f"- {v['name']} ({v['version']}): {v['advisory']}")
        except:
            print(result.stdout)
            print(result.stderr)
        return False

if __name__ == "__main__":
    run_audit()
