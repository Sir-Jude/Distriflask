from app.extensions import db
from flask_security import RoleMixin, UserMixin, SQLAlchemyUserDatastore
from sqlalchemy import Boolean, Column, event, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, backref
import uuid


class RolesUsers(db.Model):
    __tablename__ = "roles_users"
    id = Column(Integer(), primary_key=True)
    user_id = Column("users_id", Integer(), ForeignKey("users.user_id"))
    role_id = Column("roles_id", Integer(), ForeignKey("roles.role_id"))


class Users(db.Model, UserMixin):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, index=True)
    password = Column(String(80))
    device_id = Column(Integer, ForeignKey("devices.device_id"))
    main_version = Column(String, ForeignKey("releases.main_version"))
    active = Column(Boolean())
    roles = relationship(
        "Roles", secondary="roles_users", backref=backref("users", lazy=True)
    )
    fs_uniquifier = Column(
        String(255),
        unique=True,
        nullable=False,
        # Line below necessary to avoid "ValueError: Constraint must have a name"
        name="unique_fs_uniquifier_constraint",
    )

    devices = relationship("Devices", backref=backref("users", lazy=True))
    releases = relationship("Releases", backref=backref("users", lazy=True))

    def __repr__(self):
        return self.username


class Roles(db.Model, RoleMixin):
    __tablename__ = "roles"
    role_id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))

    def __repr__(self):
        return f"{self.name.capitalize()} (role_id={self.role_id})"


class Devices(db.Model):
    __tablename__ = "devices"
    device_id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True)
    country = Column(String(3), nullable=True)

    def __repr__(self):
        return f"{self.name.capitalize()} (from {self.country})"


class Releases(db.Model):
    __tablename__ = "releases"
    release_id = Column(Integer, primary_key=True)
    main_version = Column(String(20))  # e.g. 8.0.122
    # Foreign key referencing Device table
    device_id = Column(Integer, ForeignKey("devices.device_id"))
    flag_visible = Column(Boolean())

    devices = relationship("Devices", backref=backref("releases", lazy=True))

    def __repr__(self):
        return self.main_version


# Generate a random fs_uniquifier: users cannot login without it
@event.listens_for(Users, "before_insert")
def before_insert_listener(mapper, connection, target):
    if target.fs_uniquifier is None:
        target.fs_uniquifier = str(uuid.uuid4())


user_datastore = SQLAlchemyUserDatastore(db, Users, Roles)
