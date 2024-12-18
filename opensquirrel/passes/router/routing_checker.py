from opensquirrel.passes.router.general_router import Router
from typing import Any

class RoutingChecker(Router):

    def __init__(self, backend_connectivity_diagram: dict):
        self.backend_connectivity_diagram = backend_connectivity_diagram

    def route(self, interactions: list) -> None:

        non_executable_interactions = []

        for q1, q2 in interactions:
            if q2 not in self.backend_connectivity_diagram.get(q1):
                non_executable_interactions.append((q1, q2))

        if non_executable_interactions:
            raise ValueError(f"The algorithm can not be mapped to the target backend because of the following qubit interactions: {non_executable_interactions}")
        else:
            print("The algorithm can be mapped to the target backend")

