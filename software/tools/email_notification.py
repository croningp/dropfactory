import os
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

import json

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

CREDENTIALS_FILE = os.path.join(HERE_PATH, 'email_credentials.json')

def read_json_file(filename):
    with open(filename) as f:
        return json.load(f)


def send_email_notification(toaddr, subject, body):

    credentials = read_json_file(CREDENTIALS_FILE)
    fromaddr = credentials['user']
    password = credentials['password']

    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, password)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
