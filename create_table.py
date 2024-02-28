import pycountry
import random
import shutil
import subprocess
import sys
from random import choice

from app import create_app
from app.extensions import db
from app.models import Device, Release, Role, User
from faker import Faker
from flask_security import SQLAlchemyUserDatastore, hash_password

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
fake = Faker()
N_USERS = 15
ROLES = [
    "administrator",
    "customer",
    "sales",
    "production",
    "application",
    "software",
]
COUNTRIES = [country.alpha_3 for country in pycountry.countries]


def main():
    app = create_app()
    with app.app_context():
        delete_folders()
        setup_database()
        create_roles()
        devices = create_sample_devices()
        releases = create_sample_releases()
        populate_tables(devices, releases)
        create_users()
        db.session.commit()


def delete_folders():
    folders_to_delete = ["instance", "migrations"]
    for folder in folders_to_delete:
        try:
            shutil.rmtree(folder)
            print(f"Folder '{folder}' deleted.")
        except FileNotFoundError:
            print(f"Folder '{folder}' not found.")


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


def create_roles():
    app = create_app()
    with app.app_context():
        for role_name in ROLES:
            existing_role = Role.query.filter_by(name=role_name).first()
            if existing_role is None:
                new_role = Role(name=role_name, description=f"{role_name} role")
                db.session.add(new_role)
                print(f'Role "{new_role.name}" has beeen created')

        db.session.commit()


def create_sample_devices():
    random.seed(42)

    devices = set()

    for n in range(200):
        devices.add(f"Dev_0{random.randint(10,2500):04d}")
    for n in range(20):
        devices.add(f"Dev_100{random.randint(10,70):02d}")

    return list(devices)


def create_sample_releases():
    random.seed(17)

    releases = set()

    for main, max in [
        ("3.1", 12),
        ("3.0", 125),
        ("2.0", 105),
        ("1.4", 88),
        ("1.1", 220),
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
    return list(releases)


def populate_tables(devices, releases):
    random.seed(22)

    device_map = {}
    for dev_name in devices:
        device = Device(name=dev_name, country_id=random.choice(COUNTRIES))
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
                release = Release(
                    version=rel_number,
                    device_id=device_map[dev_name].device_id,
                    flag_visible=visible,
                )
                db.session.add(release)

    db.session.commit()


def create_users():
    app = create_app()
    random.seed(151)
    with app.app_context():
        print("Creating in-house users")
        for _ in range(N_USERS):
            new_user = User(
                username=fake.name(),
                password=hash_password("12345678"),
                active=True,
            )
            db.session.add(new_user)

            # Give the new user up to 4 roles:
            roles = set()
            for _ in range(random.randint(1, 4)):
                roles.add(choice(ROLES))
            for role_name in roles:
                new_role = Role.query.filter_by(name=role_name).first()
                new_user.roles.append(new_role)

            # Named (= in-house) users do not have devices.
            # We can create users like 'dev01234' if we want to simulate
            # customer user accounts.
            new_user.device_id = None

            # Indicate porgress
            print(".", end="")
            sys.stdout.flush()
        print()

        print("Creating customers")
        DEVICES = create_sample_devices()
        used_device_names = set()
        for _ in range(N_USERS):
            # Generate a unique username based on device names
            device_name = choice(DEVICES)
            while device_name in used_device_names:
                device_name = choice(DEVICES)
            used_device_names.add(device_name)

            new_user = User(
                username=device_name,
                password=hash_password("12345678"),
                active=True,
            )
            db.session.add(new_user)

            new_role = Role.query.filter_by(name="customer").first()
            new_user.roles.append(new_role)

            new_user.device_name = new_user.username

            # Indicate progress
            print(".", end="")
            sys.stdout.flush()
        print()

        db.session.commit()


if __name__ == "__main__":
    main()
