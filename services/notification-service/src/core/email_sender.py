import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from src.core.config import settings

logger = logging.getLogger(__name__)

class EmailSender:
    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str, text_content: str = "") -> tuple[bool, str]:
        """
        Gửi email qua SMTP (hỗ trợ Gmail, Mailtrap, AWS SES, v.v.)
        Trả về (is_success, error_or_info_message)
        """
        # Kiểm tra chế độ Mock và cấu hình SMTP
        use_mock = getattr(settings, "USE_MOCK_EMAIL", None)
        if use_mock is None:
            use_mock = getattr(settings, "MOCK_EMAIL_SEND", True)

        has_smtp_credentials = bool(
            settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD
        )

        # Nếu đang ở chế độ Mock hoặc chưa cấu hình đầy đủ SMTP credentials
        if use_mock or not has_smtp_credentials:
            logger.info(f"[MOCK EMAIL SENT] To: {to_email}")
            print(f">>> [NOTIFICATION SERVICE - EMAIL DISPATCHED] >>>")
            print(f"    Recipient: {to_email}")
            safe_subj = subject.encode("ascii", "replace").decode("ascii")
            print(f"    Subject:   {safe_subj}")
            if text_content:
                first_lines = [l.strip() for l in text_content.strip().split("\n") if l.strip()][:3]
                preview_text = " | ".join(first_lines).encode("ascii", "replace").decode("ascii")
                print(f"    Preview:   {preview_text}")
            print(f"    Status:    SENT (MOCK/SIMULATION SUCCESS)")
            return True, "Email sent successfully (Simulation/Mock mode)"

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = to_email

            if text_content:
                msg.attach(MIMEText(text_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            timeout = 10
            if settings.SMTP_PORT == 465:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout)
                if settings.SMTP_TLS:
                    server.starttls()

            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

            server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
            server.quit()
            logger.info(f"[REAL SMTP EMAIL SENT] To: {to_email} | Subject: {subject}")
            print(f">>> [NOTIFICATION SERVICE - REAL SMTP EMAIL SENT] >>> To: {to_email} | Subject: {subject}")
            return True, "Email sent successfully via SMTP"
        except Exception as e:
            error_msg = f"SMTP Error: {str(e)}"
            logger.error(error_msg)
            print(f">>> [NOTIFICATION SERVICE - SMTP ERROR]: {error_msg}")
            return False, error_msg

email_sender = EmailSender()
