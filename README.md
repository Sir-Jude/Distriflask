# Table of Contents
1. [Introduction](#introduction)
2. [Setting up the web application](#setting)  
2.1. [Create a virtual environment](#virtual-env)  
2.2. [Install the packages "*libldap2-dev*" and "*libsasl2-dev*"](#libldap_libsasl)  
2.3. [Install the required libraries](#libraries)  
2.4. [Set up the environmental variables](#variables)  
2.5. [Create and populate the database with some dummy data](#script)  
2.6. [Launch the application](#launching)  
3. [Using the application](#using)  
3.1. [The admin pages](#admin)  
&nbsp;&nbsp;3.1.1. [Login as an admin](#admin_login)   
&nbsp;&nbsp;3.1.2. [The list of Users](#user_list)  
&nbsp;&nbsp;3.1.3. [Create a new User](#user_create)  
&nbsp;&nbsp;3.1.4. [The table of releases and devices](#rel_dev)  
&nbsp;&nbsp;3.1.5. [Upload a file](#upload)  
3.2. [The customer page](#customer)  
&nbsp;&nbsp;3.2.2. [download a release](#download)
4. [Further development](#further)


<a id="introduction"></a>
# 1. Introduction
In VSCode, press on your keyboard Ctrl+"K" and then just "V" to see a preview of this Markdown file.

The app is a prototype of a web application for the distribution of software packages, it is coded in Python and built using the Flask framework. It is a fork of the project I am developing for my internship and, even though it is not finished yet, it already has several functionalities.

For the creation and management of the relational-database, I have used:
- **SQLite**  
  A software library that provides a relational-database management system. Unlike client-server database management systems, SQLite is serverless and self-contained, meaning it doesn't require a separate server process to operate.  
  
  It is widely used in embedded systems, mobile apps, and small to medium-sized applications where a full-fledged client-server database may be excessive.  
  
  It implements a small, fast, self-contained, high-reliability, full-featured, SQL database engine.
- **SQLAlchemy**  
  An open-source SQL toolkit and Object-Relational Mapping (ORM) library for Python. It provides a set of high-level APIs that allow developers to interact with databases using Python objects rather than writing SQL queries directly  
  
  It abstracts away many of the differences between database engines, providing a unified interface for working with different databases.  
  
  It offers a core library for building database applications independent of any ORM, as well as an ORM layer for mapping Python objects to database tables  
  
  Even though I have chosen SQLite, SQLAlchemy supports a wide range of database systems, including MySQL, PostgreSQL, Oracle and Microsoft SQL Server.
- **Flask SQLAlchemy**:  
A Flask extension, which integrates SQLAlchemy into the application.
  
  It provids easy-to-use tools for database integration and builds upon the capabilities of both Flask and SQLAlchemy, allowing developers to create web applications with robust database functionality efficiently. 


The code is split into chunks to improve its readability, debugging and further extensibility.
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
├── s.py
├── README.md
└── requirements.txt
```

These goals are reached also thanks to the implementation of [Flask's Blueprint](https://exploreflask.com/en/latest/blueprints.html) architecture.

The project comes with a create_tables.py script, which creates:
- a new database
- some dummy data, which are then saved into the database
- a folder "devises" containing a subfolder for each device
- some file.txt (representing the company's software packages), which are then saved into the device folders.


<a id="setting"></a>
# 2. Setting up the web application
<a id="virtual-env"></a>
## 2.1. Create a virtual environment
First things first, create a virtual environment
```
python3 -m venv .venv
source .venv/bin/activate
```
**TIP**: in the terminal, type "**deactivate**" to switch off the virtual environment.


<a id="libldap_libsasl"></a>
## 2.2. Install the packages "libldap2-dev" and "libsasl2-dev"
For general web development using Flask, **libldap2-dev** and **libsasl2-dev** might not be essential: Flask itself doesn't directly rely on these libraries for its core functionality.

However, their importance might arise if it's necessary to implement certain features within the Flask application that require interaction with LDAP for user authentication or to integrate SASL for security-related functionalities.

Finally, when testing the installation of the app on other computers, I have often encountered issues without these packages installed. Therefore, I strongly advise you to install them.
```
sudo apt-get install libldap2-dev
sudo apt-get install libsasl2-dev
```

<a id="libraries"></a>  
## 2.3. Install the required libraries
Install the libraries listed inside the **requirements.txt** file:
```
pip install -r requirements.txt

```

<a id="variables"></a>  
## 2.4. Set up the environmental variables
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


<a id="script"></a>  
## 2.5. Create and populate the database with some dummy data
Launch the script to create and populate the database
```
python create_tables.py
```  

<a id="launching"></a>  
## 2.6. Launch the application
In VSCode, open a second terminal (Ctrl + Shift + 5) and launch the app from there with the following command:
```
flask --app app run --debug
```
The "**--debug**" option provides:
- continuous synchronization of the code after every modification, such
  that the application does not need to be restarted after changes to the
  code
- the interactive debugger, which highlights errors in the code

Now, if you have done everything correctly, the following text should appear in your second terminal:

\* Serving Flask app 'app'  
\* Debug mode: on  
<span style="color:red">
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
</span>  
\* Running on http://127.0.0.1:5000  
<span style="color:yellow">
Press CTRL+C to quit  
</span> 
\* Restarting with watchdog (inotify)  
\* Debugger is active!    
\* Debugger PIN: 490-161-154

Finally, click on the following link to launch the application:
```
http://127.0.0.1:5000
```

<a id="using"></a>
# 3. Using the application  
<a id="admin"></a>  
## 3.1. The admin pages
<a id="admin_login"></a>  
### 3.1.1. Login as an admin
Log in as an administrator using the following credentials:
```
Username: admin
Password: 12345678
```
**IMPORTANT**: the script assigns this password to every user, but this is just a prototype and the app is running in a development environment: in case you decide to use this code to deploy the app, it is highly recommended to create a **unique and safer** password for every different user!!!

<a id="user_list"></a>
### 3.1.2. The list of Users
Click on "**Users**" to see the list of Users. They are essentially divided in two main groups:
- the employees hired by the company
- the customers  

In the first, only those who have been assigend the role of "administrator" can see the pages with the list of Users and Devices.  

The difference with the second group is that these Users have bought a device (used as their username) and a software package, which can be downloaded from the website.

<a id="user_create"></a>
### 3.1.3. Create a new User
In the page [Users](#user_list), click on **Create**.

Then, fill the form in and click on "**Register**".  

If you now go back to the list of Users, you will find that its Username has been added to the list. 

<a id="rel_dev"></a>
### 3.1.4. The table of releases and devices
In the page [Users](#user_list), note down a release version and then click on "**Devices**" in the navigation bar.

Independently from which are the numbers used, the default table always shows the lastest available minor releases (X.X.X) of the last major version (X.X).

Now, paste in the form a release number or a device name and click "**Search**"   
- The filter "**Release**", shows a table with the list of all minor releases of the major version, with the column containing the selected one highlighted in red. This allows the admin not only to see how many customers have bought that particular release, but also advise them about the updates which have been released after the version they have bought.
- The filter "**Devices**", shows the list of releases available for that particular instrument.

<a id="upload"></a>
### 3.1.5. Upload a file
Click on "**Upload**": you will be redirected to the form which allows you to select the release to be uploaded and the device it belong to.

The names of the available devices can be taken from the table in the page [Users](#user_list).

In theory, Flask allows the upload of any file, but for demostration purposes, this app restricts the format to "**.txt**" and "**.deb**"

Once you have chosen a device and an appropriate file, click on "**Upload**".  

Now, if you open the folder "**uploads**", which was created when you launched the [script](#script), you will find the file in a folder with the name of the selected device.


<a id="customer"></a>  
## 3.2. The customer page
## 3.2.1. Login as a customer

Login as an admin (if you have not done it yet, please, read how to do it in the previous [chapter](#admin)) and choose from the list of Users the username of a customer account.

Visit the link:
```
http://127.0.0.1:5000/
```

Click on "**Login**" in the navigation bar, use the the chosen username and the password "12345678" as credentials and click on the "**Login**" button at the base of the form.

**IMPORTANT**: the script assigns this password to every user, but this is just a prototype and the app is running in a development environment: in case you decide to use this code to deploy the app, it is highly recommended to create **unique and safer** passwords for every different user!!!

<a id="download"></a>
## 3.2.2. download a release  
From the dropdown menu, select the name of a software version and then click on the "**Download**" button.

The app will now allow you to save and download one of the company's software packages (remember, in this prototype, they are rapresented by some file.txt) on your computer.


<a id="further"></a>
# 4. Further development
The project is still in full development and there is still a lot of work to do, but some features are already in progress:  
- Write Flask-specific unit and functional test functions with pytest
- Improve the front-end and customer experience
- Implement a password recovering feature for the customers
