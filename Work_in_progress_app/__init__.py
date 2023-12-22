# # Basic flask imports 
# from flask import Flask, flash, redirect, render_template, url_for

# # Imports for Flask security
# from flask_security import (
#     current_user,
#     hash_password,
#     lookup_identity,
#     LoginForm,
#     RegisterForm,
#     Security,
#     SQLAlchemyUserDatastore,
#     uia_username_mapper,
#     unique_identity_attribute,
# )

# # Imports for Flask login
# from flask_login import LoginManager


# from flask_migrate import Migrate

# # Imports for Admin page
# from flask_admin import Admin, helpers as admin_helpers
# from flask_admin.contrib.sqla import ModelView

# from werkzeug.local import LocalProxy

# # Imports for WTF
# from wtforms import BooleanField, StringField, PasswordField, SelectField, SubmitField
# from wtforms.validators import InputRequired, Length, ValidationError, EqualTo


# # Imports from otehr files
# from models import db, Users, Roles
# from errors import register_error_handlers
# from views.customers import customers


# from config import Config

# def create_app(config_class=Config):
#     app = Flask(__name__)
#     app.config.from_object(config_class)
    
#     # Initialize Flask extensions here
#     admin = Admin(
#     app, name="Admin", base_template="master.html", template_mode="bootstrap3"
#     )
#     db.init_app(app)
#     migrate = Migrate(app, db)


#     def username_validator(form, field):
#         # Side-effect - field.data is updated to normalized value.
#         # Use proxy to we can declare this prior to initializing Security.
#         _security = LocalProxy(lambda: app.extensions["security"])
#         msg, field.data = _security._username_util.validate(field.data)
#         if msg:
#             raise ValidationError(msg)


#     class ExtendedRegisterForm(RegisterForm):
#         email = StringField(
#             "Username", [InputRequired(), username_validator, unique_identity_attribute]
#         )
#         password = PasswordField("Password", [InputRequired(), Length(min=8, max=20)])
#         device = StringField("Device")
#         active = BooleanField("Active")
#         role = SelectField(
#             "Role",
#             choices=[
#                 ("customer"),
#                 ("administrator"),
#                 ("sales"),
#                 ("production"),
#                 ("application"),
#                 ("software"),
#             ],
#             validators=[InputRequired()],
#         )


#     class ExtendedLoginForm(LoginForm):
#         email = StringField("Username", [InputRequired()])

#         def validate(self, **kwargs):
#             self.user = lookup_identity(self.email.data)
#             # Setting 'ifield' informs the default login form validation
#             # handler that the identity has already been confirmed.
#             self.ifield = self.email
#             if not super().validate(**kwargs):
#                 return False
#             return True


#     # Allow registration with email, but login only with username
#     app.config["SECURITY_USER_IDENTITY_ATTRIBUTES"] = [
#         {"username": {"mapper": uia_username_mapper}}
#     ]


#     @app.route("/admin/users/new/", methods=["GET", "POST"])
#     def register():
#         form = ExtendedRegisterForm()

#         if form.validate_on_submit():
#             new_user = Users(
#                 username=form.email.data,
#                 password=hash_password(form.password.data),
#                 device=form.device.data,
#                 active=form.active.data,
#             )

#             # Fetch the selected role name from the form
#             selected_role_name = form.role.data

#             # Query the role based on the selected role name
#             existing_role = Roles.query.filter_by(name=selected_role_name).first()

#             if existing_role:
#                 user_datastore.add_role_to_user(new_user, existing_role)
#                 new_user.roles.append(existing_role)
#                 # Add the new user to the database
#                 db.session.add(new_user)
#                 db.session.commit()
#                 return redirect(
#                     url_for("admin.index", _external=True, _scheme="http") + "users/"
#                 )
#             else:
#                 # Handle case where the selected role doesn't exist
#                 flash(f"Role '{selected_role_name}' does not exist.", "error")
#                 return render_template("security/register_user.html", form=form)

#         return render_template("security/register_user.html", form=form)


#     user_datastore = SQLAlchemyUserDatastore(db, Users, Roles)
#     security = Security(
#         app,
#         user_datastore,
#         register_form=ExtendedRegisterForm,
#         login_form=ExtendedLoginForm,
#     )


#     @security.register_context_processor
#     def security_register_processor():
#         return dict(
#             user_datastore=user_datastore,
#             roles=Roles.query.all(),
#             register_user_form=ExtendedRegisterForm(),
#         )


#     @app.before_request
#     def create_user():
#         existing_user = user_datastore.find_user(username="admin")
#         if not existing_user:
#             first_user = user_datastore.create_user(username="admin", password="12345678")
#             user_datastore.activate_user(first_user)
#             db.session.commit()

#             # Assign the 'administrator' role to the 'admin' user
#             admin_role = Roles.query.filter_by(name="administrator").first()
#             user_datastore.add_role_to_user(first_user, admin_role)
#             db.session.commit()


#     class UserAdminView(ModelView):
#         column_list = ("username", "device", "active", "roles")
#         column_sortable_list = (
#             "username",
#             "device",
#             "active",
#             ("roles", "roles.name"), # Make 'roles' sortable
#         )  

#         def is_accessible(self):
#             return (
#                 current_user.is_active
#                 and current_user.is_authenticated
#                 and any(role.name == "administrator" for role in current_user.roles)
#             )
            
#         def _handle_view(self, name):
#             if not self.is_accessible():
#                 return redirect(url_for("security.login"))

#         @staticmethod
#         def _display_roles(view, context, model, name):
#             return ", ".join([role.name.capitalize() for role in model.roles])

#         column_formatters = {"roles": _display_roles}


#     admin.add_view(UserAdminView(Users, db.session))


#     @security.context_processor
#     def security_context_processor():
#         return dict(
#             admin_base_template=admin.base_template,
#             admin_view=admin.index_view,
#             h=admin_helpers,
#             get_url=url_for,
#         )


#     # Flask_login stuff
#     login_manager = LoginManager()
#     login_manager.login_view = "login"


#     @login_manager.user_loader
#     def load_user(user_id):
#         return Users.query.get(user_id)
    
#     # Register blueprints here
#     app.register_blueprint(customers)
#     register_error_handlers(app)
    
#     return app