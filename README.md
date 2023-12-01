# To search something accross the files (including the .venv)
```
rg -u. <whatever>
```

# Create a virtual env
```
python3 -m venv .venv
source .venv/bin/activate
```
Type "deactivate " to go out of the virtual environment.


# Installation of the requirements
```
sudo apt-get install libldap2-dev
sudo apt-get install libsasl2-dev
pip install -r requirements.txt
```
To update requirements file, type this:
```
pip freeze > requirements.txt
```


# Create the .gitignore file
```
.env
.venv
venv
__pycache__
*.pyc
*.sqlite3
request.http
.python-version
```


# Set the environmental variables
Create a .env file
```
code .env
```
Add the following environmental variables
```
SECRET_KEY = <a_secure_secret_key>
FLASK_ENV=development
FLASK_APP=project.py
```

The **SECRET_KEY** is a crucial configuration variable used for security-related purposes, especially for cryptographic functions and session management

The **FLASK_ENV** variable is used to set the Flask environment and determines the behavior of the app: it can have values like "development", "testing" or "production".

The **FLASK_APP** variable is used by Flask to locate the app and it is used as its entry point.

Finally, in the main project file, import the libraries which allows to use the .env file
```
import os
from dotenv import load_dotenv
```


# Create the project.py file and set it up to use Flask
Import the libraries
```
from flask import Flask, flash, render_template, redirect, url_for
```

Initialize a Flask application instance
```
app = Flask(__name__)
```

Link the SECRET_KEY to the project through the .env file 
```
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
```


# Start the Flask application in debug mode
```
flask run --debug
```
The "--debug" option provide:
- the continuous synchronization of the code after every modification, so that the application has not to be retart to be updated
- the interactive debugger, which highlights the errors in the code



# Create a "*templates*" folder
It will store the files with the code for the html pages


# Create a route to a web page and its logic
The **@app.route** decorator is extensivily used in Flask to bind a URL path to a function. Additionally, by using the methods argument, it specifies the permissible HTTP request methods that the associated function will respond to.
```
@app.route("/logout/", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
```

Finally, render one of the html file kept in the *templates* folder
```
return render_template("registration/login.html", context=object)
```

Or redirect the user to a specific route, identifed by the name of its associatd function:
```
return redirect(url_for("login"))
```

