# Moffat Bay
A capstone software development project for Bellevue University's Software Development degree program.

## Contributors
* Vee Bell
* DeJanae Faison
* Julia Gonzalez
* Jess Monnier
* Professor Sue Sampson

## Getting Set Up
* Clone the repo to your computer
* In a terminal/command line window, move to your repo folder.
  * For me, that looks like:
```
cd "C:\Users\karri\Documents\Coding\csd\moffatbay"
```
  * In File Explorer, you can right-click the folder and click "Copy as path" in the menu to get the path
* Run the following commands:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
  * This will get you into a virtual environment that has the correct Python modules to run Django
* In the moffaybaylodge folder, you will find a file named dotenv_example. Rename this to '.env' and change the placeholder portions to match your setup.
  * To get a SECRET_KEY, in the top-level moffatbay folder in your virtual environment, run:
```
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
  * Here AND IN the database setup script, change the username and password to ones you want to use for your database.
* Run the database_setup.sql script in MySQL. For me, this looked like running the following command in **MySQL's command line client**:
```
SOURCE C:/Users/karri/Documents/Coding/csd/moffatbay/database_setup.sql;
```
* With MySQL still running, in your command line that is in your top-level moffatbay folder and your virtual environment (venv), run:
```
python manage.py runserver
```
* In your browser, navigate to: 
```
localhost:8000
```
 * That's the website! Well, what we have of it so far.