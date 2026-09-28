from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.adapters.rules.json_repository import JsonRuleRepository
from app.domain.rule_inspection import collect_question_fields


def main() -> int:
    root = ROOT
    questions_path = root / 'config' / 'questions.json'
    rules_dir = root / 'config' / 'rules'
    provider_path = root / 'config' / 'provider_catalog.csv'

    errors: list[str] = []

    raw_questions = json.loads(questions_path.read_text(encoding='utf-8'))
    ids = [str(item['id']) for item in raw_questions.get('questions', [])]
    if len(ids) != len(set(ids)):
        errors.append('Duplicate question IDs found.')

    repository = JsonRuleRepository(rules_dir, questions_path)
    questions = repository.questions()
    with provider_path.open(encoding='utf-8-sig', newline='') as handle:
        provider_rows = list(csv.DictReader(handle))
    service_ids = {str(row.get('service_id') or '') for row in provider_rows if row.get('service_id')}

    for rule in repository.active_rules():
        missing_questions = sorted(collect_question_fields(rule.expression) - set(questions))
        if missing_questions:
            errors.append(f'{rule.rule_version_id}: missing questions {missing_questions}')
        missing_actions = [
            str(action['service_id'])
            for action in rule.actions
            if action.get('service_id') and str(action['service_id']) not in service_ids
        ]
        if missing_actions:
            errors.append(f'{rule.rule_version_id}: missing provider service IDs {missing_actions}')

    if errors:
        print('SANDI configuration validation FAILED')
        for error in errors:
            print(f' - {error}')
        return 1

    print('SANDI configuration validation passed.')
    print(f'Questions: {len(questions)}')
    print(f'Active rule versions: {len(repository.active_rules())}')
    print(f'Provider/service rows: {len(provider_rows)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
