from app.extensions import db
from flask_security import RoleMixin, UserMixin, SQLAlchemyUserDatastore
from sqlalchemy import event
import uuid

roles_users_table = db.Table(
    "roles_users",
    db.Column("users_id", db.Integer(), db.ForeignKey("users.user_id")),
    db.Column("roles_id", db.Integer(), db.ForeignKey("roles.role_id")),
)


class Users(db.Model, UserMixin):
    __tablename__ = "users"
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, index=True)
    password = db.Column(db.String(80))
    device = db.Column(db.String(200), nullable=True)
    active = db.Column(db.Boolean())
    roles = db.relationship(
        "Roles", secondary=roles_users_table, backref="users", lazy=True
    )
    fs_uniquifier = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        name="unique_fs_uniquifier_constraint",
    )


class Roles(db.Model, RoleMixin):
    """The role of a user.

    E.g. customer, administrator, sales.

    """
    
    __tablename__ = "roles"
    
    role_id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"Role(role_id={self.role_id}, name={self.name}"


class Device(db.Model):
    """A device, like JPK01234 or C15."""

    __tablename__ = "devices"

    device_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    country = db.Column(db.String(3), nullable=True)

    def __repr__(self):
        return f"Device(device_id={self.device_id}, name={self.name}"
    

class Release(db.Model):
    __tablename__ = "releases"

    release_id = db.Column(db.Integer, primary_key=True)
    main_version = db.Column(db.String(20))  # e.g. 8.0.122
    device_id = db.Column(db.Integer)
    flag_visible = db.Column(db.Boolean())

    def __repr__(self):
        return f"Release(release_id={self.id}, name={self.name}"


# Generate a random fs_uniquifier
# Without it, users cannot login into admin panel
@event.listens_for(Users, "before_insert")
def before_insert_listener(mapper, connection, target):
    if target.fs_uniquifier is None:
        target.fs_uniquifier = str(uuid.uuid4())


user_datastore = SQLAlchemyUserDatastore(db, Users, Roles)
