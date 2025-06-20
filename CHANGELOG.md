# Changelog

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

### Types of changes:

* **Added** for new features.
* **Changed** for changes in existing functionality.
* **Fixed** for any bug fixes.
* **Removed** for now removed features.

## [ 0.5.0 ] - [ 2025-05-28 ]

### Added

- `MIPMapper` mapper pass.
- `asm_filter` method to the `Circuit` class to filter out assembly declarations by backend name.

### Fixed

- `RoutingValidator` ignores assembly declarations

## [ M.m.P ] - [ xxxx-yy-zz ]
- `asm_filter` method to the `Circuit` class to filter-out assembly declarations by backend name

### Changed

- Default gate identification check refactored (now including check for phase)
- `McKayDecomposer` checks X90 on BSR semantic instead of name

### Fixed

- `RoutingValidator` ignores assembly declarations

## [ 0.4.0 ] - [ 2025-04-28 ]

### Added

- Assembly declaration
- `Rn` unitary instruction
- `SWAP2CZDecomposer` decomposer pass
- `CZDecomposer` decomposer pass
- `ShortestPathRouter` router pass
- `RandomMapper` mapper pass
- `AStarRouter` router pass

### Changed

- libQASM 1.1.0 integrated (updated from 0.6.9)
- Refactor: removed generators
- Changed the `RoutingChecker` pass to a `RoutingValidator` pass
- Changed use of `native` to `primitive`, e.g. `NativeGateValidator` is now `PrimitiveGateValidator`
- Compilation passes accept `kwargs` as input

## [ 0.3.1 ] - [ 2025-01-31 ]

### Fixed

- Bug in the writing of SWAP instructions


## [ 0.3.0 ] - [ 2025-01-30 ]

### Added

- `NativeGateValidator` validator pass

### Changed

- Relaxed NumPy version requirement to `>=1.26` for all supported Python versions

### Fixed

- Fixed order of merging Bloch sphere rotations

## [ 0.2.0 ] - [ 2025-01-21 ]

### Added

- `init` non-unitary instruction
- `SWAP` two-qubit unitary instruction
- `barrier` and `wait` control instructions
- `SingleQubitGatesMerger` merger pass
- `SWAP2CNOTDecomposer` decomposer pass
- `CNOT2CZDecomposer` decomposer pass
- `RoutingChecker` routing pass
- Restore SGMQ notation for barrier groups in cQASMv1 Exporter

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
