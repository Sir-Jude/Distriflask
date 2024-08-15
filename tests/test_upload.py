def test_index_redirects_to_upload(admin_login):
    """
    Test that accessing index route redirects to upload route.
    """
    # Login as admin using the provided fixture
    client, _ = admin_login

    # Access the index route of UploadAdminView
    response = client.get("/admin/upload_admin/")

    # Assert that the response is a redirect to the upload route
    assert response.status_code == 302
    assert response.location == "/admin/upload_admin/admin/upload/"


def test_handle_view_redirects_to_login(client):
    """
    Test that accessing restricted view redirects to login page if not logged in.
    """
    # Access a restricted view without being logged in
    response = client.get("/admin/upload_admin/admin/upload/")

    # Assert that the response is a redirect to the login route
    assert response.status_code == 302
    assert response.location == "/login"
