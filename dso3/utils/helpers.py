import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def send_recommendation_email(user_email: str, delegate_name: str, product_name: str):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    
    subject = f"Nouveau produit recommandé : {product_name}"
    body = f"Bonjour {delegate_name},\n\nUn nouveau produit intitulé '{product_name}' vous a été recommandé par le système d'intelligence terrain.\n\nVeuillez consulter votre tableau de bord pour plus de détails.\n\nCordialement,\nL'équipe MédDelegate Pro"
    
    if not smtp_user or not smtp_password:
        logger.warning(f"Mail mocking (No SMTP config) - To: {user_email}")
        print(f"\n[{user_email}] --- SIMULATION ENVOI EMAIL ---")
        print(f"Sujet: {subject}")
        print(f"Message:\n{body}")
        print("------------------------------------------\n")
        return
        
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = user_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        logger.info(f"Email successfully sent to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {user_email}: {e}")
