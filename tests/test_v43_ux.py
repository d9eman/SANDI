from fastapi.testclient import TestClient

from app.domain.provider_quality import service_quality
from app.main import create_app


def test_home_is_reduced_to_two_primary_paths(settings):
    client = TestClient(create_app(settings))
    text = client.get('/').text
    assert 'Find food near me' in text
    assert 'Check what I qualify for' in text
    assert 'simple-process' not in text
    assert text.count('path-card') >= 2


def test_question_page_has_timeline_progress_and_tap_choices(settings):
    client = TestClient(create_app(settings))
    start = client.get('/profile/start')
    import re
    csrf = re.search(r'name="csrf" value="([^"]+)"', start.text).group(1)
    response = client.post('/start', data={'csrf': csrf, 'need': 'food', 'danger': 'no', 'language': 'en', 'source': 'direct'}, follow_redirects=False)
    profile_id = response.headers['location'].split('/')[2]
    client.get(response.headers['location'])
    page = client.get(f'/p/{profile_id}/questions')
    assert 'Profile' in page.text and 'Answer' in page.text and 'Match' in page.text and 'Connect' in page.text
    assert '<progress' in page.text
    assert 'One question at a time' in page.text


def test_future_context_questions_are_dormant_until_a_rule_uses_them(settings):
    app = create_app(settings)
    questions = app.state.container.screening.rules.questions()
    assert 'veteran_status' in questions
    assert 'foster_care_history' in questions
    client = TestClient(app)
    start = client.get('/profile/start')
    import re
    csrf = re.search(r'name="csrf" value="([^"]+)"', start.text).group(1)
    response = client.post('/start', data={'csrf': csrf, 'need': 'food', 'danger': 'no', 'language': 'en', 'source': 'direct'}, follow_redirects=False)
    profile_id = response.headers['location'].split('/')[2]
    client.get(response.headers['location'])
    first_question = client.get(f'/p/{profile_id}/questions').text
    assert 'served in the U.S. military' not in first_question
    assert 'ever been in foster care' not in first_question


def test_provider_quality_rewards_data_completeness_not_volume():
    low = service_quality({'service_mode': 'direct_service', 'availability_status': 'UNKNOWN'})
    high = service_quality({
        'service_mode': 'direct_service', 'source_url': 'https://example.org', 'last_verified_at': '2026-08-31',
        'phone': '555', 'service_description': 'Food pantry', 'hours_text': 'Mon 9-12',
        'eligibility_summary': 'Open to residents', 'languages': 'English, Spanish', 'accessibility': 'Wheelchair',
        'availability_status': 'AVAILABLE', 'address': '123 Main', 'zip_code': '92101'
    })
    assert high['score'] > low['score']
    assert high['label'] == 'Ready to share'
