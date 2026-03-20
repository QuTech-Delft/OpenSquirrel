The measure decomposer (`MeasureDecomposer`) is used to decompose measurements along an arbitrary axis into
at most 2 single-qubit gates and a measurement along the +Z-axis.

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


Example decompositions are:

|Measurement axis |Decomposition                            |
|-----------------|-----------------------------------------|
|Z      |I                                      |  
|X      |Rz(\pi/2) \cdot X^{1/2} \cdot Rz(\pi/2)| 
|Y      |$X^{1/2} \cdot X^{1/2}$                  | 
|H      |$X^{1/2} \cdot X^{1/2} \cdot Rz(\pi)$    | 
