from flask_security import UsernameUtil
import bleach


class CustomUsernameUtil(UsernameUtil):
    def check_username(self, username):
        # Add your custom username validation logic here
        # For example, allow letters, numbers, and underscores
        if not username or not username.replace(" ", "").isalnum():
            return "Username can only contain letters and numbers"
        return None

    def normalize(self, username):
        # Add your custom username normalization logic here
        # For example, clean and normalize the username using bleach and unicodedata
        return bleach.clean(username, strip=True)

    def validate(self, username):
        # Validate and normalize the username
        error_msg = self.check_username(username)
        if error_msg:
            return error_msg, None
        normalized_username = self.normalize(username)
        return None, normalized_username
