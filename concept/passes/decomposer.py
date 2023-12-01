from abc import ABC, abstractmethod

class Decomposer(ABC):

    @classmethod
    @abstractmethod
    def apply(cls, ast: str, **kwargs):
        raise NotImplementedError

class DecomposerInferred(Decomposer):
    "Inferred decomposition"

    @classmethod
    def apply(cls, ast: str, **kwargs):
        return ast + "_decomposed_Inferred"


class DecomposerPredefined(Decomposer):
    "Predefined decomposition"

    @classmethod
    def apply(cls, ast: str, **kwargs):
        gates = ""
        assert 'target_info' in kwargs.keys(), "DecomposerPredefined requires input for target_info."
        for gate in kwargs['target_info']['native_gate_set']:
            gates += f"_[{gate}]"
        return ast + "_decomposed" + gates
