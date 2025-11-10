from crewai.tools import tool
from typing import Optional
import os, ssl, re, smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
import re
from myapp.AI.Agents.automation_agent2.src.automation.log_in import email, password  

def user_login(email: str = email, password: str = password):
    user_email= email
    user_password = password
    return user_email, user_password

@dataclass
class EmailConfig:
    email: str
    password: str
    smtp_server: str
    smtp_port: int
    use_tls: bool = True



def select_email_config_by_user_email(email: str, password: str) -> EmailConfig:
    domain = email.split('@')[-1].lower()
    smtp_map = {
        "gmail.com": "smtp.gmail.com",
        "outlook.com": "smtp-mail.outlook.com",
        "hotmail.com": "smtp-mail.outlook.com",
        "yahoo.com": "smtp.mail.yahoo.com",
        "zoho.com": "smtp.zoho.com",
        "icloud.com": "smtp.mail.me.com"
    }
    if domain not in smtp_map:
        raise ValueError(f"Unsupported email domain: {domain}")
    return EmailConfig(email, password, smtp_map[domain], 465, True)


def clean_markdown(text: str) -> str:
    """
    Removes common Markdown syntax like **, #, *, and inline links.
    """
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # bold
    text = re.sub(r'__([^_]+)__', r'\1', text)    # underline
    text = re.sub(r'[*_]{1,2}', '', text)         # *, _, **, __
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # headers
    text = re.sub(r'^[-=]+\n', '', text, flags=re.MULTILINE)  # hr
    text = re.sub(r'^\s*[*-]\s+', '  - ', text, flags=re.MULTILINE)  # bullets
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1 [\2]', text)  # [text](url) → text [url]
    return text.strip()


def get_email_subject(query, report_content=None, fallback_message=None):
    subject_match = re.search(r"subject\s+'([^']+)'", query)
    
    if subject_match:
        sub = subject_match.group(1)
    elif report_content:
        sub = report_content.strip().split('\n', 1)[0][:120]
    elif fallback_message:
        sub = fallback_message.strip().split('\n', 1)[0][:120]
    else:
        sub = "Automated Email"
    sub = re.sub(r'^#+\s*', '', sub).strip()
    return sub

@tool
def send_email_smtp(
    query: str,
    attach_file_path: Optional[str] = None,
    csv_file: Optional[str] = None,
    report_content: Optional[str] = None
) -> str:                   #type: ignore
    """
    Sends an email using SMTP.
    - Supports single or multiple recipients via query
    - Uses CSV for bulk mode if given
    - Auto-generates subject if not provided
    - Attaches file if attach_file_path is given
    """

    user_email, user_password = user_login()
    try:
        config = select_email_config_by_user_email(user_email, user_password)
    except Exception as e:
        return f"SMTP Config Error: {str(e)}"

    emails_in_query = re.findall(
        r'[\w\.-]+@[\w\.-]+',
        query.replace(";", " ").replace(",", " "),
        flags=re.IGNORECASE
    )

    message_match = re.search(
        r"(?:message|send this message|write this message)\s+'([^']+)'",
        query,
        re.IGNORECASE
    )
    fallback_message = message_match.group(1) if message_match else None

    combined_message_parts = []
    if fallback_message:
        combined_message_parts.append(fallback_message.strip())
    if report_content:
        combined_message_parts.append(report_content.strip())

    if not combined_message_parts:
        return "Error: No message content found in query or generated content."

    raw_message = "\n\n".join(combined_message_parts)
    message_body = clean_markdown(raw_message)
    print(f"Message Body: {message_body}")

    def get_subject():
        subject_match = re.search(r"subject\s+'([^']+)'", query, re.IGNORECASE)
        if subject_match:
            return clean_markdown(subject_match.group(1))
        if report_content:
            return clean_markdown(report_content.strip().split('\n', 1)[0][:120])
        if fallback_message:
            return clean_markdown(fallback_message.strip().split('\n', 1)[0][:120])
        return "Automated Email"

    def attach_file_to_msg(msg):
        if attach_file_path:
            if not os.path.exists(attach_file_path):
                raise FileNotFoundError(f"Attachment not found: {attach_file_path}")
            with open(attach_file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attach_file_path)}")
            msg.attach(part)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(config.smtp_server, config.smtp_port, context=context) as server:
            server.login(config.email, config.password)

            # CSV mode first
            if csv_file:
                if not os.path.exists(csv_file):
                    return f"CSV file not found at {csv_file}"

                recipients_df = pd.read_csv(csv_file)
                if 'Emails' not in recipients_df.columns:
                    return "CSV must contain a column named 'Emails'"

                for email in recipients_df['Emails']:
                    msg = MIMEMultipart()
                    msg['From'] = config.email
                    msg['To'] = email
                    msg['Subject'] = get_subject()
                    msg.attach(MIMEText(message_body, 'plain'))
                    attach_file_to_msg(msg)
                    server.sendmail(config.email, email, msg.as_string())

                return f"Email sent to {len(recipients_df)} recipients from CSV."

            # Multi-email from query mode
            if emails_in_query:
                if len(emails_in_query) > 10:
                    for email in emails_in_query:
                        msg = MIMEMultipart()
                        msg['From'] = config.email
                        msg['To'] = email
                        msg['Subject'] = get_subject()
                        msg.attach(MIMEText(message_body, 'plain'))
                        attach_file_to_msg(msg)
                        server.sendmail(config.email, email, msg.as_string())
                    return f"Bulk email sent to {len(emails_in_query)} recipients from query."
                else:
                    for email in emails_in_query:
                        msg = MIMEMultipart()
                        msg['From'] = config.email
                        msg['To'] = email
                        msg['Subject'] = get_subject()
                        msg.attach(MIMEText(message_body, 'plain'))
                        attach_file_to_msg(msg)
                        server.sendmail(config.email, email, msg.as_string())
                    return f"Email sent to {len(emails_in_query)} recipients from query."

    except Exception as e:
        return f"SMTP Send Error: {str(e)}"
