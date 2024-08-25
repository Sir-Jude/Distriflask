from app.extensions import db
from flask_security import RoleMixin, UserMixin, SQLAlchemyUserDatastore
from sqlalchemy import Boolean, Column, event, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
import uuid


class UserRoles(db.Model):
    __tablename__ = "users_roles"
    id = Column(Integer(), primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey("users.user_id"))
    role_id = Column("role_id", Integer(), ForeignKey("roles.role_id"))


class UserCourse(db.Model):
    __tablename__ = "users_courses"
    id = Column(Integer(), primary_key=True)
    user_id = Column(Integer(), ForeignKey("users.user_id"))
    course_id = Column(Integer(), ForeignKey("courses.course_id"))


class User(db.Model, UserMixin):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    password = Column(String(80))
    active = Column(Boolean())
    roles = relationship(
        "Role", secondary="users_roles", back_populates="users", lazy=True
    )
    courses = relationship(
        "Course",
        secondary="users_courses",
        back_populates="users",
        lazy=True,
    )

    fs_uniquifier = Column(
        String(255),
        unique=True,
        nullable=False,
        # Line below necessary to avoid "ValueError: Constraint must have a name"
        name="unique_fs_uniquifier_constraint",
    )

    def numbers(self):
        if self.courses:
            return ", ".join(exercise.number for exercise in self.courses.exercises)
        else:
            return ""

    def __repr__(self):
        return self.username


class Role(db.Model, RoleMixin):
    __tablename__ = "roles"
    role_id = Column(Integer(), primary_key=True)
    name = Column(String(20), unique=True)
    description = Column(String(255))
    users = relationship(
        "User", secondary="users_roles", back_populates="roles", lazy=True
    )

    def __repr__(self):
        return f"{self.name} (role_id={self.role_id})"


class Course(db.Model):
    __tablename__ = "courses"
    course_id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True)
    users = relationship(
        "User", secondary="users_courses", back_populates="courses", lazy=True
    )
    exercises = relationship("Exercise", back_populates="course", lazy=True)

    def __repr__(self):
        return f"{self.name}"


class Exercise(db.Model):
    __tablename__ = "exercises"
    exercise_id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.course_id"))
    number = Column(String(20))  # e.g. 8.0.122
    exercise_path = Column(String(255))
    flag_visible = Column(Boolean())
    course = relationship(
        "Course", back_populates="exercises", uselist=False, lazy=True
    )

    def __repr__(self):
        return f"{self.number}"


# Generate a random fs_uniquifier: users cannot login without it
@event.listens_for(User, "before_insert")
def before_insert_listener(mapper, connection, target):
    if target.fs_uniquifier is None:
        target.fs_uniquifier = str(uuid.uuid4())


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