# TO BE REVIEW AND REWRITTEN!!!
Main source for Users and Roles model design:
(https://ckraczkowsky.medium.com/building-a-secure-admin-interface-with-flask-admin-and-flask-security-13ae81faa05)

UPDATE_1: Flask security library is deprecated  
--> pip install flask_security_too
UPDATE_2: before_first_request is deprecated
--> use before_request (https://github.com/pallets/flask/issues/4605)



# Create a User model and link it to the admin page
Import the UserMixin and the libraries to use the UUID (Universally Unique Identifier)
```
from flask_login import UserMixin
from sqlalchemy_utild import UUIDType
import uuid
```

Create the model view.
It needs to implement the following properties and methods:  

*is_authenticated*  
    This property should return True if the user is authenticated, i.e. they have provided valid credentials. (Only authenticated users will fulfill the criteria of login_required.)

*is_active*  
    This property should return True if this is an active user - in addition to being authenticated, they also have activated their account, not been suspended, or any condition your application has for rejecting an account. Inactive accounts may not log in (without being forced of course).

*get_id()*  
    This method must return a str that uniquely identifies this user, and can be used to load the user from the user_loader callback. Note that this must be a str - if the ID is natively an int or some other type, you will need to convert it to str.

```
class Users(db.Model, UserMixin):
    __tablename__ = "user"
    user_id = db.Column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4, unique=True
    )
    username = db.Column(db.String(20), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    device = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute!")

    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "admin"
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True

    def get_id(self):
        return str(self.user_id)
```

Import the libraries to create a "view" for SQLAlchemy models in Flask-Admin
```
from flask_admin.contrib.sqla import ModelView
```

Add a new view for the Use model to the admin interface
```
admin.add_view(ModelView(Users, db.session))
```


# Initiate the database
Import SQLAlchemy and Migrate
```
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
```

Configure the parameter which specifies the **URI** (**U**niform **R**esource **I**dentifier) used to connect to a database. In this case, SQLAlchemy (an open-source SQL toolkit and Object-Relational Mapping (ORM) library for Python) use the URI to establish a connection with a SQLite database called *db.sqlite3*
```
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
```

Create a SQLAlchemy instance and link to the app:
```
db = SQLAlchemy(app)
```

Initialize the **Flask-Migrate** extension, which provides a set of commands to handle database migrations: Flask-Migrate helps manage changes in the structure of your database over time, allowing you to easily create and apply migrations when you modify your database schema or models.
It takes as parameters the Flask application app and db instances set earlier.
```
migrate = Migrate(app, db)
```

From the terminal, launch the flask shell...
```
flask shell
```



...and create the actual DB typing the following commands:
```
from project import db
db.create_all()
exit()
```
**Important**: *db.create_all()* creates the tables for all the models that have been defined in the application, but if new models are added later, the command needs to be run again. 

To check whether the tables have been created, run the command (SQLite only)
```
sqlite3 <relative_path_to_the_database_file>
# for example 
# sqlite3 instance/db.sqlite3
.tables
.exit
``` 
To see the structure of the table (SQLite only)
```
PRAGMA table_info(table_name);
```


Set up the migrations directory structure with the necessary files for managing future migrations. This step is necessary only the first time you set up Flask-Migrate in a project.
```
flask db init
flask db migrate
```

**IMPORTANT**: whenever a model is modified or a new one is created, the following commands must to run in order to migrate the new changes into the database and upgrade its structure.
```
flask db migrate -m "short description..."
flask db upgrade
```
**DO NOT FORGET**: in case a model is modiefied, for example the "Users", you need to update also:
- the register form
- the register route
- the http template


# Create the admin page
Import Admin
```
from flask_admin import Admin
```

Create Admin page instance and link it to the app
```
admin = Admin(app)
```

In order to personalize the default page, create in the folder "templates" the subfolder "admin" where to store the admin page "index.html". Then, to modify it, extend the base page provided by the admin package folder and put all the code between a block body:
```
{% extends 'admin/master.html' %}

{% block body %}

...

{% endblock %}
```


# Create a registration form and its relative html webpage 
Import the relevant libraries
```
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
```

Add to the .env file a "SECRET_KEY" variable: all modern web forms works with a **CSRF** (**C**ross-**S**ite **R**equest **F**orgery) token which create a secret key which sync up behind the scenes with our secret_key and make sure a hacker has not hijacked the form itself    
```
SECRET_KEY = a_secure_secret_key
```
Then link it to the app
```
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
```
Create a a registration form
```
class RegisterForm(FlaskForm):
    username = StringField(
        validators=[
            InputRequired(),
            Length(min=4, max=20),
        ],
        render_kw={"placeholder": "Username"},
    )
    password = PasswordField(
        validators=[
            InputRequired(),
            Length(min=8, max=20),
            EqualTo("password_2", message="Passwords must match!"),
        ],
        render_kw={"placeholder": "Password"},
    )
    password_2 = PasswordField(
        validators=[InputRequired()],
        render_kw={"placeholder": "Confirm Password"},
    )

    device = StringField(
        render_kw={"placeholder": "Device"},
    )

    role = SelectField(
        choices=[("user", "User"), ("admin", "Admin")],
        validators=[
            InputRequired(),
        ],
        render_kw={"placeholder": "Role"},
    )
    submit = SubmitField("Register", render_kw={"class": "btn btn-primary"})

    def validate_username(self, field):
        field.data = field.data.lower()

        existing_user_username = Users.query.filter_by(username=field.data).first()
        if existing_user_username:
            raise ValidationError(
                "This username already exists. Please choose a different one."
            )

``` 
Inside the folder "templates", create the subfolder "registration" containing the fiel **regiser.html**:
```
<!DOCTYPE html>
<html>
  <head>
    <title>Admin - Register</title>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="" />
    <meta name="author" content="" />

    <link
      href="/admin/static/bootstrap/bootstrap2/swatch/default/bootstrap.min.css?v=2.3.2"
      rel="stylesheet"
    />
    <link
      href="/admin/static/bootstrap/bootstrap2/css/bootstrap-responsive.css?v=2.3.2"
      rel="stylesheet"
    />
    <link
      href="/admin/static/admin/css/bootstrap2/admin.css?v=1.1.1"
      rel="stylesheet"
    />

    <style>
      body {
        padding-top: 4px;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="navbar">
        <div class="navbar-inner">
          <a class="brand" href="/admin">Admin</a>
          <ul class="nav">
            <li class="active">
              <a href="/admin/">Home</a>
            </li>
            <li>
              <a href="/admin/users/">Users</a>
            </li>
          </ul>
          <ul class="nav pull-right"></ul>
        </div>
      </div>
      <p>Register here:</p>
      <form method="POST" action="{{ url_for('register') }}">
        {{ form.csrf_token }}
        {{ form.hidden_tag() }}
    
        {{ form.username() }}
        <br/>
        {% for error in form.username.errors %}
            <p class="error">{{ error }}</p>
        {% endfor %}
    
        {{ form.password() }}
        <br/>
        {% for error in form.password.errors %}
            <p class="error">{{ error }}</p>
        {% endfor %}
    
        {{ form.password_2() }}
        <br/>
    
        {{ form.device() }}
        <br/>
    
        {{ form.role() }}
        <br/>
    
        {{ form.submit() }}
    </form>
    </div>
    <script
      src="/admin/static/vendor/jquery.min.js?v=3.5.1"
      type="text/javascript"
    ></script>
    <script
      src="/admin/static/bootstrap/bootstrap2/js/bootstrap.min.js?v=2.3.2"
      type="text/javascript"
    ></script>
    <script
      src="/admin/static/vendor/moment.min.js?v=2.22.2"
      type="text/javascript"
    ></script>
    <script
      src="/admin/static/vendor/select2/select2.min.js?v=3.5.2"
      type="text/javascript"
    ></script>
  </body>
</html>
```
Create its relative route and function:
```
@app.route("/register/", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    return render_template("registration/register.html", form=form)
```



Finally, link the register function to the navbar
```
<li class="nav-item">
  <a class="nav-link" href="{{ url_for('register') }}">Register</a>
```


# Create a Login feature
Import the libraries
```
from flask_login import LoginManager
```
Create an instance of the login_manager class and link it the login to the app
```
login_manager = LoginManager(app)
```
Now, you need to provide *user_loader callback*: this is a function that Flask-Login uses to reload the user object from the user ID stored in the session. It should take the str ID of a user, and return the corresponding user object. 

```
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)
```



# How to overwrite the form...
https://flask-security-too.readthedocs.io/en/stable/customizing.html

https://flask-security-too.readthedocs.io/en/stable/configuration.html#SECURITY_USER_IDENTITY_ATTRIBUTES

https://stackoverflow.com/questions/30827696/flask-security-login-via-username-and-not-email

https://github.com/Flask-Middleware/flask-security/issues/466

https://www.google.com/search?q=%22Flask+Security+too%22+%22SECURITY_USER_IDENTITY_ATTRIBUTES%22&sca_esv=586607062&sxsrf=AM9HkKkJD5bjQxKvGsvu3LOrabDnDcwJ2w%3A1701362547996&ei=c7toZd2vPKGL9u8P3byCwAY&ved=0ahUKEwidtbqyleyCAxWhhf0HHV2eAGgQ4dUDCBA&uact=5&oq=%22Flask+Security+too%22+%22SECURITY_USER_IDENTITY_ATTRIBUTES%22&gs_lp=Egxnd3Mtd2l6LXNlcnAiOCJGbGFzayBTZWN1cml0eSB0b28iICJTRUNVUklUWV9VU0VSX0lERU5USVRZX0FUVFJJQlVURVMiSABQAFgAcAB4AJABAJgBAKABAKoBALgBA8gBAPgBAeIDBBgAIEE&sclient=gws-wiz-serp