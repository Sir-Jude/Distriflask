from project import app
from models import db, Users, Roles
from flask_security import SQLAlchemyUserDatastore
from faker import Faker

user_datastore = SQLAlchemyUserDatastore(db, Users, Roles)
fake = Faker()
ROLES=[
    "test",
    "test2",
    "customer",
    "administrator",
    "sales",
    "production",
    "application",
    "software",
]

def run():
    with app.app_context():
        Roles.query.delete()        
        print("Deleting all Roles...recreating!")

        for role_name in ROLES:
            new_role = Roles(
                name = role_name,
                description = f"{role_name} role"
            )
            db.session.add(new_role)
            
        db.session.commit()
        
# @app.before_request
# def create_user():
#     with app.app_context():
#         user_datastore = SQLAlchemyUserDatastore(db, Users, Roles)
#         existing_user = user_datastore.find_user(username="admin")
#         if not existing_user:
#             first_user = user_datastore.create_user(username="admin", password="12345678")
#             user_datastore.activate_user(first_user)
#             db.session.commit()

#             # Create the 'administrator' role if it doesn't exist
#             admin_role = Roles.query.filter_by(name="administrator").first()
#             if not admin_role:
#                 admin_role = Roles(name="administrator")
#                 db.session.add(admin_role)
#                 db.session.commit()

#             # Assign the 'administrator' role to the 'admin' user
#             user_datastore.add_role_to_user(first_user, admin_role)
#             db.session.commit()
        
if __name__ == "__main__":
    run()
        