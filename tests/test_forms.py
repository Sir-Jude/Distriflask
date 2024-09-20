from app.forms import UploadExerciseForm

def test_username_validator_success(test_form, mock_security):
    mock_security._username_util.validate.return_value = (None, "normalized_username")

    # Validate the form
    assert test_form.validate()  # This should succeed if the validator works

    # Check if the validator updated the field data
    assert test_form.username.data == "normalized_username"

    # Ensure that the validate method was called with the correct argument
    mock_security._username_util.validate.assert_called_with("testuser")

def test_username_validator_failure(test_form, mock_security, username_validation_fixtures):
    username_validator, assert_raises_validation_error = username_validation_fixtures
    mock_security._username_util.validate.return_value = ("Invalid username", None)

    assert_raises_validation_error(username_validator, test_form, test_form.username)

def test_path_exists(setup_course_and_exercise_data):
    # Unpack the fixture to get course and exercise data
    course, exercise = setup_course_and_exercise_data

    # Create an instance of the UploadExerciseForm
    form = UploadExerciseForm()
    
    # Set the courses.data to the name of the test course
    form.courses.data = course.name

    # Call path_exists and check if it returns True
    assert form.path_exists() is True

    # Optionally test with a non-existing course
    form.courses.data = "Non-existent Course"
    assert form.path_exists() is False