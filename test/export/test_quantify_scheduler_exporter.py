import contextlib
import importlib.util
import math
import unittest
import unittest.mock

from opensquirrel.common import ATOL
from opensquirrel.default_gates import CCZ, CZ, SWAP, H, Ry, Rz, X
from opensquirrel.export import quantify_scheduler_exporter
from opensquirrel.squirrel_ir import BlochSphereRotation, Float, Gate, Qubit, SquirrelIR


class FloatEq(float):
    def __eq__(self, other):
        return abs(self - other) < ATOL


class MockedQuantifyScheduler:
    def __enter__(self):
        self.patch_qs = unittest.mock.patch(
            "opensquirrel.export.quantify_scheduler_exporter.quantify_scheduler", create=True
        )

        self.patch_qs_gates = unittest.mock.patch(
            "opensquirrel.export.quantify_scheduler_exporter.quantify_scheduler_gates", create=True
        )

        with contextlib.ExitStack() as stack:
            self.mock_quantify_scheduler = stack.enter_context(self.patch_qs)
            self.mock_quantify_scheduler_gates = stack.enter_context(self.patch_qs_gates)
            self._stack = stack.pop_all()

        return self.mock_quantify_scheduler, self.mock_quantify_scheduler_gates

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._stack.__exit__(exc_type, exc_value, exc_traceback)


class QuantifySchedulerExporterTest(unittest.TestCase):
    def test_export(self):
        squirrel_ir = SquirrelIR(number_of_qubits=2, qubit_register_name="test")
        squirrel_ir.add_gate(X(Qubit(0)))
        squirrel_ir.add_gate(CZ(Qubit(0), Qubit(1)))
        squirrel_ir.add_gate(Rz(Qubit(1), Float(2.34)))
        squirrel_ir.add_gate(Ry(Qubit(2), Float(1.23)))

        with MockedQuantifyScheduler() as (mock_quantify_scheduler, mock_quantify_scheduler_gates):
            mock_schedule = unittest.mock.MagicMock()
            mock_quantify_scheduler.Schedule.return_value = mock_schedule

            quantify_scheduler_exporter.export(squirrel_ir)

            mock_quantify_scheduler.Schedule.assert_called_with("Exported OpenSquirrel circuit")

            mock_quantify_scheduler_gates.Rxy.assert_has_calls(
                [
                    unittest.mock.call(theta=FloatEq(math.pi), phi=FloatEq(0), qubit="test[0]"),
                    unittest.mock.call(theta=FloatEq(1.23), phi=FloatEq(math.pi / 2), qubit="test[2]"),
                ]
            )
            mock_quantify_scheduler_gates.CZ.assert_called_once_with(qC="test[0]", qT="test[1]")
            mock_quantify_scheduler_gates.Rz.assert_called_once_with(theta=FloatEq(2.34), qubit="test[1]")

            self.assertEqual(mock_schedule.add.call_count, 4)

    def check_gate_not_supported(self, g: Gate):
        squirrel_ir = SquirrelIR(number_of_qubits=20, qubit_register_name="test")
        squirrel_ir.add_gate(g)

        with MockedQuantifyScheduler():
            with self.assertRaisesRegex(Exception, "Cannot export circuit: it contains unsupported gates"):
                quantify_scheduler_exporter.export(squirrel_ir)

    def test_gates_not_supported(self):
        self.check_gate_not_supported(H(Qubit(0)))
        self.check_gate_not_supported(SWAP(Qubit(0), Qubit(1)))
        self.check_gate_not_supported(BlochSphereRotation(qubit=Qubit(0), axis=(1, 2, 3), angle=0.9876, phase=2.34))
        self.check_gate_not_supported(CCZ(Qubit(0), Qubit(1), Qubit(2)))


class QuantifySchedulerNotInstalledTest(unittest.TestCase):
    @unittest.skipIf(
        importlib.util.find_spec("quantify_scheduler") is not None, reason="quantify_scheduler is installed"
    )
    def test_quantify_scheduler_not_installed(self):
        with self.assertRaisesRegex(
            Exception, "quantify-scheduler is not installed, or cannot be installed on your system"
        ):
            quantify_scheduler_exporter.export(unittest.mock.MagicMock())
