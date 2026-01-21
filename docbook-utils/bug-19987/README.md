# Bug Fix: docbook-utils Hyphen Encoding (LP: #19987)

**Status:** Fixed & Verified  
**Package:** `docbook-utils`  
**Bug Report:** [Launchpad #19987](https://bugs.launchpad.net/ubuntu/+source/docbook-utils/+bug/19987) | [Debian #208967](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=208967)

## 1. The Issue
The `docbook2man` tool converts SGML `<option>` tags into plain hyphens (`-`) instead of roff-escaped minus signs (`\-`). 

**Why this matters:**
1.  **Copy-Paste Failures:** When users copy commands from man pages, plain hyphens are often interpreted incorrectly by terminals.
2.  **Lintian Errors:** Debian packaging standards require minus signs to be escaped. This triggers the Lintian warning: `hyphen-used-as-minus-sign`.

## 2. Reproduction
I reproduced the issue by creating a minimal SGML file containing an option tag.

**Test File (`reproduction.sgml`):**
```sgml
<!DOCTYPE refentry PUBLIC "-//OASIS//DTD DocBook V3.1//EN">
<refentry>
  <refnamediv><refname>test</refname><refpurpose>repro</refpurpose></refnamediv>
  <refsynopsisdiv>
    <cmdsynopsis>
      <command>test</command>
      <arg choice="plain"><option>--long-option</option></arg>
    </cmdsynopsis>
  </refsynopsisdiv>
</refentry>
```

**Command:**
```bash
docbook2man reproduction.sgml
```

**Output (Broken):**
```text
.OP - --long-option
```
*(Note the lack of backslashes before the hyphens)*

## 3. The Fix
I investigated the source code and located the conversion logic in `helpers/docbook2man-spec.pl`. The original code simply toggled bold font on/off without processing the text.

I applied a patch to capture the content within `<OPTION>` tags and use a Perl regex to escape the hyphens.

**Patch Logic:**
```perl
sgml('<OPTION>', sub { 
    &bold_on; 
    push_output('string'); 
});

sgml('</OPTION>', sub { 
    my $content = pop_output(); 
    $content =~ s/-/\\-/g;   # <--- The Fix: Replace '-' with '\-'
    output $content; 
    &font_off; 
});
```

## 4. Verification
I verified the fix using three distinct methods to ensure robustness against shell escaping issues.

### Method A: Build & Install
I generated a patch file (`dpkg-source --commit`), built the package (`debuild -us -uc`), and installed the resulting `.deb` file into the environment.

### Method B: Python Verification
Used a Python script to verify the file content without shell interference.
**Result:** `🐍 Python Verification: PASS (Found escaped hyphens)`

### Method C: Atomic Hex Dump
I inspected the raw bytes of the generated man page to confirm the presence of the backslash character (Byte `5c`).

**Command:**
```bash
grep "checkme" REAL_TEST.1 | od -t x1c
```

**Output Proof:**
```text
0000020  42  5c  2d  5c  2d  72  6f  62  75  73  74  5c  2d  63  68  65
          B   \   -   \   -   r   o   b   u   s   t   \   -   c   h   e
```
The sequence `5c 2d` (`\ -`) confirms the fix is binary-correct.

## 5. Files in this Directory
*   `fix.patch`: The official patch file submitted to fix the package.
*   `README.md`: This documentation.

