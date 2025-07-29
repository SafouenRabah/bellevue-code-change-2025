import json
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from pdfminer.high_level import extract_text


@dataclass
class Amendment:
    section_id: str
    new_text: str
    action: str = "amend"  # amend, repeal, reserve, add
    confidence: float = 0.0
    reasoning: str = ""


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def parse_ordinance_pdf(pdf_path: str) -> List[Amendment]:
    """Extract amendments from an ordinance PDF using simple heuristics."""
    text = extract_text(pdf_path)
    amendments: List[Amendment] = []

    pattern = re.compile(r"Section\s+([\d\.]+)(.*?)(?:\n|\r)", re.IGNORECASE)
    for match in pattern.finditer(text):
        section_id = match.group(1)
        remainder = match.group(2).lower()
        action = "amend"
        new_text = ""
        if "repealed" in remainder:
            action = "repeal"
        elif "reserved" in remainder:
            action = "reserve"
        else:
            # Attempt to capture the replacement text after phrases like "to read".
            next_section = re.search(r"Section\s+[\d\.]+", text[match.end():])
            end = next_section.start() if next_section else len(text)
            new_text = text[match.end():match.end()+end].strip()

        reasoning = f"Matched phrase: {match.group(0)[:40]}"
        confidence = 0.8 if action != "amend" or new_text else 0.5
        amendments.append(Amendment(section_id, new_text, action, confidence, reasoning))

    return amendments


def apply_amendments(luc_data: Dict[str, Any], amendments: List[Amendment]):
    """Modify LUC data based on parsed amendments."""
    sections = {s["id"]: s for s in luc_data.get("sections", [])}
    log = []

    for amend in amendments:
        existing = sections.get(amend.section_id, {})
        old_text = existing.get("text", "")

        if amend.action == "amend":
            sections[amend.section_id] = {
                "id": amend.section_id,
                "title": existing.get("title", ""),
                "text": amend.new_text or old_text,
            }
        elif amend.action == "repeal":
            sections[amend.section_id] = {
                "id": amend.section_id,
                "title": existing.get("title", ""),
                "text": "",
                "status": "REPEALED",
            }
        elif amend.action == "reserve":
            sections[amend.section_id] = {
                "id": amend.section_id,
                "title": existing.get("title", ""),
                "text": "",
                "status": "RESERVED",
            }
        elif amend.action == "add":
            sections[amend.section_id] = {
                "id": amend.section_id,
                "title": existing.get("title", ""),
                "text": amend.new_text,
            }

        entry = {
            "section": amend.section_id,
            "action": amend.action,
            "old_text": old_text,
            "new_text": sections[amend.section_id].get("text", ""),
            "reasoning": amend.reasoning,
            "confidence": amend.confidence,
        }
        if amend.confidence < 0.6:
            entry["TODO"] = "Review low confidence amendment"
        log.append(entry)

    luc_data["sections"] = list(sections.values())
    return luc_data, log


def main():
    luc_path = "docs/bellevue_amendments/LUC.json"
    pdf_path = "docs/bellevue_amendments/ordinance.pdf"

    luc = load_json(luc_path)
    amendments = parse_ordinance_pdf(pdf_path)
    updated, log = apply_amendments(luc, amendments)

    save_json(updated, "output_json/bellevue/LUC_amended.json")
    save_json(log, "output_json/bellevue/amendment_log.json")


if __name__ == "__main__":
    main()
