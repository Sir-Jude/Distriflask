# Create a virtual env
```
python3 -m venv .venv
source .venv/bin/activate
```


# Installation of the requirements
```
sudo apt-get install libldap2-dev
sudo apt-get install libsasl2-dev
sudo yum install cyrus-sasl-devel
pip install -r requirements.txt
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


# Create a User model and link it to the admin page
# TO BE REVIEW AND REWRITTEN!!!
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

To make implementing a user class easier, you can inherit from UserMixin, which provides default implementations for all of these properties and methods. (It’s not required, though.)

```
class User(db.Model, UserMixin):
    __tablename__ = "user"
    user_id = db.Column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4, unique=True
    )
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
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
admin.add_view(ModelView(User, db.session))
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

Using SQLite, to check whether the tables have been created, run the command
```
sqlite3 <relative_path_to_the_database_file>
# for example 
# sqlite3 instance/db.sqlite3
.tables
.exit
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
**DO NOT FORGET**: in case a model is modiefied, for example the "User", you need to update also:
- the register form
- the reigster route
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
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Username"},
    )
    password = PasswordField(
        validators=[InputRequired(), Length(min=8, max=20)],
        render_kw={"placeholder": "Password"},
    )
    submit = SubmitField("Register")
    
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                "This username already exists. Please choose a different one."
            )

``` 
Inside the folder "templates", create the subfolder "registration" containing the regiser.html file. It will extend the base.html file. 
```
{% extends 'base.html' %}
{% block title %}
<title>Register</title>
{% endblock %}
{% block content %}
<p>
    Register nere:
</p>
<form method="POST" action="">
    {{ form.csrf_token }}
    {{ form.hidden_tag() }}
    {{ form.username }}
    {{ form.password }}
    {{ form.submit }}

    <button class="btn btn-primary" type="submit">Login</button>
</form>
{% endblock %}
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
    return User.query.get(user_id)
```