# Moffat Bay
A capstone software development project for Bellevue University's Software Development degree program.

## Contributors
* Vee Bell
* DeJanae Faison
* Julia Gonzalez
* Jess Monnier
* Professor Sue Sampson

## Getting Set Up
* Clone the repo to your computer if you haven't already, or pull down changes
* In a terminal/command line window, move to your repo folder.
  * In File Explorer, you can right-click the folder and click "Copy as path" in the menu to get the path
  * For me, that looks like:
```
cd "C:\Users\karri\Documents\Coding\csd\moffatbay"
```
* Run the following commands to get into a virtual environment that has the correct Python modules to run Django:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
* In the moffaybaylodge folder, you will find a file named dotenv_example. Rename this to '.env' and change the placeholder portions to match your setup.
  * Here AND IN the database setup script, change the username and password to ones you want to use for your local copy of the database.
  * To get a SECRET_KEY, in the top-level moffatbay folder in your virtual environment, run:
```
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
* Run the database_setup.sql script in MySQL. For me, this looked like running the following command in **MySQL's command line client**:
```
SOURCE C:/Users/karri/Documents/Coding/csd/moffatbay/database_setup.sql;
```
* In your (venv) command prompt, run the following to ensure Django sets up its needed tables in the database:
```
python manage.py makemigrations
python manage.py migrate
```
* With MySQL still running, in your command line that is in your top-level moffatbay folder and your virtual environment (venv), run:
```
python manage.py runserver
```
* In your browser, navigate to: 
```
localhost:8000
```
 * That should get a local version of the site (so far) up and running on your machine.

## Project Brief for Moffat Bay Lodge
The following is copied from the Moffat Bay Project page on the course Blackboard.

### Project 1: Moffat Bay Lodge
They are looking to have you build a website that manages the following:

Customers can view all aspects of the Lodge website without being logged in. To book their vacation (lodge reservation), they must be logged in/registered. In other words, to submit a reservation, prompt users to log in or register for a free account. There are no requirements for payment, but users must “click” a button to confirm their reservation. Once a reservation is confirmed, send the record to the database for insertion. The reservations you save in the database will be used to populate the Reservation Lookup page. All registered users should be saved to a table in the database. This table will be used during the login process to validate their access.

### Project requirements:
Pages, models, operations, and/or functionality:

- Landing page:
  - Simple marketing landing page (use the Internet for inspiration on landing pages).
- About Us page:
  - Static HTML/CSS content related to Moffat Bay Lodge.
  - Include the contact information on the about page
- ~~Contact Us page:~~
  - ~~Static HTML/CSS content related to the Moffat Bay Lodge.~~
- Attractions page:
  - Static HTML/CSS content related to activites available on the island. Hiking, kayaking, whale watching, and scuba diving should be included.
- Registration page:
  - Students can pick the number of fields, but at minimum, there should be fields for email address, first name, last name, telephone, and password.
  - Additional comments:
    - All customers should be assigned a unique customerId.
    - All customers should use their email address as the “username” field and the password should be at least 8 characters in length and include one number, one uppercase and one lowercase letter (hint: use regular expression).
    - Program should check that the username (email) is in standard format, ex. bob@somthing.com.
  Passwords should be hashed and/or encrypted using standard security practices (use the Internet for ideas/code snippets; be sure to cite all external authors).
- Login page:
  - Note: Provide customers with a login form and fields for username (use email address) and password.
  - Logged in customers should be added to the application’s session.
- Lodge reservation (book your vacation) page:
  - Note: You are building a lodge reservation page that allows customers to “book their vacation.” MySQL must be used to save the data.
  - Form selection options: room size, number of guests, and check-in/check-out dates.
  - Additional comments:
    - ~~Room size: double full beds = 120.00 per night, queen = 135.00 per night, double queen beds = 150.00 per night, and king = 160.00 per night.~~ Updated with customer request for 5% room rate increase:
    - Room size: double full beds = 126.00 per night, queen = 141.75 per night, double queen beds = 157.50 per night, and king = 168.00 per night.
- Reservation summary page:
  - Note: Provide customers with a reservation confirmation summary and a button to either cancel or submit the reservation. Submitted reservation must be saved to MySQL. Canceling the reservation should take users back to the hotel reservation page.
- Reservation look up page:
  - Note: Provide customers with a page to look up previous reservation. The page should include a field to search by reservation ID or email address and display a summary of the reservation. List the room size, number of guests, and check-in/check-out dates.