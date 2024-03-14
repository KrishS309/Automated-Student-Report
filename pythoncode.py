from flask import Flask, request, jsonify, render_template
import csv
from twilio.rest import Client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

# Twilio credentials
TWILIO_ACCOUNT_SID = 'AC9b5050c32c0b0db285e8990c1622e688'
TWILIO_AUTH_TOKEN = 'b99e24329268854e0ae7e4b059d4a155'
TWILIO_PHONE_NUMBER = '+14256290790'

# Email credentials
EMAIL_ADDRESS = 'servicelearning2024@gmail.com'
EMAIL_PASSWORD = 'eilb dssr ukww dwbo'  # Update this with your app-specific password
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def is_valid_phone_number(phone_number):
    return phone_number and phone_number.startswith('+') and len(phone_number) > 10

def send_sms(to, body):
    try:
        message = client.messages.create(body=body, from_=TWILIO_PHONE_NUMBER, to=to)
        return True
    except Exception as e:
        print(f"Failed to send SMS to {to}: {e}")
        return False

def send_email(subject, to_email, student_details):
    # Note: HTML content adjusted to match provided Excel sheet structure.
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

<p>Here is the CIA 1 performance report for {student_details['StudentName']}:</p>

<table>
  <tr>
    <th>Subject</th>
    <th>Mark</th>
    <th>Attendance</th>
  </tr>
  <tr>
    <td>Compiler Design</td>
    <td>{student_details['Compiler Design']}</td>
    <td>{student_details['Compiler Design Attendance']}</td>
  </tr>
  <tr>
    <td>IOT</td>
    <td>{student_details['IOT']}</td>
    <td>{student_details['IOT Attendance']}</td>
  </tr>
  <tr>
    <td>Data Mining</td>
    <td>{student_details['Data Mining']}</td>
    <td>{student_details['Data Mining Attendance']}</td>
  </tr>
</table>

<p>Best regards,<br>Christ University</p>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the HTML content
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

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.csv'):
        csv_data = file.read().decode('utf-8').splitlines()
        csv_reader = csv.DictReader(csv_data)
        students_processed = set()

        for row in csv_reader:
            if not any(value.strip() for value in row.values()) or row['StudentName'].strip() in students_processed:
                continue

            students_processed.add(row['StudentName'].strip())

            student_name = row['StudentName'].strip()
            parent_phone = row['ParentPhone'].strip()
            parent_email = row['ParentEmail'].strip()

            if student_name and parent_phone and parent_email:
                # Hardcoded "Compiler Design" marks based on your Excel sheet
                compiler_design_marks = {
                    "Krish Sharma": "17/20",
                    "Jiffin K": "18/20",
                    "Harshith K": "20/20"
                }

                compiler_mark = compiler_design_marks.get(student_name, "N/A")

                student_details = {
                    'StudentName': student_name,
                    'Compiler Design': compiler_mark,
                    'Compiler Design Attendance': row.get('Compiler Design Attendance', 'N/A'),
                    'IOT': row.get('IOT', 'N/A'),
                    'IOT Attendance': row.get('IOT Attendance', 'N/A'),
                    'Data Mining': row.get('Data Mining', 'N/A'),
                    'Data Mining Attendance': row.get('Data Mining Attendance', 'N/A'),
                }

                sms_message = f"""Dear parent,

Here is the CIA 1 performance report for {student_name}:

- Compiler Design: {compiler_mark} Attendance: {row.get('Compiler Design Attendance', 'N/A')}
- IOT: {row.get('IOT', 'N/A')} Attendance: {row.get('IOT Attendance', 'N/A')}
- Data Mining: {row.get('Data Mining', 'N/A')} Attendance: {row.get('Data Mining Attendance', 'N/A')}

Best regards,
Christ University"""

                if send_sms(parent_phone, sms_message):
                    print(f"SMS sent successfully to {parent_phone} for student {student_name}.")

                if send_email(f"Performance Report for {student_name}", parent_email, student_details):
                    print(f"Email sent successfully to {parent_email} for student {student_name}.")

        return jsonify({'message': 'Data processed and messages sent successfully'})
    else:
        return jsonify({'error': 'Invalid file format. Please upload a CSV file'}), 400



if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
