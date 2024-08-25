from app.models import User


def test_create_button(admin_login):
    client, _ = admin_login

    response = client.get(
        "/admin/user/new/?url=/admin/user/",
    )

    assert response.status_code == 200
    assert "Save and Add Another" in response.text


def test_changing_user_data(app, admin_user, admin_login):
    client, response = admin_login

    user = User.query.filter_by(username=admin_user.username).first()

    response = client.post(
        f"/admin/user/edit/?id={user.user_id}",
        data={
            "username": "admin_2",
            "password": "12345678",
            "password_confirm": "12345678",
            "courses": "",
            "active": "y",
            "roles": "1",
        },
        follow_redirects=True,
    )

    user = User.query.filter_by(user_id=user.user_id).first()

    assert response.status_code == 200
    assert user.username == "admin_2"
