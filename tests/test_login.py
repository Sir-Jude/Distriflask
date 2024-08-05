def test_student_login(student_user):
    client, student_username, student_password = student_user
    response = client.post(
        "/student_login",
        data=dict(username=student_username, password=student_password),
    )

    assert response.status_code == 302
    assert response.location == f"/student/{student_username}/"


def test_admin_login_from_student_endpoint(admin_user):
    client, admin_username, admin_password = admin_user

    response = client.post(
        "/student_login",
        data=dict(
            username=admin_username,
            password=admin_password,
        ),
    )

    assert response.status_code == 302
    assert response.location == "/admin/"


def test_admin_login_from_admin_endpoint(admin_user):
    client, admin_username, admin_password = admin_user

    response = client.post(
        "/login",
        data=dict(
            username=admin_username,
            password=admin_password,
        ),
    )

    assert response.status_code == 302
    assert response.location == "/admin/"


def test_admin_logout(admin_user):
    client = admin_user[0]
    response = client.get("/logout")

    assert response.status_code == 302
    assert response.location == "/"


def test_student_logout(student_user):
    client = student_user[0]
    response = client.get("/logout")

    assert response.status_code == 302
    assert response.location == "/"