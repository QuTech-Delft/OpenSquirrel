from opensquirrel import Circuit


def test_empty_raw_text_string():
    qc = Circuit.from_string(
        """
        version 3.0

        qubit q

        asm(TestBackend) '''
        '''
        """,
    )


def test_single_line():
    qc = Circuit.from_string(
        """
        version 3

        qubit[2] q

        H q[0]

        asm(TestBackend) ''' a ' " {} () [] b '''

        CNOT q[0], q[1]
        """,
    )


def test_multi_line():
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


# def test_invalid_backend_name():
#     qc = Circuit.from_string(
#         """
#         version 3.0
#
#         qubit q
#
#         asm(100) '''
#         '''
#         """,
#     )


# def test_invalid_backend_name():
#     qc = Circuit.from_string(
#         """
#         version 3
#
#         qubit q
#
#         asm(TestBackend) ''' a ' " {} () [] b
#         """,
#     )
