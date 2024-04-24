def test_customer_login(customer_user):
    client, customer_username, customer_password = customer_user
    response = client.post(
        "/customer_login",
        data=dict(username=customer_username, password=customer_password),
    )

    assert response.status_code == 302
    assert response.location == f"/customer/{customer_username}/"


def test_admin_login_from_customer_endpoint(admin_user):
    client, admin_username, admin_password = admin_user

    response = client.post(
        "/customer_login",
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


def test_customer_logout(customer_user):
    client = customer_user[0]
    response = client.get("/logout")

    assert response.status_code == 302
    assert response.location == "/"