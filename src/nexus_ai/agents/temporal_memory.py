from nexus_ai.adapters.brain import BrainGateway, build_brain_gateway
from nexus_ai.services.brain import BrainCondition


class TemporalMemoryAgent:
    def __init__(self, brain_gateway: BrainGateway | None = None) -> None:
        self.brain_gateway = brain_gateway or build_brain_gateway()

    def get_relevant_conditions(self, patient_id: int) -> list[BrainCondition]:
        return self.brain_gateway.get_relevant_conditions(patient_id)
