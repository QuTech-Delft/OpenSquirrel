import math

from opensquirrel import Ry, Rz
from opensquirrel.ir import Axis, Gate, Instruction, Measure
from opensquirrel.passes.decomposer.general_decomposer import Decomposer
from opensquirrel.utils.general_math import acos
from opensquirrel.utils.identity_filter import filter_out_identities


class MeasureDecomposer(Decomposer):
    def decompose(self, instruction: Measure) -> list[Instruction]:

        if not isinstance(instruction, Measure):
            return [instruction]
        measure = instruction

        if measure.axis == Axis(0, 0, 1):
            return [measure]
        rotation_gates = self._get_rotation_gates(measure)
        return [*rotation_gates, Measure(measure.qubit, measure.bit, Axis(0, 0, 1))]

    def _get_rotation_gates(self, measure: Measure) -> list[Gate]:
        """Determines the rotation gates needed to rotate the measurement axis to the Z-axis.

        If the measurement axis is given by the unit vector
        $\\hat{n} = (n_x, n_y, n_z) = (\\sin\\theta\\cos\\phi, \\sin\\theta\\sin\\phi, \\cos\\theta)$,
        with $\\theta = \\arccos(n_z)$ and $\\phi = \\arctan2(n_y, n_x)$. We can define a unitary
        $U = Rz(\\phi) Ry(\\theta)$, that maps the +Z eigenstates to the $\\hat{n}$ eigenstates.

        Measuring in the $\\hat{n}$ direction is equivalent to first applying
        $U^\\dagger = R_y(-\\theta) R_z(-\\phi)$ and then measuring in the +Z direction.

        Order of instructions:
        1. Apply Rz(-φ).
        2. Apply Ry(-θ).
        3. Measure in the +Z direction.

        Args:
            measure: The measure instruction for which to determine the rotation gates.

        Returns:
            A list of gates that rotate the measurement axis to the +Z-axis.

        """
        n_x, n_y, n_z = measure.axis
        theta = acos(n_z)
        phi = math.atan2(n_y, n_x)

        return filter_out_identities(
            [
                Rz(measure.qubit, -phi),
                Ry(measure.qubit, -theta),
            ]
        )
