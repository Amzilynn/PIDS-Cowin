import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# Configuration SMTP (à remplir dans le .env)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "noreply@avalive.tn")

def send_email(subject, recipient_email, body_text, body_html=None):
    """
    Envoie un email via SMTP.
    Si les identifiants sont manquants, simule l'envoi dans la console.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"--- [MOCK MAIL] ---")
        print(f"To: {recipient_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body_text}")
        print(f"-------------------")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = MAIL_FROM
        msg["To"] = recipient_email

        # Version texte
        part1 = MIMEText(body_text, "plain")
        msg.attach(part1)

        # Version HTML optionnelle
        if body_html:
            part2 = MIMEText(body_html, "html")
            msg.attach(part2)

        # Connexion et envoi
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(MAIL_FROM, recipient_email, msg.as_string())
        
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email à {recipient_email}: {e}")
        return False
