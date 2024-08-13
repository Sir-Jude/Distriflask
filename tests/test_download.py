def select_course(client, course_name):
    """
    Helper function to simulate selecting a course.
    """
    response = client.post(
        "/admin/download_admin/admin/download/",
        data={"select": True, "course": course_name},
        follow_redirects=True,
    )
    return response


def test_selecting_a_course(admin_login, setup_course_and_exercise_data):
    client = admin_login
    course_name, _ = setup_course_and_exercise_data

    # Simulate selecting a course using the helper function
    response = select_course(client, course_name)

    # Access the session directly
    with client.session_transaction() as sess:
        selected_course = sess.get("selected_course")

    assert response.status_code == 200
    assert selected_course == course_name
    assert b"Course Test Course selected." in response.data


def test_file_downloaded(admin_login, setup_course_and_exercise_data):
    """
    Test if the file is correctly downloaded and the content is accurate.
    """
    client = admin_login
    course_name, exercise_file_path = setup_course_and_exercise_data

    # Simulate selecting a course using the helper function
    select_course(client, course_name)

    # Access the download page and submit the form to download the exercise
    response = client.post(
        "/admin/download_admin/admin/download/",
        data=dict(submit="download", course=course_name, exercise="1.0.1"),
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify the file download header
    assert "attachment" in response.headers["Content-Disposition"]

    # Verify the content of the file
    downloaded_content = response.data.decode("utf-8")
    with open(exercise_file_path, "r") as f:
        expected_content = f.read()

    assert downloaded_content == expected_content
