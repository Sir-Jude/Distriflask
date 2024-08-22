def test_users_button(admin_login):
    client, _ = admin_login

    response = client.get("/admin/user/")

    # Assert the presence of the button "Create" and "With selected"
    # (visible on the /admin/user/ page)
    assert response.status_code == 200
    assert b"Create" in response.data
    assert b"With selected" in response.data
    

def test_handle_view_redirects_to_login(client):
    """
    Test that accessing admin view redirects to the login page when not logged in.
    """
    # Access the restricted view without being logged in
    response = client.get("/admin/user/")

    # Assert that the response is a redirect to the login route
    assert response.status_code == 302  # 302 status code means redirection
    assert response.location == "/login"





