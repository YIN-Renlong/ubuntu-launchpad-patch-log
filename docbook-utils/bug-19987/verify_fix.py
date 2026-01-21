import sys

filename = "REAL_TEST.1"
try:
    with open(filename, "r") as f:
        content = f.read()
        # Look for literal backslash-hyphen-backslash-hyphen
        if "\\-\\-" in content or "\\-\\-robust\\-check" in content:
            print("PASS: Found escaped hyphens in " + filename)
            sys.exit(0)
        else:
            print("FAIL: Hyphens are not escaped in " + filename)
            sys.exit(1)
except FileNotFoundError:
    print("Error: File " + filename + " not found")
