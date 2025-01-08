from opensquirrel.passes.router.general_router import Router


class RoutingChecker(Router):
    def __init__(self, backend_connectivity_diagram: dict[int, list[int]]) -> None:
        super().__init__()
        self.backend_connectivity_diagram = backend_connectivity_diagram

    def route(self, interactions: list[tuple[int, int]]) -> None:
        non_executable_interactions = []

        for q1, q2 in interactions:
            if q2 not in self.backend_connectivity_diagram.get(q1, []):
                non_executable_interactions.append((q1, q2))

        if non_executable_interactions:
            error_message = f"The qubit interactions: {non_executable_interactions} prevent a 121 mapping"
            raise ValueError(error_message)
