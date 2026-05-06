import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration SMTP (à remplir via .env idéalement)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@avalive.tn")

def send_email(to_email: str, subject: str, body: str):
    """
    Envoie un email via SMTP.
    Si les credentials sont absents, simule l'envoi dans la console.
    """
    print(f"📧 [Mailer] Envoi d'email à {to_email}...")
    print(f"📝 Sujet : {subject}")
    
    if not SMTP_USER or not SMTP_PASSWORD:
        print("⚠️ [Mailer] SMTP_USER ou SMTP_PASSWORD non configurés. Simulation réussie.")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, to_email, text)
        server.quit()
        print("✅ [Mailer] Email envoyé avec succès.")
        return True
    except Exception as e:
        print(f"❌ [Mailer] Erreur lors de l'envoi : {e}")
        return False
