from project import app
from models import db, Users, Roles
from sqlalchemy import text
from flask_security import SQLAlchemyUserDatastore, hash_password
from random import choice
from faker import Faker

user_datastore = SQLAlchemyUserDatastore(db, Users, Roles)
fake = Faker()
N_USERS=50
ROLES=[
    "administrator",
    "customer",
    "sales",
    "production",
    "application",
    "software",
]

ROLE_CHOICE = [
    "customer",
    "sales",
    "production",
    "application",
    "software",
]

def roles_creation():
    with app.app_context():
        for role_name in ROLES:
            existing_role = Roles.query.filter_by(name=role_name).first()
            if existing_role is None:
                new_role = Roles(
                    name=role_name,
                    description=f"{role_name} role"
                )
                db.session.add(new_role)
                print(f'Role "{new_role.name}" has beeen created')

        db.session.commit()


def first_user():
    with app.app_context():
        user_datastore = SQLAlchemyUserDatastore(db, Users, Roles)
        existing_user = user_datastore.find_user(username="admin")
        if not existing_user:
            first_user = user_datastore.create_user(username="admin", password="12345678")
            user_datastore.activate_user(first_user)
            db.session.commit()
        else:
            first_user = user_datastore.delete_user(existing_user)
            db.session.commit()
            
            first_user = user_datastore.create_user(username="admin", password="12345678")
            user_datastore.activate_user(first_user)
            db.session.commit()
            
            # Create the 'administrator' role if it doesn't exist
            admin_role = Roles.query.filter_by(name="administrator", description="administrator role").first()
            if not admin_role:
                admin_role = Roles(name="administrator", description="administrator role")
                db.session.add(admin_role)
                db.session.commit()

            # Assign the 'administrator' role to the 'admin' user
            admin_role = Roles.query.filter_by(name="administrator").first()
            user_datastore.add_role_to_user(first_user, admin_role)
            db.session.commit()

def dummy_users():
    with app.app_context():
        user_datastore = SQLAlchemyUserDatastore(db, Users, Roles)
        for user in range(N_USERS):
            ROLE=choice(ROLE_CHOICE)
            new_user = user_datastore.create_user(
                username = fake.name(),
                password = hash_password("12345678"),
                device = f"Software {user} - Mod. 1.0",
                active = True,
                roles = [ROLE],
            )
            db.session.add(new_user)
            print(f'User "{new_user.username}" has been created.')
        
        db.session.commit()    

if __name__ == "__main__":
    roles_creation()
    first_user()
    dummy_users()