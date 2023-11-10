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


# .env file and import the libraries to use it
Create a .env file
```
code .env
```
Add the following environmental variables
```
SECRET_KEY = <a_secure_secret_key>
export FLASK_ENV=development
export FLASK_APP=project.py
```
Whitout these, we would have to stop the server and restart it everytime we made some modifications in our code to let them take effect.

Finally, in the main project file, import the libraries which allows to use it
```
import os
from dotenv import load_dotenv
```



# Create the project.py file and import the libraries to use flask
Import the libraries
```
from flask import Flask, render_template
```

Initialize a Flask application instance
```
app = Flask(__name__)
```

Sets a configuration variable for the Flask application
```
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
```


# Run the development server in debug mode
Add the "--debug" option to enable the debug mode.

This allows:
 - the continuous synchronization of the code without having to restart it
 - the error visualization  
**IMPORTANT**: Remember to remove the debug mode when the project will be deployed.

```
flask run --debug
```


# Create a **templates** folder
It will store the html template pages


# Create a User model and link it to the admin page
Import the libraries to use the UUID (Universally Unique Identifier)
```
from sqlalchemy.dialects.postgresql import UUID
import uuid
```

Create the model view
```
class User(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(50))
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
Create a SQLAlchemy instance and link to the app:
```
db = SQLAlchemy(app)
```

Configure the database connection URI (Uniform Resource Identifier) for SQLAlchemy
```
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
```

Create the actual DB from the flask shell typing into the terminal:
```
flask shell
db.create_all()
exit()
```
Run the command
```
flask db init
```

Whenever we modify a model, run the following command:
```
flask db migrate -m "short description..."
flask db upgrade
```


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


# Create a registration form and its relative register webpage 
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