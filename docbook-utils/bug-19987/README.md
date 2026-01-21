# Engineering Report: docbook-utils Bug Fix (LP: #19987)

**Bug ID:** [Launchpad #19987](https://bugs.launchpad.net/ubuntu/+source/docbook-utils/+bug/19987)
**Package:** `docbook-utils`
**Severity:** Medium (Lintian error / Copy-paste failure)
**Status:** Fixed, Patched, Verified

---

## 1. Test Environment
Verification was performed in a clean GitHub Codespace environment.

*   **Distributor ID:** Ubuntu
*   **Description:** Ubuntu 24.04.3 LTS
*   **Release:** 24.04
*   **Codename:** noble
*   **Kernel:** Linux 6.8.0-1030-azure x86_64

## 2. Problem Description
The `docbook2man` utility converts DocBook SGML `<option>` tags into man pages.
**Defect:** It rendered options as plain hyphens (`-`) instead of roff-escaped minus signs (`\-`).
**Impact:** 
1.  Command line options copied from man pages often fail in terminals.
2.  Triggers Lintian tag: `hyphen-used-as-minus-sign`.

## 3. The Fix Implementation
The conversion logic resides in `helpers/docbook2man-spec.pl`. The original code merely toggled the bold font attribute. I introduced a capture logic to apply a Regex substitution on the content.

**Applied Patch (Perl):**
```perl
sgml('<OPTION>', sub { 
    &bold_on; 
    push_output('string'); 
});

sgml('</OPTION>', sub { 
    my $content = pop_output(); 
    $content =~ s/-/\\-/g;  # Global replacement of - with \-
    output $content; 
    &font_off; 
});
```

---

## 4. Verification Protocol

### A. Input Data (`reproduction.sgml`)
A standard DocBook RefEntry was created containing the string `--robust-check`.
*(See `reproduction.sgml` in this repository)*

### B. Output Artifact (`REAL_TEST.1`)
The SGML was processed using the patched `docbook2man`.
**Command:** `docbook2man reproduction.sgml > REAL_TEST.1`

**Content of generated file:**
```troff
.SH SYNOPSIS
\fBcheckme\fR \fB\-\-robust\-check\fR
```
*Observation: The double backslashes indicate correct escaping.*

### C. Automated Python Verification
A Python script was written to bypass shell escaping ambiguity and verify the string literal.

**Script (`verify_fix.py`):**
```python
import sys

filename = "REAL_TEST.1"
try:
    with open(filename, "r") as f:
        content = f.read()
        # Look for literal backslash-hyphen sequence
        if "\\-\\-" in content:
            print("PASS: Found escaped hyphens in " + filename)
            sys.exit(0)
        else:
            print("FAIL: Hyphens are not escaped")
            sys.exit(1)
except FileNotFoundError:
    print("Error: File not found")
```

**Execution Result:**
```text
PASS: Found escaped hyphens in REAL_TEST.1
```

### D. Binary Verification (Hex Dump)
To ensure no hidden characters or encoding issues, an octal dump was analyzed.
Target string: `\-` (Backslash then Hyphen).
Hex values: `5c` (Backslash), `2d` (Hyphen).

**Command:**
```bash
grep "checkme" REAL_TEST.1 | od -t x1c
```

**Output:**
```text
0000020  42  5c  2d  5c  2d  72  6f  62  75  73  74  5c  2d  63  68  65
          B   \   -   \   -   r   o   b   u   s   t   \   -   c   h   e
```
**Conclusion:** The sequence `5c 2d` appears three times, corresponding to `\-`, `\-`, and the internal hyphen in `robust\-check`. The fix is binary exact.

---

## 5. Repository Contents
*   `fix.patch`: The generated debdiff for the package.
*   `reproduction.sgml`: Input source for verification.
*   `REAL_TEST.1`: Output man page proving the fix.
*   `verify_fix.py`: Automation script used for testing.

