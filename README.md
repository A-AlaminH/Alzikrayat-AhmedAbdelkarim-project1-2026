# Alzikrayat by Ahned Abdelkarim

## Project Name

Alzikrayat Photo Sharing Application

## Description

Alzikrayat is a small website where users can create an account, share photos, view others photos, and leave comments.

## Technologies

- **web server**: Python and Flask 
- **Database**: MySQL for storing users, photos, and comments
- PyMySQL for running handwritten SQL queries
- HTML, Bootstrap, CSS, and a small amount of JavaScript for the pages

Flask receives requests, while the app's own regex router chooses the action for each URL. The project does not use an ORM.

## How to Run

1. Install Python and MySQL Server.
2. Open PowerShell in this project folder.
3. Create the database once:

   ```powershell
   mysql -u root -p -e "source schema.sql"
   ```

4. Create a virtual environment and install the packages:

   ```powershell
   py -m venv --clear .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

5. Set your MySQL password for this PowerShell session:

   ```powershell
   $env:DB_PASSWORD = 'your MySQL root password'
   ```

6. Start the app:

   ```powershell
   .\.venv\Scripts\python.exe app.py
   ```

7. Open http://127.0.0.1:5000 in a browser.



## Student Name

Ahmed Abdelkarim
