'''
alarm.py

This module sends an alarm to the user
'''
import os
import smtplib

try:
    from email.MIMEMultipart import MIMEMultipart
except ImportError:
    from email.mime.multipart import MIMEMultipart
    
from email.mime.text import MIMEText

def _get_server_port_pair(account_type="gmail"):
    if account_type == "gmail":
        return "smtp.gmail.com", 587

def _initialize_smtp_server(server, host):
    mail_server = smtplib.SMTP(server, host)
    mail_server.ehlo()
    mail_server.starttls()
    mail_server.ehlo()

    return mail_server

def initialize_alarm_account(username, passwd, account_type="gmail"):
    assert username and passwd, "Need a valid username and passwd pair"

    if _verify_account(username, passwd, account_type=account_type):
        with open("user_alarm.txt", "w") as save_file:
            server, port = _get_server_port_pair(account_type)
            save_file.write("Server: " + server + "\n")
            save_file.write("Port: "+str(port)+"\n")
            save_file.write("Username: "+username+"\n")
            save_file.write("Password: "+passwd+"\n")
    else:
        raise ValueError("It is not a valid username password pair")

def _verify_account(username, passwd, account_type="gmail"):
    server, port = _get_server_port_pair(account_type)
    mail_server = _initialize_smtp_server(server, port)

    try:
        mail_server.login(username, passwd)
        return True
    except:
        return False

def add_receipent(receipent):
    assert os.path.exists("user_alarm.txt"), "You have to initialize an email account first"

    with open("user_alarm.txt", "a") as user_alarm:
        user_alarm.write("Receipent: "+receipent+"\n")

def _make_message_body(from_, to_):
    message = MIMEMultipart()
    message["From"] = from_
    message["To"]   = to_
    message["Subject"] = "Alarm from Surveillance Camera"

    body = "The surveillance camera system detected suspicous, please react asap."
    message.attach(MIMEText(body))

    return message.as_string()

def send_alarm():
    assert os.path.exists("user_alarm.txt"), "You have to initialize an email account first"

    with open("user_alarm.txt", "r") as user_alarm:
        lines    = user_alarm.read().split("\n")[:-1]

        server   = lines[0][len("Server: "):]
        port     = int(lines[1][len("Port: "):])
        username = lines[2][len("Username: "):]
        password = lines[3][len("Password: "):]

        receipents = [msg[len("Receipent: "):] for msg in lines[4:]]

        mail_server = _initialize_smtp_server(server, port)
        mail_server.login(username, password)

        for receipent in receipents:
            message = _make_message_body(username, receipent)
            mail_server.sendmail(username, receipent, message)

    
if __name__ == "__main__":
    initialize_alarm_account("eecs488alarm@gmail.com", "qwertyuiop1qwertyuiop")
    add_receipent("jeromemao95@gmail.com")
    send_alarm()
