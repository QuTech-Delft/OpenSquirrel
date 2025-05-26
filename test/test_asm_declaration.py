import math

import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.parser.libqasm.parser import Parser
from opensquirrel.passes.merger import SingleQubitGatesMerger


def test_empty_raw_text_string() -> None:
    qc = Circuit.from_string(
        """
version 3.0

qubit q

asm(TestBackend) '''
'''
""",
    )
    assert (
        str(qc)
        == """version 3.0

qubit[1] q

asm(TestBackend) '''
'''
"""
    )


def test_single_line() -> None:
    qc = Circuit.from_string(
        """
version 3

qubit[2] q

H q[0]

asm(TestBackend) ''' a ' " {} () [] b '''

CNOT q[0], q[1]
""",
    )
    assert (
        str(qc)
        == """version 3.0

qubit[2] q

H q[0]
asm(TestBackend) ''' a ' " {} () [] b '''
CNOT q[0], q[1]
"""
    )


def test_multi_line() -> None:
    qc = Circuit.from_string(
        """
version 3

qubit[2] q

H q[0]

asm(TestBackend) '''
  a ' " {} () [] b
  // This is a single line comment which ends on the newline.
  /* This is a multi-
  line comment block */
'''

CNOT q[0], q[1]
        """,
    )
    assert (
        str(qc)
        == """version 3.0

qubit[2] q

H q[0]
asm(TestBackend) '''
  a ' " {} () [] b
  // This is a single line comment which ends on the newline.
  /* This is a multi-
  line comment block */
'''
CNOT q[0], q[1]
"""
    )


def test_invalid_backend_name() -> None:
    with pytest.raises(
        OSError,
        match=r"Error at <unknown file name>:5:13..16: mismatched input '100' expecting IDENTIFIER",
    ):
        Parser().circuit_from_string(
            """version 3.0

        qubit q

        asm(100) '''
        '''
        """
        )


def test_invalid_raw_text_string() -> None:
    with pytest.raises(
        OSError,
        match=r"Error at <unknown file name>:5:26..29: mismatched input ''''' expecting RAW_TEXT_STRING",
    ):
        Parser().circuit_from_string(
            """version 3

        qubit q

        asm(TestBackend) ''' a ' " {} () [] b
        """
        )


def test_asm_circuit_builder() -> None:
    builder = CircuitBuilder(2)
    builder.H(0)
    builder.asm("TestBackend", """ a ' " {} () [] b """)
    builder.CNOT(0, 1)
    qc = builder.to_circuit()
    assert (
        str(qc)
        == """version 3.0

qubit[2] q

H q[0]
asm(TestBackend) ''' a ' " {} () [] b '''
CNOT q[0], q[1]
"""
    )


def test_no_merging_across_asm() -> None:
    builder = CircuitBuilder(2)
    builder.H(0)
    builder.Y90(1)
    builder.asm("TestBackend", """ a ' " {} () [] b """)
    builder.H(0)
    builder.X90(1)
    qc = builder.to_circuit()
    qc.merge(merger=SingleQubitGatesMerger())
    assert (
        str(qc)
        == """version 3.0

qubit[2] q

H q[0]
Y90 q[1]
asm(TestBackend) ''' a ' " {} () [] b '''
H q[0]
X90 q[1]
"""
    )
