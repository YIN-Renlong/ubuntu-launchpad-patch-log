# Ubuntu Launchpad Patch Log

This repository serves as a centralized archive of engineering reports, patch files, and independent verification logs for bugs submitted to the [Ubuntu Launchpad](https://launchpad.net/ubuntu) tracking system.

The primary goal is to provide **reproducible proof** for every submitted patch, ensuring that fixes are tested in clean and isolated environments before upstream submission.

## Repository Structure

The repository is organized hierarchically by package name and bug ID:

```text
.
├── package-name/
│   └── bug-id/
│       ├── report.md       # Detailed verification report
│       ├── fix.patch       # The raw patch file
│       ├── reproduction/   # Scripts to reproduce the bug (MRE)
│       └── artifacts/      # Binary dumps or logs proving the fix
```

## Patch Log

| Package | Bug ID | Description | Status | Verification Report |
| :--- | :--- | :--- | :--- | :--- |
| `docbook-utils` | [#19987](https://bugs.launchpad.net/ubuntu/+source/docbook-utils/+bug/19987) | **Hyphen Encoding Fix:** Resolves incorrect rendering of options in man pages (Lintian `hyphen-used-as-minus-sign`). | ✅ Verified | [View Report](./docbook-utils/bug-19987/) |


## 🔗 References

* [Ubuntu Bug Tracker (Launchpad)](https://bugs.launchpad.net/ubuntu)
* [Debian Bug Tracker](https://www.debian.org/Bugs/)
* [Ubuntu Packaging Guide](https://packaging.ubuntu.com/html/)

---

*Maintained by YIN Renlong*
