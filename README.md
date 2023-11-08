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

Create a SQLAlchemy instance:
```
db = SQLAlchemy()
```

Configure the database connection URI (Uniform Resource Identifier) for SQLAlchemy
```
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
```

Links SQLAlchemy with Flask
```
db.init_app(app)
```


# Create the admin page
Import Admin
```
from flask_admin import Admin
```

Create Admin page instance
```
admin = Admin()
```

Links the Admin instance with Flask
```
db.init_app(app)
```

In order to personalize the default page, create in the folder "templates" the subfolder "admin" where to store the admin page "index.html". Then, to modify it, extend the base page provided by the admin package folder and put all the code between a block body:
```
{% extends 'admin/master.html' %}

{% block body %}

...

{% endblock %}
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

Create the actual DB from the flask shell typing into the terminal:
```
flask shell
db.create_all()
exit()
```