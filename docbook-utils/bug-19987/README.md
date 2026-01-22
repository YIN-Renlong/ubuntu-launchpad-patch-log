# Engineering Report: docbook-utils Hyphen Encoding Fix

**Bug ID:** [Ubuntu Launchpad #19987](https://bugs.launchpad.net/ubuntu/+source/docbook-utils/+bug/19987)
**Upstream ID:** [Debian Bug #208967](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=208967)
**Package:** `docbook-utils`
**Severity:** Medium (Lintian error / Copy-paste failure)
**Status:** Fixed, Patched, Verified

---

## 1. Test Environment
Verification was performed in a clean GitHub Codespace environment.

```text
Distributor ID: Ubuntu
Description:    Ubuntu 24.04.3 LTS
Release:        24.04
Codename:       noble
Kernel:         Linux 6.8.0-1030-azure x86_64
```

## 2. Problem Description
The `docbook2man` utility converts DocBook SGML `<option>` tags into man pages.
*   **Defect:** It rendered options as plain hyphens (`-`) instead of roff-escaped minus signs (`\-`).
*   **Impact:** Command line options copied from man pages fail in terminals; triggers Lintian tag `hyphen-used-as-minus-sign`.

---

## 3. The Solution (Patch)
I modified the Perl helper script `helpers/docbook2man-spec.pl` to capture the content of the `<OPTION>` tag and apply a Regex substitution.

**File: `fix.patch` (Content applied):**
```perl
sgml('<OPTION>', sub { 
    &bold_on; 
    push_output('string'); 
});

sgml('</OPTION>', sub { 
    my $content = pop_output(); 
    $content =~ s/-/\\-/g;  # <--- Global replacement of - with \-
    output $content; 
    &font_off; 
});
```

---

## 4. Verification Protocol

The following files are included in this repository to allow independent reproduction of the fix.

### A. Input Data (`reproduction.sgml`)
A standard DocBook RefEntry was created containing the string `--robust-check`.

**File Content:**
```sgml
<!DOCTYPE refentry PUBLIC "-//OASIS//DTD DocBook V3.1//EN">
<refentry>
  <refnamediv>
    <refname>checkme</refname>
    <refpurpose>Verification of hyphen encoding</refpurpose>
  </refnamediv>
  <refsynopsisdiv>
    <cmdsynopsis>
      <command>checkme</command>
      <arg choice="plain"><option>--robust-check</option></arg>
    </cmdsynopsis>
  </refsynopsisdiv>
</refentry>
```

### B. Automated Python Verification
A Python script was written to bypass shell escaping ambiguity and verify the string literal.

**File Content (`verify_fix.py`):**
```python
import sys

filename = "REAL_TEST.1"
try:
    with open(filename, "r") as f:
        content = f.read()
        # Look for literal backslash-hyphen-backslash-hyphen
        if "\\-\\-" in content:
            print("PASS: Found escaped hyphens in " + filename)
            sys.exit(0)
        else:
            print("FAIL: Hyphens are not escaped in " + filename)
            sys.exit(1)
except FileNotFoundError:
    print("Error: File " + filename + " not found")
```

**Execution Result:**
```text
$ python3 verify_fix.py
PASS: Found escaped hyphens in REAL_TEST.1
```

### C. Binary Verification (Hex Dump)
To ensure no hidden characters or encoding issues, an octal dump was analyzed on the generated artifact `REAL_TEST.1`.
*   Target string: `\-` (Backslash then Hyphen).
*   Hex values: `5c` (Backslash), `2d` (Hyphen).

**Command:**
```bash
grep "checkme" REAL_TEST.1 | od -t x1c
```

**Output:**
```text
0000020  42  5c  2d  5c  2d  72  6f  62  75  73  74  5c  2d  63  68  65
          B   \   -   \   -   r   o   b   u   s   t   \   -   c   h   e
```
**Conclusion:** The sequence `5c 2d` appears three times, corresponding to the two leading dashes and the internal hyphen in `robust\-check`. The fix is binary exact.


# Phase 2: Independent Cross-Verification Report

**Verification Target:** `docbook-utils` Hyphen Encoding Fix
**Verifier:** Independent Operator
**Infrastructure:** Oracle Cloud (OCI)
**Date:** 2026-01-21
**Status:** **PASSED (Robust Verification)**

---

## 1. Test Environment

To ensure the fix is not specific to the author's environment (Azure/GitHub Codespaces), a completely separate verification instance was provisioned on Oracle Cloud.

* **OS:** Ubuntu 24.04.2 LTS
* **Kernel:** Linux 6.8.0-1022-oracle x86_64
* **Package:** `docbook-utils` (Default Repository Version)

---

## 2. Reproduction Steps (Raw Commands)

The following commands were executed to replicate the bug and verify the fix. These steps use a manual logic injection to bypass potential `patch` command path mismatches.

### A. Setup and Baseline Failure
First, we establish the test environment and confirm the bug exists.

```bash
# 1. Install prerequisites
sudo apt update && sudo apt install -y docbook-utils wget

# 2. Prepare workspace
mkdir -p ~/docbook-verification
cd ~/docbook-verification

# 3. Create the reproduction SGML file
cat << 'EOF' > reproduction.sgml
<!DOCTYPE refentry PUBLIC "-//OASIS//DTD DocBook V3.1//EN"><refentry>
  <refnamediv>
    <refname>checkme</refname>
    <refpurpose>Verification of hyphen encoding</refpurpose>
  </refnamediv>
  <refsynopsisdiv>
    <cmdsynopsis>
      <command>checkme</command>
      <arg choice="plain"><option>--robust-check</option></arg>
    </cmdsynopsis>
  </refsynopsisdiv></refentry>
EOF

# 4. Copy the system Perl script locally (to avoid modifying system files)
cp /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl local-spec.pl

# 5. Run the conversion (Unpatched)
onsgmls reproduction.sgml | sgmlspl ./local-spec.pl > REAL_TEST.1
```

### B. Applying the Fix (Manual Logic Injection)
We manually modify the Perl script to inject the fix logic. This ensures the code is correct even if the `.patch` file fails due to version differences.

```bash
# 1. Disable the existing (buggy) OPTION handler
sed -i "s/sgml('<OPTION>',.*bold_.*);/# &/" local-spec.pl

# 2. Append the corrected logic to the end of the file
cat << 'EOF' >> local-spec.pl
# --- FIX APPLIED MANUALLY ---
sgml('<OPTION>', sub { 
    &bold_on; 
    push_output('string'); 
});

sgml('</OPTION>', sub { 
    my $content = pop_output(); 
    $content =~ s/-/\\-/g; 
    output $content; 
    &font_off; 
});
EOF
```

### C. Generating the Fixed Artifact

```bash
# Run the conversion again using the PATCHED script
onsgmls reproduction.sgml | sgmlspl ./local-spec.pl > REAL_TEST.1
```

---

## 3. Verification Results

We utilized three distinct methods to verify the fix.

### Method 1: Source Logic Check (Python)
We verified that the literal escape sequence `\-` exists in the file.

**Code:**
```python
cat << 'EOF' > verify_fix.py
import sys
filename = "REAL_TEST.1"

try:
    with open(filename, "r") as f:
        content = f.read()
        if "\\-\\-" in content:
            print("PASS: Found escaped hyphens in " + filename)
            sys.exit(0)
        else:
            print("FAIL: Hyphens are not escaped")
            sys.exit(1)
except FileNotFoundError:
    print("Error: File not found")
EOF

python3 verify_fix.py
```

**Result:**
```plaintext
PASS: Found escaped hyphens in REAL_TEST.1
```

### Method 2: Binary Integrity Check (Hex Dump)
We inspected the binary octal dump to ensure the sequence is `5c 2d` (Backslash `\` + Hyphen `-`) rather than just `2d`.

**Command:**
```bash
grep "robust" REAL_TEST.1 | od -t x1c
```

**Result:**
```plaintext
0000020  42  5c  2d  5c  2d  72  6f  62  75  73  74  5c  2d  63  68  65
          B   \   -   \   -   r   o   b   u   s   t   \   -   c   h   e
```
**Observation:** The sequence `5c 2d` appears three times. **PASS**.

### Method 3: Engine-Level Robustness Check (Groff Intermediate Output)
To eliminate ambiguity caused by terminal font rendering (UTF-8 vs ASCII), we inspected the `groff` typesetting engine's internal instruction set. We searched for the Semantic Minus Command (`C\-`).

**Command:**
```bash
groff -man -Z -Tps REAL_TEST.1 | grep -F "C\-"
```

**Result:**
```plaintext
C\-
C\-
C\-
C\-
```
**PASS:** Groff is explicitly using the SEMANTIC MINUS glyph (`C\-`).

---

## 4. Final Conclusion

The patch has been independently verified on a separate kernel and cloud architecture. The analysis of the `groff` intermediate output confirms that the patch successfully forces the typesetting engine to switch from a "Text Hyphen" context to a "Semantic Minus" context. The fix is robust, binary-exact, and reproducible.
