def test_upload_button(admin_login):
    client, _ = admin_login

    response = client.get("/admin/upload_admin/admin/upload/")

    # Assert the presence of the string "Upload a file"
    assert response.status_code == 200
    assert b"Upload a file" in response.data


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
    
def test_course_selection(admin_login, setup_course_and_exercise_data):
    """
    Test course selection and session storage.
    """
    client, _ = admin_login

    # Simulate form submission to select a course
    response = client.post(
        "/admin/upload_admin/admin/upload/",
        data={
            "courses": "Test Course",
            "select": "Submit",
        },
        follow_redirects=True
    )

    # Check if the session contains the selected course
    # "session_transaction()" is a method provided by Flask’s test_client()
    # It allows to access, inspect/modify values stored in the session during a test
    with client.session_transaction() as sess:
        # Retrieve value associated with key "selected_course" from session (a dictionary)
        assert sess.get("selected_course") == "Test Course"

    # Check for the flash message
    assert b"Course Test Course selected." in response.data

    # Verify the response status code
    assert response.status_code == 200
