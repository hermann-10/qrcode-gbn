QRify - QR Code-Based Attendance System


QRify is a Django-based QR code attendance tracking system for employees. Each employee is assigned a unique UUID and QR code, which is used to mark their attendance by scanning. The system includes admin login, employee registration, QR code scanning, and rich analytics and reporting features.

🚀 How to Run the App
1. Clone the repository
bash
Copy
Edit
git clone https://github.com/yourusername/qrify.git
cd qrify

2. Install dependencies
Make sure you have Python and Django installed. Then run:

bash
Copy
Edit
pip install -r requirements.txt

3. Run the server
bash
Copy
Edit
python manage.py runserver
Open your browser and go to:
👉 http://127.0.0.1:8000/

🔐 Admin Access Setup
Before logging in to the system, you need to create a superuser (admin):

bash
Copy
Edit
python manage.py createsuperuser
Provide a username, email, and password when prompted.

Now navigate to the admin login page:
👉 http://127.0.0.1:8000/login

Use the superuser credentials to log in.

👤 Features for Admin
📌 Staff Container
Register New Employees: Add employees with details like name, department, and generate their QR code.

View & Filter Employees: Easily search and filter by departments or names.

QR Code Scanner: Scan employee QR codes using a connected scanner or manually enter the UUID in the text field. Scanning logs attendance automatically.

📊 Analytics Container
Only accessible by the admin.

1. General Analytics
Overview of attendance trends over time.

Visual charts (daily, weekly, monthly trends).

2. Department Analytics
View department-wise presence statistics.

Analyze most/least active departments.

3. Employee Analytics
Select an employee and date range.

View daily, weekly, and monthly scan data.

Export attendance report as Excel.

Presence status marked as:

IP (If Present)

WH (Work from Home / Absent)


📦 Technologies Used
Python (Django Framework)

HTML5, CSS3, JavaScript

Chart.js / 3D chart libraries

Excel export via pandas and openpyxl

UUID-based QR Code system

📄 License
This project is licensed under the MIT License.
created by : Anothjeev Arunthavarajah  GBN Intern 

