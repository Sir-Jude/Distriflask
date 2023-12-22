from app import app
from models import db, Users, Roles
import subprocess
import shutil
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


# Function to delete folders
def delete_folders():
    folders_to_delete = ["instance", "migrations"]
    for folder in folders_to_delete:
        try:
            shutil.rmtree(folder)
            print(f"Folder '{folder}' deleted.")
        except FileNotFoundError:
            print(f"Folder '{folder}' not found.")

# Function to perform database setup tasks
def setup_database():
    
    # Log into the shell and execute commands
    subprocess.run(
        ["flask", "shell"],
        input="from models import db\n" "db.create_all()\n" "exit()\n",
        text=True
    )
    
    # Initiating and migrating the database
    subprocess.run(["flask", "db", "init"])
    subprocess.run(["flask", "db", "migrate"])


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
        

def dummy_users():
    with app.app_context():
        for number in range(N_USERS):
            new_user = Users(
                username = fake.name(),
                password = hash_password("12345678"),
                device = f"Software {number} - Mod. 1.0",
                active = True,
            )
            db.session.add(new_user)
            
            role_name = choice(ROLES)
            new_role = Roles.query.filter_by(name=role_name).first()
            new_user.roles.append(new_role)
            
            print(f'User "{new_user.username}" has been created.')
        
        db.session.commit()    

if __name__ == "__main__":
    delete_folders()
    setup_database()
    roles_creation()
    dummy_users()
