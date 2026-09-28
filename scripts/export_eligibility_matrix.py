#!/usr/bin/env python3
"""Generate a shareable CSV directly from active rule and question JSON files."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.adapters.rules.json_repository import JsonRuleRepository
from app.domain.rule_export import requirement_matrix_csv

repo = JsonRuleRepository(ROOT / "config" / "rules", ROOT / "config" / "questions.json")
out = ROOT / "docs" / "SANDI_Eligibility_Requirements_and_Questions.csv"
out.write_text(requirement_matrix_csv(repo.active_rules(), repo.questions()), encoding="utf-8-sig")
print(out)
