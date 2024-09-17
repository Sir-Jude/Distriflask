def test_validate_upload_form_missing_fields(client, app, mock_form):
    """
    Test case where the form is missing course name or exercise number.
    """
    mock_form, validate_form = mock_form  # Unpack the tuple

    # Modify the mock form to simulate missing fields
    mock_form.courses.data = None  # Missing course name
    mock_form.exercise.data = None  # Missing exercise number

    # Push a request context to allow flash messages
    with app.test_request_context():
        result = validate_form(mock_form)
        assert not result


def test_validate_upload_form_non_existent_path(client, app, mock_form):
    """
    Test case where the selected course path does not exist.
    """
    mock_form, validate_form = mock_form  # Unpack the tuple

    # Modify the mock form to simulate a non-existent path
    mock_form.path_exists.return_value = False

    # Push a request context to allow flash messages
    with app.test_request_context():
        result = validate_form(mock_form)
        assert not result


def test_validate_upload_form_invalid_file_format(client, app, mock_form):
    """
    Test case where the file format is invalid.
    """
    mock_form, validate_form = mock_form  # Unpack the tuple

    # Modify the mock form to simulate an invalid file format
    mock_form.allowed_file.return_value = False

    # Push a request context to allow flash messages
    with app.test_request_context():
        result = validate_form(mock_form)
        assert not result


def test_validate_upload_form_success(client, app, mock_form):
    """
    Test case where all fields are valid and the form passes validation.
    """
    mock_form, validate_form = mock_form  # Unpack the tuple

    # Use the mock form as is (default valid setup)

    # Push a request context to allow flash messages
    with app.test_request_context():
        result = validate_form(mock_form)
        assert result is True
