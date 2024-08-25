def test_upload_button(admin_login):
    client, _ = admin_login

    response = client.get("/admin/upload_admin/admin/upload/")

    # Assert the presence of the string "Upload a file"
    assert response.status_code == 200
    assert b"Upload a file" in response.data


def test_all_fields_have_been_filled_out(admin_login):
    client, _ = admin_login

    response = client.post(
        "/admin/upload_admin/admin/upload/",
        data={},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Please fill out both" in response.data


def test_valid_course_name(admin_login, setup_course_and_exercise_data):
    client, _ = admin_login
    course, exercise = setup_course_and_exercise_data

    response = client.post(
        "/admin/upload_admin/admin/upload/",
        data={
            "course": "Wrong course name",
            "exercise": exercise.number,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Selected course does not exist." in response.data


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
