import random

from app import create_app
from app.extensions import db
from app.models import Users, Roles, Devices, Releases
import subprocess
import shutil
from flask_security import SQLAlchemyUserDatastore, hash_password
from random import choice
from faker import Faker

user_datastore = SQLAlchemyUserDatastore(db, Users, Roles)
fake = Faker()
N_USERS = 50
ROLES = [
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
        input="from app.extensions import db\n" "db.create_all()\n" "exit()\n",
        text=True,
    )

    # Initiating and migrating the database
    subprocess.run(["flask", "db", "init"])
    subprocess.run(["flask", "db", "migrate"])


def roles_creation():
    app = create_app()
    with app.app_context():
        for role_name in ROLES:
            existing_role = Roles.query.filter_by(name=role_name).first()
            if existing_role is None:
                new_role = Roles(name=role_name, description=f"{role_name} role")
                db.session.add(new_role)
                print(f'Role "{new_role.name}" has beeen created')

        db.session.commit()


def create_sample_devices():
    random.seed(42)

    devices = set()

    devices.add("c15")
    devices.add("c24")
    for n in range(200):
        devices.add(f"dev0{random.randint(10,2500):04d}")
    for n in range(20):
        devices.add(f"dev100{random.randint(10,70):02d}")
    return devices


def create_sample_releases():
    random.seed(17)

    releases = set()

    for main, max in [
        ("8.1", 12),
        ("8.0", 125),
        ("7.0", 105),
        ("6.4", 88),
        ("6.1", 220),
    ]:
        for i in range(1, max + 1):
            # Include only every 3rd possible release
            if random.randint(1, 3) == 1:
                releases.add(f"{main}.{i}")
                # Add A (and maybe B and C) variants for some of the releases
                if random.randint(1, 50) == 1:
                    releases.add(f"{main}.{i}A")
                    releases.add(f"{main}.{i}B")
                    releases.add(f"{main}.{i}C")
                elif random.randint(1, 30) == 1:
                    releases.add(f"{main}.{i}A")
                    releases.add(f"{main}.{i}B")
                elif random.randint(1, 10) == 1:
                    releases.add(f"{main}.{i}A")
    return releases


def populate_tables(devices, releases):
    random.seed(22)

    device_map = {}
    for dev_name in devices:
        device = Devices(name=dev_name, country=None)
        db.session.add(device)
        device_map[dev_name] = device

    # Finalize device entries, so the objects get a device_id
    db.session.commit()

    for rel_number in releases:
        # Hide one out of 5 releases
        visible = random.randint(1, 5) > 1
        for dev_name in devices:
            # Include only every 4th combination
            if random.randint(1, 4) == 1:
                release = Releases(
                    main_version=rel_number,
                    device_id=device_map[dev_name].device_id,
                    flag_visible=visible,
                )
                db.session.add(release)


def devices_and_releases():
    app = create_app()
    with app.app_context():
        devices = create_sample_devices()
        releases = create_sample_releases()
        populate_tables(devices, releases)
        db.session.commit()


def dummy_users():
    app = create_app()
    with app.app_context():
        for number in range(N_USERS):
            new_user = Users(
                username=fake.name(),
                password=hash_password("12345678"),
                active=True,
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
    populate_tables(create_sample_devices(), create_sample_releases())
    devices_and_releases()
    dummy_users()
