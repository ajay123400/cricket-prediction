from tests.conftest import login


def test_change_password_wrong_current(client):
    login(client)
    resp = client.post("/admin/settings", data={
        "action": "change_password",
        "current_password": "wrongpass",
        "new_password": "newpassword123",
        "confirm_password": "newpassword123",
    }, follow_redirects=True)
    assert b"Current password is incorrect" in resp.data


def test_change_password_mismatch(client):
    login(client)
    resp = client.post("/admin/settings", data={
        "action": "change_password",
        "current_password": "testpass123",
        "new_password": "newpassword123",
        "confirm_password": "different456",
    }, follow_redirects=True)
    assert b"do not match" in resp.data


def test_change_password_success_and_relogin(client):
    login(client)
    resp = client.post("/admin/settings", data={
        "action": "change_password",
        "current_password": "testpass123",
        "new_password": "newpassword123",
        "confirm_password": "newpassword123",
    }, follow_redirects=True)
    assert b"Password changed successfully" in resp.data

    client.get("/admin/logout")

    old_login = client.post("/admin/login", data={"username": "testadmin", "password": "testpass123"}, follow_redirects=True)
    assert b"Invalid username or password" in old_login.data

    new_login = client.post("/admin/login", data={"username": "testadmin", "password": "newpassword123"}, follow_redirects=True)
    assert b"Dashboard" in new_login.data
