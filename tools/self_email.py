import time
import smtplib
from email.mime.multipart import MIMEMultipart
import os
import json


def email_inventory_errors(mfr, body_string):
    email_login_filepath = os.path.abspath(os.pardir) + "\\data\\email_login.txt"
    with open(email_login_filepath, 'r') as text_file:
        email_login = json.load(text_file)
        user_name = email_login['UserName']
        password = email_login['Password']
        email_from = email_login['From']
        email_to = email_login['To']
        msg = MIMEMultipart()
        msg["From"] = email_from
        msg["To"] = email_to
        msg["Subject"] = mfr + " Errors " + time.strftime("%m.%d.%Y")
        msg.preamble = body_string
        server = smtplib.SMTP_SSL(email_login['Server'])
        server.login(user_name, password)
        server.sendmail(email_from, email_to, msg.as_string())
        server.quit()
