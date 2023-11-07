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
python -m flask --app <project_name> run --debug
```

# Install the environmental variables
```
export FLASK_ENV=development
export FLASK_APP=project.py
```

# Create a template folder
It will store the html template pages