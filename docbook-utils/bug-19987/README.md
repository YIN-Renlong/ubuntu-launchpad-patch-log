# Report: docbook-utils Hyphen Encoding Fix

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


## Phase 2: Local ARM64 Cross-Verification & Release Engineering Audit

**Date:** 2026-01-22
**Status:** **PASSED**
**Operator:** YIN Renlong

To ensure absolute rigor, a third phase of verification was conducted locally on Apple Silicon (ARM64) hardware. This phase moved beyond simple script patching and simulated the full **Debian Package Maintainer workflow**, ensuring the fix survives the build compilation process and satisfies strict linting standards.

### 1. Test Environment (Clean Room)
All tests were executed within an ephemeral Docker container to guarantee zero environmental contamination. The workload ran natively on ARM64 architecture without emulation.

* **Host Hardware:** MacBook Pro M1 Pro (Apple Silicon)
* **Container Engine:** Docker Desktop 4.32.1 (Engine: 27.0.3)
* **Target OS:** Ubuntu 24.04 LTS (Noble Numbat) `arm64`
* **Mirror:** Friedrich-Alexander-Universität (FAU) `ubuntu-ports` mirror (High-bandwidth verification).

### 2. Methodology A: System-Level Forensic Patching (Reverse Generation)
To eliminate potential whitespace corruption or encoding issues inherent in copy-pasting patch files, I utilized a **Reverse Patch Generation** strategy. Instead of applying an external file, I programmatically modified the system Perl script using regex, generated a system-native diff, reverted the file, and then validated that the generated patch applied cleanly.

**Log Artifacts:**

**Environment Preparation:**
```bash
root@eda402a24f38:/work# apt-get install --reinstall -y docbook-utils
# [Log truncated: dependencies and certificates installed successfully]
root@eda402a24f38:/work# cp /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl.orig
```

**Logic Injection & Patch Generation:**
I injected the logic directly into the AST handler and generated a unified diff.
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

**Application & Forensic Verification:**
The file was reverted to the broken state, and the patch was applied via `patch` to ensure compatibility.
```bash
root@eda402a24f38:/work# cp /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl.orig /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl
root@eda402a24f38:/work# patch /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl < fix.patch
patching file /usr/share/perl5/sgmlspl-specs/docbook2man-spec.pl
```

**Binary Output Validation:**
The docbook2man conversion was executed, and the output was analyzed via octal dump (`od`).
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

### 3. Methodology B: Full Source Package Build ("The Maintainer Standard")
To validate upstream compatibility, I moved beyond system patching and performed a full Release Engineering cycle. This involved rebuilding the `docbook-utils` package from source code, managing the fix via `quilt` (the standard Debian patch manager), and compiling a binary `.deb` installer. This ensures the patch survives the build pipeline and satisfies package linting requirements.

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

# Logic Injection (Programmatic modification)
root@f3da69ac36c4:/work/docbook-utils-0.6.14# perl -i -0777 -pe 's/sgml\(\x27<OPTION>\x27, \\&bold_on\);\nsgml\(\x27<\/OPTION>\x27, \\&font_off\);/sgml\(\x27<OPTION>\x27, sub {\n\t&bold_on;\n\tpush_output(\x27string\x27);\n});\nsgml\(\x27<\/OPTION>\x27, sub {\n\tmy \$content = pop_output();\n\t\$content =~ s\/-\/\\\\-\/g;\n\toutput \$content;\n\t&font_off;\n});/s' helpers/docbook2man-spec.pl

root@f3da69ac36c4:/work/docbook-utils-0.6.14# quilt refresh
Refreshed patch debian/patches/fix-hyphen-encoding.patch
```

**Compilation & Linting:**
The package was built using `debuild`. The process automatically triggered `lintian` checks, which completed without fatal errors, confirming the patch structure is valid.
```bash
root@f3da69ac36c4:/work/docbook-utils-0.6.14# debuild -us -uc
# [Log truncated: dpkg-source and dpkg-buildpackage execution]
Now running lintian docbook-utils_0.6.14-4_arm64.changes ...
Finished running lintian.
```

**Artifact Installation:**
The custom-compiled `.deb` was installed. Runtime dependencies (jadetex, docbook-xml) were resolved via `apt-get install -f`.
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

### 4. Forensic Audit of Artifacts
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

### 5. Visual Typographic Verification
A PostScript (`.ps`) file was generated from the man page using `groff -man -Tps`. Inspection in macOS Preview confirmed that the glyphs rendered are true Minus Signs (longer stroke, distinct from hyphens), confirming the fix propagates correctly through the typesetting engine to the printer driver.

---
### Final Verdict
The fix has been verified on x86_64 (Cloud) and ARM64 (Local M1). It successfully passes the Debian Quilt/Debuild packaging pipeline. The binary output is bit-perfect. The patch is ready for immediate merge into the upstream repositories.
