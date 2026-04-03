import json
import subprocess
import os

def run_invoke(h, context):
    cmd = ["python3", "seed.py", "invoke", h, json.dumps(context)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    try:
        # Standardize on parsing the JSON result
        return json.loads(proc.stdout)
    except:
        return {"error": proc.stderr or proc.stdout}

print("--- Synapse Safety Test Harness ---")

# 1. Invalid Hash Format
print("\nTest 1: Invalid Hash Format...")
res = run_invoke("not-a-hash", {})
# The Linker returns failure result with 'error' key
if res.get("status") == "failure" and "Invalid SHA-256 Hash" in res.get("error", ""):
    print("PASS: Caught invalid hash format.")
else:
    print(f"FAIL: Expected error message, got: {res}")

# 2. ABI Violation (No 'result' assigned)
print("\nTest 2: ABI Violation...")
bad_blob = "log('hello')"
h = subprocess.check_output(["python3", "seed.py", "put", bad_blob], text=True).strip()
res = run_invoke(h, {})
if res.get("status") == "failure" and "ABI Violation" in str(res.get("error", "")):
    print("PASS: Caught ABI violation.")
else:
    print(f"FAIL: Expected ABI error, got: {res}")

# 3. Sandbox Breakout (open())
print("\nTest 3: Sandbox Breakout (open())...")
breakout_blob = "open('secret.txt', 'w').write('hacked')"
h = subprocess.check_output(["python3", "seed.py", "put", breakout_blob], text=True).strip()
res = run_invoke(h, {})
if res.get("status") == "failure" and "name 'open' is not defined" in str(res.get("error", "")):
    print("PASS: open() is restricted.")
else:
    print(f"FAIL: Sandbox breakout succeeded or wrong error: {res}")

# 4. Sandbox Breakout (import)
print("\nTest 4: Sandbox Breakout (import)...")
# Note: Python's exec() with restricted builtins often allows the 'import' syntax 
# but fails when it tries to access the __import__ builtin.
import_blob = "import os; result = os.getcwd()"
h = subprocess.check_output(["python3", "seed.py", "put", import_blob], text=True).strip()
res = run_invoke(h, {})
if res.get("status") == "failure" and ("name 'os' is not defined" in str(res.get("error", "")) or "__import__" in str(res.get("error", ""))):
    print("PASS: import is restricted.")
else:
    print(f"FAIL: import breakout succeeded or wrong error: {res}")

print("\n--- Safety Testing Complete ---")
