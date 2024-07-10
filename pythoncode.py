# Import necessary modules
from flask import Flask, request, jsonify, render_template
import csv
import os
from twilio.rest import Client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Initialize the Flask application
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Twilio credentials (loaded from .env file)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Email credentials (loaded from .env file)
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Function to validate phone numbers
def is_valid_phone_number(phone_number):
    if not phone_number.startswith('+'):
        phone_number = '+91' + phone_number  # Assume Indian country code if not provided
    return phone_number and phone_number.startswith('+') and len(phone_number) > 10

# Function to send SMS using Twilio
def send_sms(to, body):
    try:
        message = client.messages.create(body=body, from_=TWILIO_PHONE_NUMBER, to=to)
        print(f"SMS sent successfully to {to} with SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send SMS to {to}: {e}")
        return False

# Function to send email using SMTP
def send_email(subject, to_email, student_details, report_title):
    subjects_html = ''.join(f"<tr><th>{subj}</th><td>{marks}</td></tr>" for subj, marks in student_details.items() if subj not in ['Name', 'Total Attendance'])

    html = f"""<html>
<head>
<style>
  table {{
    width: 100%;
    border-collapse: collapse;
  }}
  th, td {{
    padding: 8px;
    text-align: left;
    border-bottom: 1px solid #ddd;
  }}
  th {{
    background-color: #f2f2f2;
  }}
</style>
</head>
<body>
<p>Dear parent,</p>

<p>Here is the {report_title} performance report for {student_details['Name']}:</p>

<table>
  {subjects_html}
</table>

<p>Total current attendance of student - {student_details['Total Attendance']}%</p>

<p>Best regards,<br>Christ University</p>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False

# Route to render the index page
@app.route('/')
def index():
    return render_template('index.html')

# Function to process student data from the CSV file
def process_student_data(csv_reader, headers, report_title):
    fixed_columns = {'Name', 'Parent_Mail', 'Parent_No', 'Total Attendance'}
    students_processed = set()  # Set to keep track of processed students

    for row in csv_reader:
        row_dict = dict(zip(headers, row))
        student_name = row_dict['Name'].strip()
        parent_phone = row_dict['Parent_No'].strip()
        parent_email = row_dict['Parent_Mail'].strip()

        if not student_name or student_name in students_processed:
            continue

        students_processed.add(student_name)

        # Extract student details dynamically
        student_details = {header: row_dict[header] for header in headers if header not in fixed_columns}
        student_details['Name'] = student_name
        student_details['Total Attendance'] = row_dict['Total Attendance']

        # Prepare the subjects list for SMS
        subjects_list = '\n'.join(
            f"- {header}: {marks}" for header, marks in student_details.items() if header not in ['Name', 'Total Attendance']
        )

        sms_message = f"""Dear parent,

Here is the {report_title} performance report for {student_name}:

{subjects_list}

Total current attendance of student - {student_details['Total Attendance']}%

Best regards,
Christ University"""

        # Send SMS
        if is_valid_phone_number(parent_phone):
            if send_sms(parent_phone, sms_message):
                print(f"SMS sent successfully to {parent_phone} for student {student_name}.")
            else:
                print(f"Failed to send SMS to {parent_phone} for student {student_name}.")
        else:
            print(f"Invalid phone number: {parent_phone} for student {student_name}")

        # Send Email
        if send_email(f"Performance Report for {student_name}", parent_email, student_details, report_title):
            print(f"Email sent successfully to {parent_email} for student {student_name}.")
        else:
            print(f"Failed to send email to {parent_email} for student {student_name}.")

# Route to handle file upload
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.csv'):
        csv_data = file.read().decode('utf-8').splitlines()
        csv_reader = csv.reader(csv_data)

        # Read the first row for the title
        report_title_row = next(csv_reader)
        report_title = ' '.join(report_title_row).strip()  # Join list elements into a string and strip

        # Skip the header row
        headers = next(csv_reader)

        # Process student data
        process_student_data(csv_reader, headers, report_title)

        return jsonify({'message': 'Data processed and messages sent successfully'})
    else:
        return jsonify({'error': 'Invalid file format. Please upload a CSV file'}), 400

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
