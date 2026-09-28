from __future__ import annotations

import csv
import json

from app.adapters.rules.json_repository import JsonRuleRepository
from app.domain.rule_inspection import collect_question_fields


def test_question_ids_are_unique(settings):
    raw = json.loads(settings.questions_path.read_text(encoding='utf-8'))
    ids = [item['id'] for item in raw['questions']]
    assert len(ids) == len(set(ids)), 'Duplicate question IDs make rule references ambiguous.'


def test_every_active_rule_field_has_a_question(settings):
    repository = JsonRuleRepository(settings.rules_dir, settings.questions_path)
    questions = repository.questions()
    missing: dict[str, list[str]] = {}
    for rule in repository.active_rules():
        unresolved = sorted(collect_question_fields(rule.expression) - set(questions))
        if unresolved:
            missing[rule.rule_version_id] = unresolved
    assert not missing


def test_rule_action_service_ids_exist_in_provider_catalog(settings):
    repository = JsonRuleRepository(settings.rules_dir, settings.questions_path)
    with settings.provider_seed_path.open(encoding='utf-8-sig', newline='') as handle:
        service_ids = {row['service_id'] for row in csv.DictReader(handle) if row.get('service_id')}
    missing: dict[str, list[str]] = {}
    for rule in repository.active_rules():
        unresolved = [
            str(action['service_id'])
            for action in rule.actions
            if action.get('service_id') and action['service_id'] not in service_ids
        ]
        if unresolved:
            missing[rule.rule_version_id] = unresolved
    assert not missing
