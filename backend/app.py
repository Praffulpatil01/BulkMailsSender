from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv
import time
import json
import re

# Load environment variables
load_dotenv()

app = FastAPI(title="Bulk Email Sender")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://InboxWave.netlify.app",
        "https://bulkmailssender.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB in bytes

def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

@app.post("/api/send-emails")
async def send_emails(
    emails: str = Form(...),
    subject: str = Form(...),
    content: str = Form(...),
    attachment: Optional[UploadFile] = File(None)
):
    try:
        email_list = json.loads(emails)
        
        # Remove duplicates and validate emails
        unique_emails = list(dict.fromkeys([email.strip() for email in email_list if email.strip()]))
        valid_emails = [email for email in unique_emails if is_valid_email(email)]
        invalid_emails = [email for email in unique_emails if not is_valid_email(email)]

        if not valid_emails:
            raise HTTPException(status_code=400, detail="No valid email addresses provided")

        # Check attachment size
        if attachment:
            content = await attachment.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail="File size exceeds 25MB limit")
            await attachment.seek(0)

        successful_sends = 0
        failed_sends = 0
        error_messages = []

        # Send emails
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)

            for email in valid_emails:
                try:
                    msg = MIMEMultipart()
                    msg['From'] = SENDER_EMAIL
                    msg['To'] = email
                    msg['Subject'] = subject

                    # Add text content
                    msg.attach(MIMEText(content, 'plain'))

                    # Add attachment if present
                    if attachment:
                        file_content = await attachment.read()
                        part = MIMEApplication(file_content, Name=attachment.filename)
                        part['Content-Disposition'] = f'attachment; filename="{attachment.filename}"'
                        msg.attach(part)
                        await attachment.seek(0)

                    server.send_message(msg)
                    successful_sends += 1
                    time.sleep(0.1)  # Rate limiting

                except Exception as e:
                    failed_sends += 1
                    error_messages.append(f"Failed to send to {email}: {str(e)}")

        return JSONResponse({
            "message": f"Successfully sent to {successful_sends} recipients. Failed: {failed_sends}. Invalid emails: {len(invalid_emails)}",
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "invalid_emails": invalid_emails,
            "error_messages": error_messages,
            "status": "success" if successful_sends > 0 else "partial_failure"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-credentials")
async def update_credentials(email: str = Form(...), password: str = Form(...)):
    try:
        env_content = f"""SENDER_EMAIL={email}
SENDER_PASSWORD={password}"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        # Reload environment variables
        load_dotenv(override=True)
        
        return {"message": "Credentials updated successfully", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get-sender-email")
async def get_sender_email():
    try:
        return {"email": os.getenv('SENDER_EMAIL'), "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)