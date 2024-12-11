from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv
import time
import re
import json
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB in bytes

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@app.route('/api/send-emails', methods=['POST'])
def send_emails():
    try:
        # Get form data
        emails = json.loads(request.form['emails'])
        subject = request.form['subject']
        content = request.form['content']
        
        # Handle file attachment
        attachment_file = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file.filename:
                # Check file size
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > MAX_FILE_SIZE:
                    return jsonify({
                        'message': 'File size exceeds 25MB limit',
                        'status': 'error'
                    }), 400
                
                attachment_file = file

        # Remove duplicates while preserving order
        emails = list(dict.fromkeys([email.strip() for email in emails if email.strip()]))
        
        print(f"Processing {len(emails)} unique emails:", emails)
        
        # Validate emails
        valid_emails = [email for email in emails if is_valid_email(email)]
        invalid_emails = [email for email in emails if not is_valid_email(email)]
        
        if not valid_emails:
            return jsonify({
                'message': 'No valid email addresses provided',
                'status': 'error'
            }), 400

        successful_sends = 0
        failed_sends = 0
        error_messages = []

        try:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            server.login(SENDER_EMAIL, SENDER_PASSWORD)

            for email in valid_emails:
                try:
                    msg = MIMEMultipart()
                    msg['From'] = SENDER_EMAIL
                    msg['To'] = email
                    msg['Subject'] = subject

                    # Attach text content
                    msg.attach(MIMEText(content, 'plain'))

                    # Attach file if present
                    if attachment_file:
                        attachment_file.seek(0)
                        part = MIMEApplication(
                            attachment_file.read(),
                            Name=attachment_file.filename
                        )
                        part['Content-Disposition'] = f'attachment; filename="{attachment_file.filename}"'
                        msg.attach(part)

                    server.send_message(msg)
                    successful_sends += 1
                    
                except Exception as e:
                    failed_sends += 1
                    error_msg = f"Failed to send to {email}: {str(e)}"
                    error_messages.append(error_msg)
                    print(error_msg)
                
                time.sleep(0.1)

            server.quit()
            print("SMTP connection closed")

        except Exception as smtp_error:
            print(f"SMTP Error: {str(smtp_error)}")
            return jsonify({
                'message': f'SMTP Error: {str(smtp_error)}',
                'status': 'error'
            }), 500

        result_message = (
            f'Successfully sent to {successful_sends} recipients. '
            f'Failed: {failed_sends}. '
            f'Invalid emails: {len(invalid_emails)}'
        )

        return jsonify({
            'message': result_message,
            'successful_sends': successful_sends,
            'failed_sends': failed_sends,
            'invalid_emails': invalid_emails,
            'error_messages': error_messages,
            'status': 'success' if successful_sends > 0 else 'partial_failure'
        })

    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({
            'message': str(e),
            'status': 'error'
        }), 500

@app.route('/api/update-credentials', methods=['POST'])
def update_credentials():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({
                'message': 'Email and password are required',
                'status': 'error'
            }), 400

        # Update .env file
        env_path = Path('.env')
        env_content = f"""SENDER_EMAIL={email}
SENDER_PASSWORD={password}"""
        
        env_path.write_text(env_content)
        
        # Reload environment variables
        load_dotenv(override=True)
        
        return jsonify({
            'message': 'Credentials updated successfully',
            'status': 'success'
        })

    except Exception as e:
        print(f"Error updating credentials: {str(e)}")
        return jsonify({
            'message': str(e),
            'status': 'error'
        }), 500

@app.route('/api/get-sender-email', methods=['GET'])
def get_sender_email():
    try:
        return jsonify({
            'email': os.getenv('SENDER_EMAIL'),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'message': str(e),
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)