from opensquirrel import Circuit


def test_reset() -> None:
    qc = Circuit.from_string(
        """
        version 3.0

        qubit[2] q

        H q[0]

        reset q[0]
        """,
    )
    assert (
        str(qc)
        == """version 3.0

qubit[2] q

H q[0]
reset q[0]
"""
    )


def test_reset_sgmq() -> None:
    qc = Circuit.from_string(
        """
        version 3.0

        qubit[3] q

        reset q[0:2]
        """,
    )
    assert (
        str(qc)
        == """version 3.0

qubit[3] q

reset q[0]
reset q[1]
reset q[2]
"""
    )


# def test_reset_all() -> None:
#     qc = Circuit.from_string(
#         """
#         version 3.0
#
#         qubit[1] q
#         qubit[2] qq
#
#         reset
#         """,
#     )
#     assert (
#         str(qc)
#         == """version 3.0
#
# qubit[3] q
#
# reset q[0]
# reset q[1]
# reset q[2]
# """
#     )
