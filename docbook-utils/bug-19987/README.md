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

