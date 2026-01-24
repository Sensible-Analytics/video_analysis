from dataclasses import dataclass
from typing import Optional


@dataclass
class DiagramSpec:
    diagram_type: str
    mermaid: str


def normalize_mermaid(diagram_type: str, mermaid: str) -> Optional[DiagramSpec]:
    if not mermaid or not mermaid.strip():
        return None

    # Strip backticks and whitespace
    m = mermaid.strip().strip("`").strip()

    # Basic sanity: ensure first word matches type where applicable
    # We don't over-normalize; just ensure it's a valid block start.
    if diagram_type == "mindmap" and not m.lower().startswith("mindmap"):
        m = "mindmap\n  " + m
    elif diagram_type == "flowchart" and "flowchart" not in m.lower():
        m = "flowchart TD\n  " + m
    elif diagram_type == "hierarchy" and not m.lower().startswith("graph"):
        m = "graph TD\n  " + m
    elif diagram_type == "timeline" and "timeline" not in m.lower():
        # Mermaid doesn't have a native 'timeline' keyword; often flowchart is used.
        m = "flowchart TD\n  " + m

    return DiagramSpec(diagram_type=diagram_type, mermaid=m)
