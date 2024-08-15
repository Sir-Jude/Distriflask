def test_username_validator(test_form, mock_security):
    # Validate the form
    assert test_form.validate()  # This should succeed if the validator works

    # Check if the validator updated the field data
    assert test_form.username.data == "normalized_username"

    # Ensure that the validate method was called with the correct argument
    mock_security._username_util.validate.assert_called_with("testuser")
