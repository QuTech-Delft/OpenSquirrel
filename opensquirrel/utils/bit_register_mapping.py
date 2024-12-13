"""This module contains the ``BitStringMapping`` class."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opensquirrel.ir import Measure


class BitStringMapping:
    """Utility class to create bitstringmappings for opensquirrel exporter passes."""

    def __init__(self) -> None:
        """Init of the ``BitStringMapping``."""
        self._mapping: defaultdict[int, list[int]] = defaultdict(list)
        self._bit_allocation: dict[int, int] = {}

    def add_measure(self, g: Measure) -> None:
        """Add a acquisition_channel and bitstring_index of `g` to the mapping.

        Args:
            g: measurement to add the acquisition_channel and bitstring_index from.
        """
        acq_channel = g.qubit.index
        bit_idx = g.bit.index

        self._mapping[acq_channel].append(bit_idx)
        self._bit_allocation[bit_idx] = acq_channel

    def get_last_added_acq(self) -> tuple[int, int]:
        """Get the last added acquisition_channel corresponding acquisition_index.

        Especially useful when exporting to ``quantify_scheduler``, since not only the
        final acquisition_channel-acquisition_index pairs are needed, but also all
        intermediate pairs.

        Returns:
            Tuple containing the last added acquisition_channel and corresponding
            acquisition_index.
        """
        try:
            acq_channel = next(reversed(self._mapping))
        except StopIteration as e:
            msg = "BitStringMapping is empty, so there is no acq to get"
            raise ValueError(msg) from e
        acq_idx = len(self._mapping[acq_channel]) - 1
        return acq_channel, acq_idx

    def to_export_format(self) -> dict[str, dict[str, int]]:
        """Export to json format.

        For each bit, only the last executed measurement remains in the mapping.

        Returns:
            Dictionary with the following format:
            {
            "<acquisition_channel>":
            {
                "<acquisition_index>": <bitstring_index>,
                "<acquisition_index>": <bitstring_index>,
                ...
            },
            ...
            }
        """
        json_mapping: defaultdict[str, dict[str, int]] = defaultdict(dict)
        for acq_channel, bit_indices in self._mapping.items():
            for acq_idx, bit_idx in enumerate(bit_indices):
                if self._bit_allocation[bit_idx] == acq_channel:
                    json_mapping[str(acq_channel)][str(acq_idx)] = bit_idx
        return dict(json_mapping)
