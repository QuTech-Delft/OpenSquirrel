# Changelog

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

### Types of changes:

* **Added** for new features.
* **Changed** for changes in existing functionality.
* **Fixed** for any bug fixes.
* **Removed** for now removed features.

## [M.m.P] - [ yyyy-mm-dd ]

### Added

- `U`(theta, phi, lambda) gate to default single-qubit gates
- `Z90` and `mZ90` pi-half rotation gates (equivalent to `S` and `Sdag` gates)

### Changed

- Moved Bloch sphere rotation composition from the merger pass interface to Bloch sphere rotation semantic module.

## [ 0.8.0 ] - [ 2025-11-03 ]

### Added

- Processing of control instructions (Barrier, Wait) added to quantify-scheduler exporter

### Changed

- Refactor of visitor functionality of IR components and implementations
- Improved SWAP placement and refactor of common functionalities in existing router passes

## [ 0.7.0 ] - [ 2025-10-13 ]

### Added

- Support for Python 3.13 added

### Removed

- Support for Python 3.9 dropped

## [ 0.6.1 ] - [ 2025-10-06 ]

### Added

- `instruction_count` property to `Circuit`

### Fixed

- Autocompletion for `Circuitbuilder` gates
- Re-mapper properly handles remapping of target qubits

## [ 0.6.0 ] - [ 2025-08-28 ]

### Added

- `MIPMapper` mapper pass
- OpenSquirrel's `__version__` attribute exposed

### Changed

- `RoutingValidator` changed to `InteractionValidator`

### Fixed

- `ShortestPathRouter` and `AStarRouter` now correctly propagate SWAP gate insertion effects throughout the circuit
- The values for parameters `theta` and `phi` stay within the domain `(-pi, pi]` throughout parse- and compile-time
(_note_: gate modifiers have precedence over normalization)
- Mapping of the target qubits of controlled gates

## [ 0.5.0 ] - [ 2025-05-28 ]

### Added

- `asm_filter` method to the `Circuit` class to filter out assembly declarations by backend name

### Fixed

- `RoutingValidator` ignores assembly declarations

### Changed

- Default gate identification check refactored (now including check for phase)
- `McKayDecomposer` checks X90 on BSR semantic instead of name

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
