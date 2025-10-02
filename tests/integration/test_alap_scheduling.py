import pytest
import importlib

from opensquirrel import Circuit
from opensquirrel.passes.exporter import ExportFormat


class TestALAPScheduling:

    @pytest.fixture
    def qs_is_installed(self) -> bool:
        return importlib.util.find_spec("quantify_scheduler") is not None


    def test_hectoqubit_alap1(self, qs_is_installed: bool) -> None:
        qc = Circuit.from_string(
            """version 3.0

            qubit[5]  q
            bit[5]  b

            reset q
            barrier q
            X q[0]
            X q[0:1]
            X q[0:2]
            X q[0:3]
            X q[0:4]
            barrier q
            b = measure q
            """
        )

        if qs_is_installed:
            exported_schedule, _ = qc.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)

            # fig, _ = exported_schedule.plot_circuit_diagram(figsize=(20, 6))
            # fig.set_dpi(300)
            # fig.savefig("example.png")
            # fig.show()

    def test_hectoqubit_alap2(self, qs_is_installed: bool) -> None:

        qc = Circuit.from_string(
            """version 3.0

            qubit[5]  q
            bit[2]  b

            init q
            barrier q
            X q[3]
            barrier q[3,4]
            X q[4]
            barrier q[3,4]
            X q[4]
            b[0,1] = measure q[3,4]
            """
        )

        if qs_is_installed:
            exported_schedule, _ = qc.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)

            # fig, _ = exported_schedule.plot_circuit_diagram(figsize=(20, 6))
            # fig.set_dpi(300)
            # fig.savefig("example.png")
            # fig.show()

    def test_hectoqubit_alap3(self, qs_is_installed: bool) -> None:

        qc = Circuit.from_string(
            """version 3.0

            qubit[5]  q
            bit[5]  b

            init q
            barrier q
            mY90 q[2]
            CNOT q[2], q[0]
            CNOT q[2], q[1]
            CNOT q[2], q[3]
            CNOT q[2], q[4]
            barrier q
            b[0:4] = measure q[0:4]
            """
        )

        if qs_is_installed:
            exported_schedule, _ = qc.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)

            # fig, _ = exported_schedule.plot_circuit_diagram(figsize=(20, 6))
            # fig.set_dpi(300)
            # fig.savefig("example.png")
            # fig.show()

    def test_hectoqubit_alap4(self, qs_is_installed: bool) -> None:
        qc = Circuit.from_string(
            """version 3.0

            qubit[5] q
            bit[2] b
            init q[3]
            init q[2]
            barrier q[3]
            barrier q[2]
            Ry(-1.5707963) q[3]
            Ry(-1.5707963) q[2]
            CZ q[3], q[2]
            Ry(1.5707963) q[2]
            barrier q[3]
            barrier q[2]
            b[0] = measure q[3]
            b[1] = measure q[2]
            """
        )

        if qs_is_installed:
            exported_schedule, _ = qc.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)

            # fig, _ = exported_schedule.plot_circuit_diagram(figsize=(20, 6))
            # fig.set_dpi(300)
            # fig.savefig("example.png")
            # fig.show()