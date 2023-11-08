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


# Create the .env file and import the libraries to use it
Import the libraries
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

Sets a configuration variable for the Flask application and store it in the .emv file
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


# Install the environmental variables
```
export FLASK_ENV=development
export FLASK_APP=project.py
```


# Create a **templates** folder
It will store the html template pages


# Initiate the database
Import SQLAlchemy
```
from flask_sqlalchemy import SQLAlchemy
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

# Create a Login feature
Import the libraries
```
from flask_login import LoginManager
```
Create an instance of the login_manager class and link it the login to the app
```
login_manager = LoginManager(app)
```



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
