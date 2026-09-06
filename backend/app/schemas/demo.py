from pydantic import BaseModel


class DemoScenario(BaseModel):
    id: str
    name: str
    description: str
    document_type: str
    document_label: str


SCENARIOS = [
    DemoScenario(id="demo-clean", name="CLEAN DOCUMENT - DEMO", description="Synthetic baseline with fictional fields.", document_type="passport", document_label="SYNTHETIC TEST DOCUMENT - NOT VALID FOR TRAVEL OR IDENTIFICATION"),
    DemoScenario(id="demo-warning", name="DOCUMENT WITH WARNINGS - DEMO", description="Synthetic low-detail document for uncertainty handling.", document_type="passport", document_label="SYNTHETIC TEST DOCUMENT - CONTROLLED WARNING CASE"),
    DemoScenario(id="demo-tampered", name="SYNTHETIC TAMPER CASE - DEMO", description="Synthetic altered presentation for forensic baseline review.", document_type="passport", document_label="SYNTHETIC TEST DOCUMENT - CONTROLLED TAMPER CASE"),
]
