import os
import pycountry
import random
import shutil
import subprocess
import sys

from app import create_app
from app.extensions import db
from app.models import Country, Course, Exercise, Role, User
from faker import Faker
from flask_security import SQLAlchemyUserDatastore, hash_password

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
fake = Faker()
N_USERS = 15
ROLES = [
    "administrator",
    "student",
    "teacher",
]

countries = list(pycountry.countries)
COUNTRIES = [
    {"short_name": country.alpha_3, "long_name": country.name} for country in countries
]


def main():
    app = create_app()
    with app.app_context():
        delete_folders()
        setup_database()
        create_roles()
        create_countries()
        courses = create_sample_courses()
        exercises = create_sample_exercises()
        populate_tables(courses, exercises)
        create_users()
        db.session.commit()


def delete_folders():
    folders_to_delete = ["instance", "migrations", "uploads"]
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


def create_roles(app=None):
    if app is None:
        app = create_app()
    with app.app_context():
        for role_name in ROLES:
            existing_role = Role.query.filter_by(name=role_name).first()
            roles = Role.query.all()
            if existing_role is None:
                new_role = Role(name=role_name, description=f"{role_name} role")
                db.session.add(new_role)
                print(f'Role "{new_role.name}" has been created')

        db.session.commit()


def create_countries():
    app = create_app()
    with app.app_context():
        for country_name in COUNTRIES:
            existing_country = Country.query.filter_by(
                name=country_name["long_name"]
            ).first()
            if existing_country is None:
                new_country = Country(name=country_name["long_name"])
                db.session.add(new_country)

        db.session.commit()


def create_sample_courses():
    random.seed(42)

    courses = set()

    for n in range(100):
        courses.add(f"crs0{random.randint(10,2500):04d}")
    for n in range(10):
        courses.add(f"crs100{random.randint(10,70):02d}")

    return list(courses)


def create_sample_exercises():
    random.seed(17)

    exercises = set()

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
                exercises.add(f"{main}.{i}")
                # Add A (and maybe B and C) variants for some of the exercises
                if random.randint(1, 50) == 1:
                    exercises.add(f"{main}.{i}A")
                    exercises.add(f"{main}.{i}B")
                    exercises.add(f"{main}.{i}C")
                elif random.randint(1, 30) == 1:
                    exercises.add(f"{main}.{i}A")
                    exercises.add(f"{main}.{i}B")
                elif random.randint(1, 10) == 1:
                    exercises.add(f"{main}.{i}A")
    return list(exercises)


def populate_tables(courses, exercises):
    random.seed(22)

    course_map = {}
    countries = Country.query.all()

    for dev_name in courses:
        country = random.choice(countries)
        course = Course(
            name=dev_name,
            country_id=country.country_id,
        )
        db.session.add(course)
        course_map[dev_name] = course

    # Finalize course entries, so the objects get a course_id
    db.session.commit()

    for rel_number in exercises:
        # Hide one out of 5 exercises
        visible = random.randint(1, 5) > 1
        for dev_name in courses:
            # Include only every 4th combination
            if random.randint(1, 4) == 1:
                release = Exercise(
                    version=rel_number,
                    course_id=course_map[dev_name].course_id,
                    flag_visible=visible,
                )

                os.makedirs(f"uploads/{dev_name}", exist_ok=True)
                rel_path = os.path.join(dev_name, release.version)

                release.exercise_path = f"{rel_path}.txt"

                with open(f"uploads/{release.exercise_path}", "w") as file:
                    file.write(f"This is the exercise {release.version}")

                db.session.add(release)

    db.session.commit()


def create_users():
    app = create_app()
    random.seed(151)
    with app.app_context():
        print("Creating teachers users")
        # Fetch the "teacher" role from the database
        teacher_role = Role.query.filter_by(name="teacher").first()
        for _ in range(N_USERS):
            new_user = User(
                username=fake.name(),
                password=hash_password("12345678"),
                active=True,
            )
            db.session.add(new_user)

            # Assign the "teacher" role to the new user
            new_user.roles.append(teacher_role)

            # Teacher users do not initially have am assigned course.
            new_user.course_id = None

            # Indicate progress
            print(".", end="")
            sys.stdout.flush()
        print()

        print("Creating students")
        COURSES = create_sample_courses()
        for course_name in COURSES:
            new_user = User(
                username=course_name,
                password=hash_password("12345678"),
                active=True,
            )
            db.session.add(new_user)

            new_role = Role.query.filter_by(name="student").first()
            new_user.roles.append(new_role)

            new_user.course_name = new_user.username

            # Indicate progress
            print(".", end="")
            sys.stdout.flush()
        print()

        db.session.commit()


if __name__ == "__main__":
    main()
