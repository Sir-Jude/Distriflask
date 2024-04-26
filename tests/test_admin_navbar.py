def test_users_button(admin_login):
    client = admin_login

    response = client.get(
        "/admin/user/"
    )

    # Assert the presence of the button "Create" and "With selected"
    # (visible on the /admin/user/ page)
    assert response.status_code == 200
    assert b"Create" in response.data
    assert b"With selected" in response.data


def test_upload_button(admin_login):
    client = admin_login

    response = client.get(
        "/admin/upload_admin/admin/upload/"
    )

    # Assert the presence of the string "Upload a file"
    assert response.status_code == 200
    assert b"Upload a file" in response.data


def test_download_button(admin_login):
    client = admin_login

    response = client.get(
        "/admin/download_admin/admin/download/"
    )

    # Assert the presence of the string "Download a file"
    assert response.status_code == 200
    assert b"Download a file" in response.data