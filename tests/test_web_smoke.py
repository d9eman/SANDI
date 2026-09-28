from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.main import create_app


def hidden_csrf(html: str) -> str:
    match = re.search(r'name="csrf" value="([^"]+)"', html)
    assert match
    return match.group(1)


def login(client, path, username, password):
    page = client.get(path)
    return client.post(
        path,
        data={"csrf": hidden_csrf(page.text), "username": username, "password": password},
        follow_redirects=False,
    )


def create_profile(client: TestClient, source: str = "direct") -> str:
    start = client.get(f"/profile/start?source={source}")
    response = client.post(
        "/start",
        data={
            "csrf": hidden_csrf(start.text),
            "need": "food",
            "danger": "no",
            "language": "en",
            "source": source,
        },
        follow_redirects=False,
    )
    profile_id = response.headers["location"].split("/")[2]
    client.get(response.headers["location"])
    return profile_id


def test_home_has_two_separate_start_paths(settings):
    client = TestClient(create_app(settings))
    response = client.get("/")
    assert response.status_code == 200
    assert "Find food near me" in response.text
    assert "Check what I qualify for" in response.text
    assert "See my matches" not in response.text
    assert 'action="/start"' not in response.text


def test_food_now_shows_maps_but_not_irrelevant_direct_site_or_applications(settings):
    client = TestClient(create_app(settings))
    response = client.get("/food-now?location=92101")
    assert response.status_code == 200
    assert "Find Food map" in response.text
    assert "GPS Food Locator" in response.text
    assert "CalFresh application assistance" not in response.text
    assert "North County Client Choice Pantry" not in response.text
    assert "Check what I qualify for" in response.text


def test_direct_site_only_appears_for_matching_zip(settings):
    client = TestClient(create_app(settings))
    response = client.get("/food-now?location=92081")
    assert "North County Client Choice Pantry" in response.text
    assert "Open site" in response.text


def test_location_control_has_explicit_status_and_coordinate_fields(settings):
    client = TestClient(create_app(settings))
    response = client.get("/food-now")
    assert 'id="use-my-location"' in response.text
    assert 'id="food-latitude"' in response.text
    assert 'id="food-longitude"' in response.text
    assert 'id="location-status"' in response.text
    javascript = client.get("/static/app.js").text
    assert "window.isSecureContext" in javascript
    assert "form.requestSubmit()" in javascript


def test_profile_goes_directly_to_eligibility_questions(settings):
    client = TestClient(create_app(settings))
    profile_id = create_profile(client)
    question = client.get(f"/p/{profile_id}/questions")
    assert question.status_code == 200
    assert "What ZIP code are you in now?" in question.text
    assert "Food maps for" not in question.text


def test_food_zip_is_reused_when_profile_created_after_food_finder(settings):
    app = create_app(settings)
    client = TestClient(app)
    client.get("/food-now?location=92101&urgency=now")
    profile_id = create_profile(client, source="food")
    profile = app.state.container.profiles.require(profile_id)
    assert profile.value("zip_code") == "92101"
    assert profile.value("urgency") == "now"
    question = client.get(f"/p/{profile_id}/questions")
    assert "What ZIP code are you in now?" not in question.text


def test_results_rank_matches_and_show_expected_vs_actual(settings):
    from datetime import date

    app = create_app(settings)
    app.state.container.screening.engine.today_provider = lambda: date(2026, 8, 2)
    client = TestClient(app)
    profile_id = create_profile(client)
    profile_service = app.state.container.profiles
    from app.domain.enums import AnswerState
    for question_id, value in {
        "zip_code": "92101",
        "household_size": 1,
        "monthly_income": 99999,
        "student_half_time": "no",
    }.items():
        profile_service.save_answer(profile_id, question_id, AnswerState.KNOWN, value)
    response = client.get(f"/p/{profile_id}/results")
    assert response.status_code == 200
    assert "Start with the best next step." in response.text
    assert "program" in response.text and "do not currently match" in response.text
    assert "Program expects" in response.text
    assert "Your answer" in response.text
    assert "Start the official application" in response.text


def test_resource_open_and_feedback_are_tracked(settings):
    app = create_app(settings)
    client = TestClient(app)
    page = client.get("/food-now?location=92101")
    open_response = client.get("/go/svc_feeding_sd_locator?location=92101", follow_redirects=False)
    assert open_response.status_code == 302
    feedback = client.post(
        "/resource-feedback",
        data={
            "csrf": hidden_csrf(page.text),
            "service_id": "svc_feeding_sd_locator",
            "outcome": "yes",
            "location": "92101",
            "note": "Found a site",
        },
        follow_redirects=False,
    )
    assert feedback.status_code == 303
    metrics = app.state.container.audit_repository.metrics()
    assert metrics["resource_opens"] == 1
    assert metrics["feedback_yes"] == 1


def test_staff_can_download_live_requirement_matrix(settings):
    client = TestClient(create_app(settings))
    assert login(client, "/staff/login", "staff", "test-password").status_code == 303
    response = client.get("/staff/eligibility-matrix.csv")
    assert response.status_code == 200
    assert "program_id,program_name,rule_version_id" in response.text
    assert "monthly_income" in response.text
    assert "What ZIP code are you in now?" in response.text


def test_staff_and_provider_form_login(settings):
    client = TestClient(create_app(settings))
    assert client.get("/staff", follow_redirects=False).status_code == 303
    assert client.get("/provider", follow_redirects=False).status_code == 303
    assert login(client, "/staff/login", "staff", "test-password").status_code == 303
    assert client.get("/staff").status_code == 200
    assert client.get("/staff/questions").status_code == 200

    client2 = TestClient(create_app(settings))
    assert login(client2, "/provider/login", "provider", "test-password").status_code == 303
    assert client2.get("/provider").status_code == 200
    assert "User journey stage" in client2.get("/provider/new").text


def test_home_changes_start_to_continue_only_after_profile_exists(settings):
    client = TestClient(create_app(settings))
    first = client.get("/")
    assert "Check what I qualify for" in first.text
    assert "Continue my eligibility check" not in first.text
    profile_id = create_profile(client)
    home = client.get("/")
    assert "Continue my eligibility check" in home.text
    assert f'/p/{profile_id}/questions' in home.text
    assert "See my matches" not in home.text


def test_stale_profile_cookie_is_cleared_without_internal_server_error(settings):
    app = create_app(settings)
    client = TestClient(app)
    profile_id = create_profile(client)
    with app.state.container.database.transaction() as connection:
        connection.execute("DELETE FROM profiles WHERE id=?", (profile_id,))

    food = client.get("/food-now")
    assert food.status_code == 200
    home = client.get("/")
    assert "Check what I qualify for" in home.text
    assert "Continue my eligibility check" not in home.text

    old_bookmark = client.get(f"/p/{profile_id}/questions", follow_redirects=False)
    assert old_bookmark.status_code == 303
    assert old_bookmark.headers["location"] == "/profile/start?notice=profile_not_found"


def test_interaction_repository_drops_missing_optional_foreign_keys(settings):
    app = create_app(settings)
    app.state.container.resource_repository.record_interaction(
        visitor_id="VIS-TEST",
        profile_id="SAN-NOTFOUND",
        service_id=None,
        action="search",
        metadata={"test": True},
    )
    with app.state.container.database.connect() as connection:
        row = connection.execute(
            "SELECT profile_id, metadata_json FROM resource_interactions WHERE visitor_id=?",
            ("VIS-TEST",),
        ).fetchone()
    assert row["profile_id"] is None
    assert "stale_profile_reference_removed" in row["metadata_json"]
