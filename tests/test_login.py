class TestStudent:
    def test_student_login(self, student_user):
        client, student_username, student_password = student_user
        response = client.post(
            "/student_login",
            data=dict(username=student_username, password=student_password),
            follow_redirects=True,
        )

        # Check if request was successful
        assert response.status_code == 200
        
        # Check if the content includes the username
        assert (
            f"<h3>{student_username.title()}'s profile.</h3>".encode() in response.data
        )

        # Check if the content includes the flash message
        assert b"Logged in successfully." in response.data

        # Also assert that the final location URL is correct
        assert response.request.path == f"/student/{student_username}/"

    def test_student_logout(self, student_user):
        client = student_user[0]
        response = client.get("/logout", follow_redirects=True)

        assert response.status_code == 200
        assert b"Welcome to Your Company!" in response.data
        assert response.request.path == "/"


class TestAdmin:
    def test_correct_admin_login_from_student_endpoint(self, admin_user):
        client, admin_username, admin_password, admin_roles = admin_user

        response = client.post(
            "/student_login",
            data=dict(
                username=admin_username, password=admin_password, roles=admin_roles
            ),
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert f"<h2>Welcome, {admin_username.title()}!</h2>".encode() in response.data
        assert response.request.path == "/admin/"

    def test_correct_admin_login_correctly_from_admin_endpoint(self, admin_user):
        client, admin_username, admin_password, admin_roles = admin_user

        response = client.post(
            "/login",
            data=dict(
                username=admin_username,
                password=admin_password,
            ),
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert f"<h2>Welcome, {admin_username.title()}!</h2>".encode() in response.data
        assert response.request.path == "/admin/"

    def test_admin_logout(self, admin_user):
        client = admin_user[0]
        response = client.get("/logout", follow_redirects=True)

        assert response.status_code == 200
        assert b"Welcome to Your Company!" in response.data
        assert response.request.path == "/"

class TestWrongLogin:    
    def test_wrong_username_from_student_endpoint(self, admin_user):
        client, admin_username, admin_password, admin_roles = admin_user
        
        response = client.post(
            "/student_login",
            data=dict(
                username="Wrong username", password=admin_password, roles=admin_roles
            ),
            follow_redirects=True,
        )
        
        assert response.status_code == 200
        assert b"Invalid username." in response.data
        assert response.request.path == "/student_login"

    def test_wrong_student_password(self, student_user):
        client, student_username, student_password = student_user
        response = client.post(
            "/student_login",
            data=dict(username=student_username, password="Wrong password"),
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Wrong password - Try Again..." in response.data
        assert response.request.path == "/student_login"

    def test_wrong_admin_password_from_admin_endpoint(self, admin_user):
        client, admin_username, admin_password, admin_roles = admin_user
        
        response = client.post(
            "/login",
            data=dict(
                username=admin_username, password="wrong password", roles=admin_roles
            ),
            follow_redirects=True,
        )
        
        assert response.status_code == 200
        assert b"Invalid password" in response.data
        assert response.request.path == "/login"