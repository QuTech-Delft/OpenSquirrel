import unittest

from opensquirrel.parse.antlr.qubit_range_checker import QubitRangeChecker
from opensquirrel.parse.antlr.squirrel_ir_from_string import antlr_tree_from_string


class QubitRangeCheckerTest(unittest.TestCase):
    @staticmethod
    def check(s):
        tree = antlr_tree_from_string(s)

        qubit_range_checker = QubitRangeChecker()
        qubit_range_checker.visit(tree)

    def test_valid(self):
        QubitRangeCheckerTest.check(
            """
version 3.0

qubit[3] q

gate1 q[0]
gate2 q[1]
gate3 q[2]
"""
        )

    def test_single_out_of_range(self):
        with self.assertRaisesRegex(Exception, "Qubit index 4 out of range"):
            QubitRangeCheckerTest.check(
                """
version 3.0

qubit[3] q

gate q[4]
"""
            )

    def test_many_out_of_range(self):
        with self.assertRaisesRegex(Exception, "Qubit index 5 out of range"):
            QubitRangeCheckerTest.check(
                """
version 3.0

qubit[3] q

gate q[1, 5]
"""
            )

    def test_malformed_range(self):
        with self.assertRaisesRegex(Exception, "Qubit index range 3:1 malformed"):
            QubitRangeCheckerTest.check(
                """
version 3.0

qubit[4] q

gate q[3:1]
"""
            )

    def test_range_out_of_range(self):
        with self.assertRaisesRegex(Exception, "Qubit index range 1:4 out of range"):
            QubitRangeCheckerTest.check(
                """
version 3.0

qubit[4] q

gate q[1:4]
"""
            )
