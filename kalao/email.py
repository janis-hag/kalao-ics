import smtplib
from email.message import EmailMessage

import config


def send_email(subject: str, message: str, subtype: str = 'plain') -> None:
    with smtplib.SMTP(config.Email.host, port=config.Email.port) as smtp:
        smtp.ehlo()

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = config.Email.sender
        msg['To'] = ', '.join(config.Email.receivers)

        msg.set_content(message, subtype=subtype)

        smtp.send_message(msg)
