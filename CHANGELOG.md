# Changelog

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

### Types of changes:
* **Added** for new features.
* **Changed** for changes in existing functionality.
* **Deprecated** for soon-to-be removed features.
* **Removed** for now removed features.
* **Fixed** for any bug fixes.
* **Security** in case of vulnerabilities.

## [ 0.2.0 ] - [ 2025-01-08 ]

### Added

- `init` non-unitary instruction
- `SWAP` two-qubit unitary instruction
- `barrier` and `wait` control instructions
- `SingleQubitGatesMerger` merger pass
- `SWAP2CNOTDecomposer` decomposer pass
- `CNOT2CZDecomposer` decomposer pass

### Changed

- Importing modules, classes, and functionalities simplified
- `merge_single_qubit_gates` method of `Circuit` class,
changed to general `merge` method that accepts custom merger passes
- libQASM 0.6.9 integrated (updated from 0.6.7)
- Refactor: code base adheres to the PEP8 style guide
- Refactor: instruction library simplified
- Refactor: comment nodes removed from IR

### Fixed

- Bug in ABA-decomposer
- Bug in McKay-decomposer (all single-qubit Clifford gates are verified)
