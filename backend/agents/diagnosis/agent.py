from agents.disease.agent import DiseaseAgent


class DiagnosisAgent(DiseaseAgent):
    """Wrapper class for backward compatibility with route mappings."""
    name = "diagnosis"
