import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class EmailSender:
    def __init__(self, smtp_server='smtp.gmail.com', port=587):
        self.smtp_server = smtp_server
        self.port = port
        self.server = None
        self.from_address = "jhstep23@gmail.com"  # Email address to send from
        self.password = "lhnd jvnk rkej ptll"  # Your email password

    def connect(self):
        try:
            self.server = smtplib.SMTP(self.smtp_server, self.port)
            self.server.starttls()
            self.server.login(self.from_address, self.password)
        except smtplib.SMTPException as e:
            print(f"Failed to connect: {e}")
            self.server = None

    def send_email(self, to_address, subject, body):
        if not self.server:
            self.connect()

        if self.server:
            # Create the message
            msg = MIMEMultipart()
            msg['From'] = self.from_address
            msg['To'] = to_address
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            try:
                self.server.send_message(msg)
                print(f"Email sent successfully to {to_address}")
            except smtplib.SMTPException as e:
                print(f"Failed to send email: {e}")

    def quit(self):
        if self.server:
            self.server.quit()
            self.server = None


