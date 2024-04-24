def test_users_button(admin_user):
    client, admin_username, admin_password = admin_user

    response = client.post(
        "/login",
        data=dict(
            username=admin_username,
            password=admin_password,
        ),
    )
    response = client.get(
        "/admin/user/"
    )

    # Assert the presence of the button "Create"
    # (visible only in the /admin/user/ page)
    assert response.status_code == 200
    assert b"Create" in response.data