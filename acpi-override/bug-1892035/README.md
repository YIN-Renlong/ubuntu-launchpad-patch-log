# Engineering Report: acpi-override-initramfs Logic Failure

- **Bug ID**: [Ubuntu Launchpad #1892035](https://bugs.launchpad.net/ubuntu/+source/acpi-override/+bug/1892035)
- **Upstream ID**: [Debian Bug #968604](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=968604)
- **Package**: `acpi-override`
- **Version**: `0.1+nmu1` (Broken) -> `0.1+nmu1ubuntu1` (Fixed)
- **Severity**: High (Breaks kernel updates and package installation)
- **Status**: Fixed, Patched, Verified

---

## 1. Problem Analysis
The `acpi-override` hook script unconditionally executes `cp -a /var/lib/acpi-override/*`. When this directory is empty (the default state on a fresh install), the shell glob expansion (`*`) fails. Because the script runs with `set -e`, this causes `cp` to exit with an error, halting `update-initramfs`.

**Impact:** Users cannot install kernels or update system packages if this package is installed.

## 2. Technical Solution
Implemented a precondition check using a standard shell conditional. The script now verifies that the directory exists and contains files (`ls -A`) before attempting the copy operation.

**Patch Strategy**:
- **Toolchain:** `quilt` (Debian standard).
- **Target:** `acpi-override` script at source root.
- **Logic:** Wraps the copy command in `if [ -d ... ] && [ -n ... ]; then ... fi`.

---

## 3. Verification Protocol
Verification was conducted across **three isolated environments** to validate the build process, the upgrade path, and dependency resolution.

### Environment 1: Build & Unit Test
**Objective:** Create a clean package using standard Debian tools (`debuild`) and verify syntax.

**Procedure:**
1.  Imported source via `apt-get source`.
2.  Applied patch via `quilt`.
3.  Updated changelog via `sed`/`dch`.
4.  Built via `debuild -us -uc`.

**QA Result (Lintian):**
```text
W: acpi-override source: quilt-series-but-no-build-dep [debian/patches/series]
W: acpi-override source: source-contains-quilt-control-dir [.pc/]
```
*Note: Warnings are expected for converting a native package to a quilt-managed package.*

---

### Environment 2: A/B Integration Test (The "User Experience")
**Objective:** Prove that the upstream package fails, and the local fix repairs the system.
**Environment:** Clean Docker Container (`ubuntu:noble`).

#### Step A: The Control (Failure)
Installing the official repository version.
```bash
apt-get install -y acpi-override-initramfs linux-image-generic
```
**Raw Log Evidence:**
```text
update-initramfs: Generating /boot/initrd.img-6.8.0-90-generic
cp: cannot stat '/var/lib/acpi-override/*': No such file or directory
E: /usr/share/initramfs-tools/hooks/acpi-override failed with return 1.
...
E: Sub-process /usr/bin/dpkg returned an error code (1)
```
**Result:** CONFIRMED CRASH.

#### Step B: The Fix (Upgrade)
Upgrading the broken system using the locally built artifact.
```bash
apt-get install -y ./build/acpi-override-initramfs_0.1+nmu1ubuntu1_all.deb
```
**Raw Log Evidence:**
```text
Preparing to unpack .../acpi-override-initramfs_0.1+nmu1ubuntu1_all.deb ...
Unpacking acpi-override-initramfs (0.1+nmu1ubuntu1) over (0.1+nmu1) ...
Setting up acpi-override-initramfs (0.1+nmu1ubuntu1) ...
...
update-initramfs: Generating /boot/initrd.img-6.8.0-90-generic
```
**Result:** SUCCESS. The package repaired the broken installation state.

---

### Environment 3: Dependency Stress Test (The "Mechanic's Check")
**Objective:** Verify package metadata (`debian/control`) and recovery capability.
**Method:** Raw `dpkg` installation followed by dependency resolution.

#### Step A: Raw Installation
```bash
dpkg -i ./build/acpi-override-initramfs_0.1+nmu1ubuntu1_all.deb
```
**Raw Log Evidence (Dependency Validation):**
```text
dpkg: dependency problems prevent configuration of acpi-override-initramfs:
 acpi-override-initramfs depends on initramfs-tools-core; however:
  Package initramfs-tools-core is not installed.
```
*Status: PASS (Dependencies are correctly enforced).*

#### Step B: System Recovery
```bash
apt-get install -f -y  # Fix broken dependencies
apt-get install -y linux-image-generic # Install kernel to trigger hook
```
**Raw Log Evidence (Recovery):**
```text
Setting up acpi-override-initramfs (0.1+nmu1ubuntu1) ...
...
update-initramfs: Generating /boot/initrd.img-6.8.0-90-generic
```
*Status: PASS (System recovered and configured correctly).*

#### Step C: Final Logic Verification
Running the hook manually in both edge cases.

| Scenario                | Command                                                 | Result                 |
| :---------------------- | :------------------------------------------------------ | :--------------------- |
| **Empty Directory**     | `rm -f /var/lib/acpi-override/* && update-initramfs -u` | **PASS** (Exit Code 0) |
| **Populated Directory** | `touch .../test.aml && update-initramfs -u`             | **PASS** (Exit Code 0) |

---

## 4. Test Environment Details
All verification performed on Apple Silicon (M1/M2/M3) virtualization.

*   **Architecture:** `aarch64`
*   **Kernel:** `Linux fa3e8a49caee 6.6.32-linuxkit`
*   **OS:** `Ubuntu 24.04.3 LTS (Noble Numbat)`
*   **Installed Package:**
    ```text
    ii  acpi-override-initramfs  0.1+nmu1ubuntu1  all  initramfs-tools hook to override ACPI tables
    ```

## 5. Artifacts
*   **Patch File:** [`lp1892035-fix-empty-dir-crash.patch`](./lp1892035-fix-empty-dir-crash.patch) (Generated via `dpkg-source` with DEP-3 headers)
