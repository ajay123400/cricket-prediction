from tests.conftest import login


def _post_data(action):
    return {
        "title": "India vs Pakistan Prediction",
        "team_1": "India",
        "team_2": "Pakistan",
        "match_name": "India vs Pakistan",
        "match_date": "",
        "match_time": "",
        "tournament": "T20 World Cup",
        "venue": "",
        "category_id": "",
        "prediction": "team_1",
        "team_1_probability": "70",
        "team_2_probability": "30",
        "confidence": "high",
        "summary": "Test summary",
        "content": "Test content",
        "seo_title": "",
        "seo_description": "",
        "seo_keywords": "",
        "action": action,
    }


def test_draft_not_visible_on_public_site(client):
    login(client)
    client.post("/admin/posts/new", data=_post_data("save_draft"), follow_redirects=True)

    resp = client.get("/prediction/india-vs-pakistan-prediction")
    assert resp.status_code == 404

    home = client.get("/")
    assert b"India vs Pakistan" not in home.data


def test_publish_makes_post_visible(client):
    login(client)
    client.post("/admin/posts/new", data=_post_data("publish"), follow_redirects=True)

    resp = client.get("/prediction/india-vs-pakistan-prediction")
    assert resp.status_code == 200
    assert b"India" in resp.data and b"Pakistan" in resp.data

    home = client.get("/")
    assert b"India" in home.data
