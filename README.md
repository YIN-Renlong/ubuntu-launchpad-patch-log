# Ubuntu/Debian Patch Log

This repository archives engineering analysis, patches, and verification logs for bugs submitted to the Ubuntu and Debian trackers.

Each entry contains the artifacts required to understand and verify a specific bug fix, ensuring a reproducible and transparent contribution process.

## Repository Structure

The repository is organized by package name and the corresponding bug ID:

```text
.
├── package-name/
│   └── bug-id/
│       ├── README.md           # Engineering analysis and verification log.
│       └── lp<bug-id>.debdiff  # The sponsorship-ready patch file.
```

## Contribution Log

| Fix Date   | Package       | Bug ID                                                       | Description                                       | Upstream Status | Report                                      |
| ---------- | ------------- | ------------------------------------------------------------ | ------------------------------------------------- | --------------- | ------------------------------------------- |
| 2026-01-27 | acpi-override | [#1892035](https://bugs.launchpad.net/ubuntu/+source/acpi-override/+bug/1892035) | Fix crash in update-acpi-override with empty dir. | Submitted       | [View Report](./acpi-override/bug-1892035/) |
| 2026-01-22 | docbook-utils | [#19987](https://bugs.launchpad.net/ubuntu/+source/docbook-utils/+bug/19987) | Resolve incorrect hyphen encoding in man pages.   | Submitted       | [View Report](./docbook-utils/bug-19987/)   |


## References

* [Ubuntu Bug Tracker (Launchpad)](https://bugs.launchpad.net/ubuntu)
* [Debian Bug Tracker](https://www.debian.org/Bugs/)
* [Ubuntu Packaging Guide](https://packaging.ubuntu.com/html/)

---

*Maintained by YIN Renlong*
