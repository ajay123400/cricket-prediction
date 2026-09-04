from tests.conftest import login


def _post_data(action, title):
    return {
        "title": title,
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


def test_slug_change_301_redirects_old_url(client):
    login(client)
    client.post("/admin/posts/new", data=_post_data("publish", "India vs Pakistan Prediction"), follow_redirects=True)

    old_url = "/prediction/india-vs-pakistan-prediction"
    assert client.get(old_url).status_code == 200

    client.post("/admin/posts/edit/1", data=_post_data("publish", "India vs Pakistan Updated Prediction"), follow_redirects=True)

    resp = client.get(old_url, follow_redirects=False)
    assert resp.status_code == 301
    assert resp.headers["Location"].endswith("/prediction/india-vs-pakistan-updated-prediction")

    resp2 = client.get("/prediction/india-vs-pakistan-updated-prediction")
    assert resp2.status_code == 200
