from app.extensions import db
from flask_security import RoleMixin, UserMixin
from sqlalchemy import event
import uuid

roles_users_table = db.Table(
    "roles_users",
    db.Column("users_id", db.Integer(), db.ForeignKey("users.user_id")),
    db.Column("roles_id", db.Integer(), db.ForeignKey("roles.id")),
)


class Users(db.Model, UserMixin):
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
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


# Generate a random fs_uniquifier
# Without it, users cannot login into admin panel
@event.listens_for(Users, "before_insert")
def before_insert_listener(mapper, connection, target):
    if target.fs_uniquifier is None:
        target.fs_uniquifier = str(uuid.uuid4())
