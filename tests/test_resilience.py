from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.main import create_app


def csrf(html: str) -> str:
    match = re.search(r'name="csrf" value="([^"]+)"', html)
    assert match
    return match.group(1)


def create_profile(client: TestClient) -> str:
    page = client.get('/profile/start')
    response = client.post(
        '/start',
        data={'csrf': csrf(page.text), 'need': 'food', 'danger': 'no', 'language': 'en', 'source': 'direct'},
        follow_redirects=False,
    )
    assert response.status_code == 303
    profile_id = response.headers['location'].split('/')[2]
    client.get(response.headers['location'])
    return profile_id


def current_question_id(html: str) -> str | None:
    match = re.search(r'action="/p/[^/]+/questions/([^"]+)"', html)
    return match.group(1) if match else None


def test_anonymous_partial_food_inputs_never_raise_500(settings):
    client = TestClient(create_app(settings), raise_server_exceptions=False)
    urls = [
        '/food-now',
        '/food-now?location=',
        '/food-now?location=not-a-zip',
        '/food-now?location=92130&urgency=unexpected',
        '/food-now?latitude=not-a-number&longitude=also-bad',
        '/food-now?latitude=nan&longitude=inf',
        '/food-now?location=' + ('x' * 1500),
    ]
    for url in urls:
        response = client.get(url)
        assert response.status_code < 500, (url, response.text)


def test_unknown_and_skip_can_finish_survey_without_dead_end(settings):
    client = TestClient(create_app(settings), raise_server_exceptions=False)
    profile_id = create_profile(client)
    seen: set[str] = set()
    for index in range(100):
        page = client.get(f'/p/{profile_id}/questions', follow_redirects=False)
        assert page.status_code < 500
        if page.status_code == 303:
            assert page.headers['location'] == f'/p/{profile_id}/results'
            break
        question_id = current_question_id(page.text)
        assert question_id
        assert question_id not in seen
        seen.add(question_id)
        response = client.post(
            f'/p/{profile_id}/questions/{question_id}',
            data={'csrf': csrf(page.text), 'answer_state': 'unknown' if index % 2 == 0 else 'skipped'},
            follow_redirects=False,
        )
        assert response.status_code == 303
    else:
        raise AssertionError('survey did not terminate after all available questions were unknown/skipped')
    results = client.get(f'/p/{profile_id}/results')
    assert results.status_code == 200
    assert 'Start with the best next step.' in results.text


def test_invalid_question_urls_and_answers_are_graceful(settings):
    client = TestClient(create_app(settings), raise_server_exceptions=False)
    profile_id = create_profile(client)
    fallback = client.get(f'/p/{profile_id}/questions?question=does_not_exist')
    assert fallback.status_code == 200

    page = client.get(f'/p/{profile_id}/questions?question=household_size')
    invalid_number = client.post(
        f'/p/{profile_id}/questions/household_size',
        data={'csrf': csrf(page.text), 'answer_state': 'known', 'value': 'nan'},
    )
    assert invalid_number.status_code == 400

    invalid_question = client.post(
        f'/p/{profile_id}/questions/not_a_question',
        data={'csrf': csrf(page.text), 'answer_state': 'known', 'value': 'anything'},
    )
    assert invalid_question.status_code == 404

    page = client.get(f'/p/{profile_id}/questions?question=student_half_time')
    invalid_choice = client.post(
        f'/p/{profile_id}/questions/student_half_time',
        data={'csrf': csrf(page.text), 'answer_state': 'known', 'value': 'not-an-option'},
    )
    assert invalid_choice.status_code == 400


def test_unknown_public_resources_and_feedback_do_not_500(settings):
    client = TestClient(create_app(settings), raise_server_exceptions=False)
    page = client.get('/food-now')
    assert client.get('/go/not-a-service').status_code == 404
    invalid_feedback = client.post(
        '/resource-feedback',
        data={'csrf': csrf(page.text), 'service_id': 'not-a-service', 'outcome': 'yes'},
    )
    assert invalid_feedback.status_code == 404
    invalid_outcome = client.post(
        '/resource-feedback',
        data={'csrf': csrf(page.text), 'service_id': 'svc_feeding_sd_locator', 'outcome': 'maybe'},
    )
    assert invalid_outcome.status_code == 400


def test_results_use_compact_food_shortcut_not_duplicate_food_assessment(settings):
    client = TestClient(create_app(settings))
    profile_id = create_profile(client)
    response = client.get(f'/p/{profile_id}/results')
    assert response.status_code == 200
    assert 'Need food now?' in response.text
    assert 'Open food finder' in response.text
    assert 'Food resources and navigation' not in response.text
    assert 'Available to everyone without completing the eligibility survey' not in response.text


def test_food_search_explains_what_changed_and_scroll_target(settings):
    client = TestClient(create_app(settings))
    initial = client.get('/food-now')
    assert 'No verified direct site in our small demo matched yet' not in initial.text
    assert 'action="/food-now#food-results"' in initial.text
    searched = client.get('/food-now?location=92130&urgency=today')
    assert searched.status_code == 200
    assert 'No verified direct site in our small demo matched yet' in searched.text
    assert '92130' in searched.text
    assert 'live countywide network' in searched.text


def test_bad_direct_referral_input_is_4xx_not_500(settings):
    client = TestClient(create_app(settings), raise_server_exceptions=False)
    profile_id = create_profile(client)
    page = client.get(f'/p/{profile_id}/referrals')
    response = client.post(
        f'/p/{profile_id}/referrals',
        data={
            'csrf': csrf(page.text),
            'provider_id': 'prov-not-real',
            'service_id': 'svc-not-real',
            'consent': 'yes',
        },
    )
    assert 400 <= response.status_code < 500


def test_survey_valid_answer_policy_completes_without_500(settings):
    app = create_app(settings)
    client = TestClient(app, raise_server_exceptions=False)
    profile_id = create_profile(client)
    catalog = app.state.container.screening.rules.questions()
    seen: set[str] = set()
    for _ in range(100):
        page = client.get(f'/p/{profile_id}/questions', follow_redirects=False)
        assert page.status_code < 500
        if page.status_code == 303:
            assert page.headers['location'] == f'/p/{profile_id}/results'
            break
        question_id = current_question_id(page.text)
        assert question_id and question_id not in seen
        seen.add(question_id)
        question = catalog[question_id]
        if question.question_id == 'zip_code':
            values = ['92101']
        elif question.answer_type == 'number':
            values = ['1']
        elif question.answer_type == 'single_select':
            values = [str(question.options[0]['value'])]
        elif question.answer_type == 'multi_select':
            values = [str(question.options[0]['value'])] if question.options else []
        else:
            values = ['test']
        payload = {'csrf': csrf(page.text), 'answer_state': 'known', 'value': values if len(values) > 1 else (values[0] if values else '')}
        response = client.post(f'/p/{profile_id}/questions/{question_id}', data=payload, follow_redirects=False)
        assert response.status_code == 303
    else:
        raise AssertionError('valid-answer survey did not terminate')
    assert client.get(f'/p/{profile_id}/results').status_code == 200
    assert client.get(f'/p/{profile_id}').status_code == 200
    assert client.get(f'/p/{profile_id}/referrals').status_code == 200
    assert client.get(f'/p/{profile_id}/documents').status_code == 200
