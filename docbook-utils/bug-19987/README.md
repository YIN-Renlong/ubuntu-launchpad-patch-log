# Report: docbook-utils Hyphen Encoding Patch & Verification

**Bug ID:** [Ubuntu Launchpad #19987](https://bugs.launchpad.net/ubuntu/+source/docbook-utils/+bug/19987)
**Upstream ID:** [Debian Bug #208967](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=208967)
**Package:** `docbook-utils`
**Severity:** Medium (Lintian error / Copy-paste failure)
**Status:** Fixed, Patched, Verified

---

# Phase 1: Primary Verification & Root Cause Analysis

## 1. Test Environment
I performed verification in a pristine GitHub Codespace environment to establish a baseline.

```text
Distributor ID: Ubuntu
Description:    Ubuntu 24.04.3 LTS
Release:        24.04
Codename:       noble
Kernel:         Linux 6.8.0-1030-azure x86_64
```

## 2. Problem Description
The `docbook2man` utility converts DocBook SGML `<option>` tags into man pages using an incorrect glyph.
*   **Defect:** It renders options as plain hyphens (`-`) instead of roff-escaped minus signs (`\-`).
*   **Impact:** Command line options copied from man pages fail in terminals; this triggers the Lintian tag `hyphen-used-as-minus-sign`.

---

## 3. Patch Implementation
My fix modifies the `SGMLSpm` specification file (`helpers/docbook2man-spec.pl`). I intercept the `<OPTION>` element stream, capture the buffer, and apply a regex substitution to enforce proper escaping.

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

I created the following artifacts to allow for independent reproduction of my fix.

### A. Input Data (`reproduction.sgml`)
I defined a minimal DocBook RefEntry containing the string `--robust-check` to isolate the conversion logic.

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
To verify the fix without ambiguity regarding shell string escaping/expansion, I utilized a Python script to inspect the raw file content.

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
To validate the file integrity at the byte level, I analyzed an octal dump on the generated artifact `REAL_TEST.1`.
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

---

# Phase 2: Independent Cross-Verification Report

**Verification Target:** `docbook-utils` Hyphen Encoding Fix
**Infrastructure:** Oracle Cloud (OCI)
**Date:** 2026-01-21
**Status:** **PASSED**

---

## 1. Test Environment

To ensure the fix is architecture-agnostic and not specific to my local environment, I provisioned a secondary validation instance on Oracle Cloud.

* **OS:** Ubuntu 24.04.2 LTS
* **Kernel:** Linux 6.8.0-1022-oracle x86_64
* **Package:** `docbook-utils` (Default Repository Version)

---

## 2. Reproduction Steps (Raw Commands)

I executed the following commands to replicate the bug and verify the fix. Note: I utilize direct stream editing (sed/cat) rather than `patch` to ensure application robustness against minor upstream version drift.

### A. Setup and Baseline Failure
Establishing the test environment and confirming the defect.

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

### B. Patch Application (Direct Modification)
I manually modified the Perl script to inject the fixed logic. This prevents potential patch fuzz/offset errors.

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

I utilized three distinct methods to verify the fix.

### Method 1: Source Logic Check (Python)
Verifying the literal escape sequence `\-` exists in the file.

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
I inspected the binary octal dump to ensure the sequence is `5c 2d` (Backslash `\` + Hyphen `-`) rather than just `2d`.

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
To eliminate ambiguity caused by terminal font rendering (UTF-8 vs ASCII), I inspected the `groff` typesetting engine's internal instruction set. I searched for the Semantic Minus Command (`C\-`).

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

# Phase 3: Local ARM64 Verification & Packaging Audit

**Date:** 2026-01-22
**Status:** **PASSED**
**Operator:** YIN Renlong

To ensure absolute rigor, I conducted a third phase of verification locally on Apple Silicon (ARM64) hardware. This phase simulated the full **Debian Package Maintainer workflow**, ensuring the fix survives the build compilation process and satisfies strict linting standards.

### 1. Test Environment
I executed tests within a clean Docker container to guarantee zero environmental contamination. The workload ran natively on ARM64 architecture without emulation.

* **Host Hardware:** MacBook Pro M1 Pro (Apple Silicon)
* **Container Engine:** Docker Desktop 4.32.1 (Engine: 27.0.3)
* **Target OS:** Ubuntu 24.04 LTS (Noble Numbat) `arm64`
* **Mirror:** Friedrich-Alexander-Universität (FAU) `ubuntu-ports` mirror (High-bandwidth verification).

### 2. Methodology A: Reverse Patch Generation
To eliminate potential encoding issues inherent in copy-pasting patch files, I utilized a **Reverse Patch Generation** strategy. I programmatically modified the system Perl script using regex, generated a system-native diff, reverted the file, and then validated that the generated patch applied cleanly.

**Log Artifacts:**

**Environment Preparation:**
```bash
root@eda402a24f38:/work# apt-get install --reinstall -y docbook-utils
# [Log truncated: dependencies and certificates installed successfully]
root@eda402a24f38:/work# cp /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl.orig
```

**In-Place Modification & Patch Generation:**
I injected the logic directly into the AST handler via Perl one-liner and generated a unified diff.
```bash
root@eda402a24f38:/work# perl -i -0777 -pe 's/sgml\(\x27<OPTION>\x27, \\&bold_on\);\nsgml\(\x27<\/OPTION>\x27, \\&font_off\);/sgml\(\x27<OPTION>\x27, sub {\n\t&bold_on;\n\tpush_output(\x27string\x27);\n});\nsgml\(\x27<\/OPTION>\x27, sub {\n\tmy \$content = pop_output();\n\t\$content =~ s\/-\/\\\\-\/g;\n\toutput \$content;\n\t&font_off;\n});/s' /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl
root@eda402a24f38:/work# diff -u /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl.orig /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl > fix.patch
```

**Patch Integrity Check:**
The system-generated patch matches the upstream submission logic exactly.
```diff
--- /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl.orig
+++ /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl
@@ -519,8 +519,16 @@
 sgml('<GROUP>', \&group_start);
 sgml('</GROUP>', \&group_end);
 
-sgml('<OPTION>', \&bold_on);
-sgml('</OPTION>', \&font_off);
+sgml('<OPTION>', sub {
+	&bold_on;
+	push_output('string');
+});
+sgml('</OPTION>', sub {
+	my $content = pop_output();
+	$content =~ s/-/\\-/g;
+	output $content;
+	&font_off;
+});
```

**Application & Verification:**
I reverted the file to the broken state, and applied the patch via `patch` to ensure compatibility.
```bash
root@eda402a24f38:/work# cp /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl.orig /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl
root@eda402a24f38:/work# patch /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl < fix.patch
patching file /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl
```

**Binary Output Validation:**
I executed the docbook2man conversion, and analyzed the output via octal dump (`od`).
```bash
root@eda402a24f38:/work# docbook2man reproduction.sgml > REAL_TEST.1
root@eda402a24f38:/work# grep "robust" REAL_TEST.1 | od -t x1c
0000000  5c  66  42  63  68  65  63  6b  6d  65  5c  66  52  20  5c  66
          \   f   B   c   h   e   c   k   m   e   \   f   R       \   f
0000020  42  5c  2d  5c  2d  72  6f  62  75  73  74  5c  2d  63  68  65
          B   \   -   \   -   r   o   b   u   s   t   \   -   c   h   e
0000040  63  6b  5c  66  52  0a
          c   k   \   f   R  \n
```
**Observation:** The sequence `5c 2d` (Escaped Minus) appears correctly at bytes 21 and 23.

### 3. Methodology B: Source Package Build ("Maintainer Standard")
To validate upstream compatibility, I performed a full Release Engineering cycle. This involved rebuilding the `docbook-utils` package from source code, managing the fix via `quilt` (the standard Debian patch manager), and compiling a binary `.deb` installer. This ensures the patch survives the build pipeline and satisfies package linting requirements.

**Log Artifacts:**

**Build Environment Initialization:**
I configured the environment to pull source code (`deb-src`) and utilized the high-bandwidth FAU mirror (ARM64) to resolve heavy build dependencies (TeXLive, Jade, SP).
```bash
root@f3da69ac36c4:/work# sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources
root@f3da69ac36c4:/work# apt-get build-dep -y docbook-utils
# [Log truncated: 5769 kB of build dependencies installed]
```

**Source Patching via Quilt:**
Instead of editing files directly, I registered the fix as a formal patch in the package's `debian/patches` series.
```bash
root@f3da69ac36c4:/work# apt-get source docbook-utils
root@f3da69ac36c4:/work/docbook-utils-0.6.14# export QUILT_PATCHES=debian/patches
root@f3da69ac36c4:/work/docbook-utils-0.6.14# quilt new fix-hyphen-encoding.patch
root@f3da69ac36c4:/work/docbook-utils-0.6.14# quilt add helpers/docbook2man-spec.pl

# Patch Application (Programmatic modification)
root@f3da69ac36c4:/work/docbook-utils-0.6.14# perl -i -0777 -pe 's/sgml\(\x27<OPTION>\x27, \\&bold_on\);\nsgml\(\x27<\/OPTION>\x27, \\&font_off\);/sgml\(\x27<OPTION>\x27, sub {\n\t&bold_on;\n\tpush_output(\x27string\x27);\n});\nsgml\(\x27<\/OPTION>\x27, sub {\n\tmy \$content = pop_output();\n\t\$content =~ s\/-\/\\\\-\/g;\n\toutput \$content;\n\t&font_off;\n});/s' helpers/docbook2man-spec.pl

root@f3da69ac36c4:/work/docbook-utils-0.6.14# quilt refresh
Refreshed patch debian/patches/fix-hyphen-encoding.patch
```

**Compilation & Linting:**
I built the package using `debuild`. The process automatically triggered `lintian` checks, which completed without fatal errors, confirming the patch structure is valid.
```bash
root@f3da69ac36c4:/work/docbook-utils-0.6.14# debuild -us -uc
# [Log truncated: dpkg-source and dpkg-buildpackage execution]
Now running lintian docbook-utils_0.6.14-4_arm64.changes ...
Finished running lintian.
```

**Artifact Installation:**
I installed the custom-compiled `.deb`. Runtime dependencies (jadetex, docbook-xml) were resolved via `apt-get install -f`.
```bash
root@f3da69ac36c4:/work# dpkg -i docbook-utils_0.6.14-4_all.deb
root@f3da69ac36c4:/work# apt-get install -f -y
# [Log truncated: dependencies resolved and package configured]
```

**Output Verification (The "Ghost File"):**
The docbook2man utility outputs to a file named after the SGML RefEntryTitle (CHECKME.1) rather than STDOUT. I verified the content of this generated file.
```bash
root@f3da69ac36c4:/work# docbook2man reproduction.sgml
root@f3da69ac36c4:/work# ls -l CHECKME.1
-rw-r--r-- 1 root root 444 Jan 22 11:00 CHECKME.1

root@f3da69ac36c4:/work# grep "robust" CHECKME.1 | od -t x1c
0000000  5c  66  42  63  68  65  63  6b  6d  65  5c  66  52  20  5c  66
          \   f   B   c   h   e   c   k   m   e   \   f   R       \   f
0000020  42  5c  2d  5c  2d  72  6f  62  75  73  74  5c  2d  63  68  65
          B   \   -   \   -   r   o   b   u   s   t   \   -   c   h   e
0000040  63  6b  5c  66  52  0a
          c   k   \   f   R  \n
```
**Observation:** The hex dump confirms the sequence `5c 2d` (Escaped Minus) is present in the binary built from the patched source.

### 4. Binary Output Validation
I verified the output of the custom-built package using a standard DocBook SGML test case (CHECKME).

**Command:**
```bash
grep "robust" CHECKME.1 | od -t x1c
```

**Hex Output Analysis:**
```text
0000020  42  5c  2d  5c  2d  72  6f  62  75  73  74  5c  2d  63  68  65
          B   \   -   \   -   r   o   b   u   s   t   \   -   c   h   e
```
* Byte 021-022: `5c 2d` -> `\-` (Escaped Minus)
* Byte 023-024: `5c 2d` -> `\-` (Escaped Minus)

### 5. Visual Regression Test (Side-by-Side Comparison)
I generated a PostScript file (`comparison.ps`) and converted it to PDF to visually verify the glyph rendering logic in the typesetting engine (`groff`). I manually injected a "Broken" line to demonstrate the difference.

**PostScript Source Analysis (Snippet):**
```ps
% Line 1: Patched (Uses \255 for Minus)
(1. P)108 165.6 Q (ATCHED...): E
(checkme \255\255rob)108 177.6 Q (ust\255check) E 

% Line 2: Broken (Uses standard Hyphens)
(2. BR)108 194.4 Q (OKEN...): E
(checkme --rob)108 206.4 Q (ust-check) E
```
*Note: `\255` is the Octal code for the Semantic Minus Sign in Groff's Times-Bold encoding.*

**Visual Result (Screenshot):**
![Visual Verification of Fix](img/comparison.png)

**Conclusion:**
*   **Patched Line:** Renders as `−−robust−check`. The glyphs are wide and distinct (U+2212).
*   **Broken Line:** Renders as `--robust-check`. The glyphs are short and stubby (U+002D).

---
### Final Verdict
I have verified the fix on x86_64 (Cloud) and ARM64 (Local M1). It successfully passes the Debian Quilt/Debuild packaging pipeline. The binary output is bit-perfect. The patch is ready for immediate merge into the upstream repositories.
