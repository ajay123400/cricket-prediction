from tests.conftest import login


def test_login_page_loads(client):
    resp = client.get("/admin/login")
    assert resp.status_code == 200


def test_dashboard_requires_login(client):
    resp = client.get("/admin/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/login" in resp.headers["Location"]


def test_login_wrong_password(client):
    resp = client.post("/admin/login", data={"username": "testadmin", "password": "wrong"}, follow_redirects=True)
    assert b"Invalid username or password" in resp.data


def test_login_success_and_dashboard_access(client):
    resp = login(client)
    assert resp.status_code == 200
    resp2 = client.get("/admin/dashboard")
    assert resp2.status_code == 200


def test_logout(client):
    login(client)
    resp = client.get("/admin/logout", follow_redirects=False)
    assert resp.status_code == 302
    resp2 = client.get("/admin/dashboard", follow_redirects=False)
    assert resp2.status_code == 302
