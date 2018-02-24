# Phonemate-App-Backend
A REST API created using the Flask micro-framework for the smartphone recommender android application "PhoneMate".

## Getting Started

### Prerequisites
* <b>Python - Version v3.5.2</b><br>
    Check if Python 3 is already installed.
    ```bash
    python --version
    ```
    If Python 3 is not already installed, you can install it using the following command <b>(For Debian systems)</b>:
    ```bash
    sudo apt-get install python3=3.5.2*
    ```
    <br>
* <b>Pip - Version v9.0.1</b><br>
    Check if pip is already installed.
    ```bash
    pip --version
    ```
    If not, install it using the follwing command <b>(For Debian systems)</b>:
    ```bash
    sudo apt-get install python3-pip
    ```
    <br>
*  <b>virtualenv - Version v15.1.0</b><br>
    Check if virtualenv is already installed.
    ```bash
    virtualenv --version
    ```
    If not, install it as follows:
    ```bash
    pip install virtualenv
    ```
    <br>
* <b>MongoDB - Version v3.4.13</b><br>
      Instructions to download it are available at the following link:<br>
      MongoDB Community Edition Server: https://docs.mongodb.com/manual/administration/install-community/
      <br>
      
### Installing
* 1. Clone the project and put it in your home folder<br>
     This can be done using the Github Clone or download button or by using the following command:
     ```bash
     git clone https://github.com/vishvanatarajan/Phonemate-App-Backend.git
     ```
* 2. Open the project folder and create a virtual environment.
     ```bash
     cd <your_project_directory> (Phonemate-App-Backend)
     virtualenv venv
     ```
  
* 3. Activate the virtual environment.
     ```bash
     source venv/bin/activate
     ```
     
* 4. Inside the project folder, create a <b>folder</b> called <b>instance</b>.<br>
     Now, create <b>two files</b> inside this folder:
     * 1. __init__.py - To mark this folder as a Python package.
     * 2. <b>config</b>.py - A file that stores project sensitive information such as SECRET-KEY, API keys, etc.<br>
     ```bash
     #Sample contents for instance/config.py
     
     DEBUG = True
     DATABASE_URI = "mongodb://localhost:27017/<database_name>
     DATABASE_NAME = <database_name>
     SECRET_KEY = "your-secret-key-needs-to-be-put-here"
     BCRYPT_LOG_ROUNDS = 14 #can be changed according to requirements, but this is ideal
     DEVELOPER_EMAIL = <give the developer email id>
     DEVELOPER_PASSWORD = <give the password against which this account will be validated>
     ```
  
 * 5. The <b>SECRET_KEY</b> can be generated with the following Python code:
      ```bash
      import os
      os.urandom(24)
      ```
   
 * 6. Open the project folder in the terminal and install the required Python modules using the following command:
       ``` bash
       pip install -r requirements.txt
       ```
 * 7. <b>Final Directory structure</b>
         ```bash
         Phonemate-App-Backend <project_folder>
         ├── instance
         │   ├── config.py
         │   └── __init__.py
         ├── phonemate
         │   ├── __init__.py
         │   ├── models
         │   │   ├── __init__.py
         │   │   ├── tokens.py
         │   │   └── users.py
         │   ├── static
         │   └── views.py
         ├── venv
         ├── requirements.txt
         └── run.py
         ```
         
## Running the Server
  In the project directory, open the terminal and type,
  ```bash
  python run.py
  ```
  Then, start your mongod server, if it is not already started.<br>
  To check status of mongod server in Ubuntu 16.04, type the following command in the terminal:
  ```bash
  sudo systemctl status mongodb
  ```
  In case the server is <b>stopped</b>, start it is using the following command:
  ```bash
  sudo systemctl start mongodb
  ```
  
 ## Built With
  * [Flask](http://flask.pocoo.org/) -  A microframework for Python based on Werkzeug and Jinja 2.
  * [MongoDB](https://www.mongodb.com/) - A Free and Open Source document based NoSQL database.
  * [MongoEngine](http://mongoengine.org/) - A Document-Object Mapper (think ORM, but for document databases) for working with MongoDB from Python.
  * [Flask-Bcrypt](https://flask-bcrypt.readthedocs.io/en/latest/) - A Flask extension that provides bcrypt hashing utilities to securely store password or other sensitive information in the database.
  * [Flask-CORS](http://flask-cors.readthedocs.io/en/latest/) - A Flask extension for handling Cross Origin Resource Sharing (CORS), making cross-origin AJAX possible.
  
  ## Debugging Tips
  * 1. If database errors are encountered, ensure that the <b>DATABASE_URI</b> in the [instance/config.py] is correct.
  * 2. Format of Authorization token to be sent is - <b>"Bearer <JWT_encoded_token>"</b>.<br>
    If this format is not followed, JWT Signature errors will be encountered.
  * 3. Whenever, <b>HTTP request</b> is sent, ensure that it <b>always </b> has a <b>content-type: application/json</b>.<br>
  
  ## Note
  <b> By default, the app is set to run on http://localhost:5000</b><br>
      If you wish to change it to the IP of your machine, go to the <b>run.py</b> file and change its content as follows:
  ```bash
  #run.py
  
  from phonemate import app
  if __name__ == "__main__":
      app.run(host="0.0.0.0", port=5000)
  ```
