from app.extensions import db
from app.models import User, Role
from flask_security import hash_password

def test_create_button(admin_login):
    client, _ = admin_login

    response = client.get(
        "/admin/user/new/?url=/admin/user/",
    )

    assert response.status_code == 200
    assert "Save and Add Another" in response.text

# def test_register_new_user(admin_login):
#     client, _ =admin_login
    
#     response = client.get(
#         "/admin/user/new/?url=/admin/user/",
#     )
    
#     with client:
#         new_user = User(
#             username="test_user",
#             password=hash_password("12345678"),
#             roles=[Role.query.filter_by(name="student").first()],
#             active=True,
#         )

#         db.session.add(new_user)
#         db.session.commit()
    
#     user = User.query.filter_by(username=new_user.username)
    
#     assert user == new_user
    
