The measure decomposer (`MeasureDecomposer`) decomposes measurements along an arbitrary axis into at most 2 single-qubit gates followed by a measurement along the Z-axis.

## Theory

For a measurement axis defined by the unit vector
$$\hat{n} = (\sin\theta\cos\phi, \sin\theta\sin\phi, \cos\theta)$$

where $\theta = \arccos(n_z)$ and $\phi = \arctan2(n_y, n_x)$, we construct the unitary transformation:
$$U = R_z(\phi) R_y(\theta)$$

This unitary maps Z-axis eigenstates to eigenstates along the $\hat{n}$ direction. Measuring in the $\hat{n}$ basis is equivalent to applying the inverse transformation $U^\dagger = R_y(-\theta) R_z(-\phi)$ and then measuring along Z.

## Decomposition steps

1. Apply $R_z(-\phi)$
2. Apply $R_y(-\theta)$
3. Measure in the Z basis

## Common examples

| Measurement axis | Decomposition |
|---|---|
| Z | $I$ |
| X | $R_y(-\pi/2)$ |
| Y | $R_y(-\pi/2) \cdot R_z(\-pi/2)$ |
| H | $R_y(-\pi/4)$ |
