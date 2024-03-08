# Introduction
In VSCode, press on your keyboard Ctrl+"K" and then just "V" to see a preview of this Markdown file.

The app is split into chunks to improve its redability, debugging and further extensibility .
```
.
├── app
|   ├── static
│   │   ├── images
│   │   |    └── your_company.png
|   |   ├── customer_style.css
|   |   ├── ...
|   |
|   ├── templates
│   │   ├── admin
│   │   │   ├── index.html
│   │   │   ├── ...
|   |   |    
│   │   ├── customers
│   │   │   ├── login.html
│   │   │   ├── ...
|   |   |
│   │   ├── errors
│   │   │   ├── 403.html
│   │   │   ├── ...
│   │   │   
│   │   ├── home
│   │   │   ├── home.html
│   │   │   ├── ...
|   |   |
│   │   └── security
│   │       ├── login_user.html
│   │       ├── ...
|   |       
│   ├── views
│   |   ├── admin_pages.py
│   |   ├── ...
|   |   
|   ├── __init__.py
│   ├── errors.py
│   ├── extensions.py
│   ├── forms.py
│   └── models.py
│
├── tests
│   ├── conftest.py
│   ├── __init__.py
│   ├── test_html.py
|   ├── ...
|
├── .env
├── .gitignore
├── config.py
├── create_table.py
├── README.md
└── requirements.txt
```

These goals are reached also thanks to the implementation of [Flask's Blueprint](https://exploreflask.com/en/latest/blueprints.html) architecture.

The project comes with a create_table.py script, which:
- erases any pre-existing database
- sets a new one
- populates it with dummy data


## Create a virtual env
First thing first, create a virtual environment
```
python3 -m venv .venv
source .venv/bin/activate
```
**TIP**: in the terminal, type "*deactivate*" to switch off the virtual environment.


## Installation of requirements
Install the libraries listed inside the **requirements.txt** file:
```
pip install -r requirements.txt

```

## Set the environmental variables
Create a .env file
```
code .env
```
Add the following environmental variables
```
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=Y0ur_cOmpany_Secr3T_K3y_D0_N0t_5har3
SECURITY_PASSWORD_SALT=Sal7_F0r_YoUr_CoMpAnY_PaS5w0rD
SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3
```

The **FLASK_ENV** variable is used to set the Flask environment and determines the behavior of the app: it can have values like "development", "testing" or "production".

The **FLASK_APP** variable is used by Flask to locate the app and it is used as its entry point.

The **SECRET_KEY** is a crucial configuration variable used for security-related purposes, especially for cryptographic functions and session management

The **SECURITY_PASSWORD_SALT** is a variable used in combination with the SECRET_KEY to enhance the security of password hashing, especially when working with user authentication systems.

The **SQLALCHEMY_DATABASE_URI** specifies the name of the database connected to the project while using SQLAlchemy.

# Populate the database with some dummy data
Launch the script to create and populate the database
```
python create_tables.py
```

# Launch the application 
Launch the app
```
flask --app app run --debug
```
The "**--debug**" option provides:
- continuous synchronization of the code after every modification, such
  that the application does not need to be restarted after changes to the
  code
- the interactive debugger, which highlights errors in the code

# Using and exploring the app
In the VSCode terminal, click on
```
http://127.0.0.1:5000
```
(Or type the same address in the address bar of any browser)

Click on **Login** and use the following credentials
```
Username: admin
Password: 123456478
```

To go to the admin page, go to the link:
```
http://127.0.0.1:5000/admin/
```