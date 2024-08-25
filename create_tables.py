import os
import random
import shutil
import subprocess
import sys

from app import create_app
from app.extensions import db
from app.models import Course, Exercise, Role, User
from faker import Faker
from flask_security import SQLAlchemyUserDatastore, hash_password

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
fake = Faker()
N_TEACHERS = 10
N_STUDENTS = 50
ROLES = [
    "administrator",
    "student",
    "teacher",
]

COURSES = ["C#", "C++", "PHP", "Python", "Java", "JavaScript"]


def main():
    app = create_app()
    with app.app_context():
        delete_folders()
        setup_database()
        create_roles()
        exercises = create_sample_exercises()
        populate_tables(COURSES, exercises)
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
            # Include only every 3rd possible exercise
            if random.randint(1, 3) == 1:
                exercises.add(f"{main}.{i}")
    return list(exercises)


def populate_tables(courses, exercises):
    random.seed(22)

    course_map = {}

    for course_name in courses:
        course = Course(
            name=course_name,
        )
        db.session.add(course)
        course_map[course_name] = course

    # Finalize course entries, so the objects get a course_id
    db.session.commit()

    for exr_number in exercises:
        # Hide one out of 5 exercises
        visible = random.randint(1, 5) > 1
        for course_name in courses:
            # Include only every 4th combination
            if random.randint(1, 4) == 1:
                exercise = Exercise(
                    number=exr_number,
                    course_id=course_map[course_name].course_id,
                    flag_visible=visible,
                )

                os.makedirs(f"uploads/{course_name}", exist_ok=True)
                exr_path = os.path.join(course_name, exercise.number)

                exercise.exercise_path = f"{exr_path}.txt"

                with open(f"uploads/{exercise.exercise_path}", "w") as file:
                    file.write(f"This is the exercise {exercise.number}")

                db.session.add(exercise)

    db.session.commit()


def create_users():
    app = create_app()
    random.seed(151)
    with app.app_context():
        print("Creating teachers users")

        # Fetch the "teacher" role from the database
        teacher_role = Role.query.filter_by(name="teacher").first()
        for _ in range(N_TEACHERS):
            new_user = User(
                username=fake.name(),
                password=hash_password("12345678"),
                active=True,
            )
            db.session.add(new_user)

            # Assign the "teacher" role to the new user
            new_user.roles.append(teacher_role)

            # Teachers do not initially have an assigned course.
            print(".", end="")
            sys.stdout.flush()
        print()

        print("Creating students")

        # Fetch a list of courses from the database
        courses = Course.query.all()

        for _ in range(N_STUDENTS):
            new_user = User(
                username=fake.name(),
                password=hash_password("12345678"),
                active=True,
            )
            db.session.add(new_user)

            # Assign the "student" role to the new user
            student_role = Role.query.filter_by(name="student").first()
            new_user.roles.append(student_role)

            # Randomly assign 1 to 3 courses to the new user
            assigned_courses = random.sample(courses, k=random.randint(1, 4))
            new_user.courses.extend(assigned_courses)

            # Indicate progress
            print(".", end="")
            sys.stdout.flush()
        print()

        db.session.commit()


if __name__ == "__main__":
    main()
