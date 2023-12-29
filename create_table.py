#! /usr/bin/env python3

"""Create and populate a dummy table in SQLAlchemy"""

# Live Hacks:
#
# * Setup
#
#   export FLASK_ENV=development FLASK_APP=project.py
#   export SECRET_KEY=a_secure_secret_key SECURITY_PASSWORD_SALT=a_secure_salt_key
#   sudo apt install python3-venv libldap2-dev libsasl2-dev sqlite3-pcre
#   python3 -m venv .venv
#   source .venv/bin/activate
#   python3 -mpip install --no-user -r requirements.txt
#
#
# * Interact with the data base
#
#   $ source .venv/bin/activate
#
# ** Dump content of database
#   $ sqlite3 instance/project.db .dump
#   or maybe even
#   $ sqlite3_analyzer instance/project.db
#
# ** Command-line tool
#   $ sudo apt install litecli sqlite3-tools
#   # Or, if this version throws the error
#   #   AttributeError: module 'click' has no attribute 'get_terminal_size'
#   # Download litecli_1.10.0-1_all.deb and install that.
#
#   $ litecli instance/project.db
#   -- Make REGEXP available:
#   litecli>  .load /usr/lib/sqlite3/pcre.so
#
#   litecli>  .tables  -- show tables
#   litecli>  help     -- show all commands
#   litecli>  select * from users
#   litecli>  select * from releases, devices \
#                 where releases.device_id = devices.device_id \
#                 order by main_version, name


import random

from flask import Flask
from flask_security import RoleMixin, SQLAlchemyUserDatastore, UserMixin
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"

db = SQLAlchemy()
db.init_app(app)


roles_users_table = db.Table(
    "roles_users",
    db.Column("users_id", db.Integer, db.ForeignKey("users.user_id")),
    db.Column("roles_id", db.Integer, db.ForeignKey("roles.role_id")),
)


class User(db.Model, UserMixin):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, index=True)
    password = db.Column(db.String(80))
    device = db.Column(db.String(200), nullable=True)
    active = db.Column(db.Boolean)
    roles = db.relationship(
        "Role", secondary=roles_users_table, backref="users", lazy=True
    )
    fs_uniquifier = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        name="unique_fs_uniquifier_constraint",
    )


class Role(db.Model, RoleMixin):
    """The role of a user.

    E.g. customer, administrator, sales.

    """

    __tablename__ = "roles"

    role_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"Role(role_id={self.role_id}, name={self.name}"


class Device(db.Model):
    """A device, like dev01234 or C15."""

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


def main():
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    with app.app_context():
        db.drop_all()  # Needed?
        db.create_all()

        first_user = user_datastore.create_user(username="admin", password="12345678")
        user_datastore.activate_user(first_user)
        # db.session.commit()

        devices = create_sample_devices()
        releases = create_sample_releases()
        populate_tables(devices, releases)
        db.session.commit()


def populate_tables(devices, releases):
    random.seed(22)

    device_map = {}
    for dev_name in devices:
        device = Device(name=dev_name, country=None)
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
                    main_version=rel_number,
                    device_id=device_map[dev_name].device_id,
                    flag_visible=visible,
                )
                db.session.add(release)


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


if __name__ == "__main__":
    main()
