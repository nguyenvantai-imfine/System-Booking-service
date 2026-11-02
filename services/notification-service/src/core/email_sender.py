import smtplib
import logging
from email.utils import parseaddr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from src.core.config import settings

logger = logging.getLogger(__name__)
SMTP_RECIPIENT_REJECTED_PERMANENTLY = "SMTP recipient rejected permanently."

class EmailSender:
    @staticmethod
    def _masked_recipient(to_email: str) -> str:
        address = parseaddr(to_email)[1]
        if "@" not in address:
            return "invalid-recipient"
        local, domain = address.rsplit("@", 1)
        return f"{local[:1]}***@{domain}"

    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str, text_content: str = "") -> tuple[bool, str]:
        """
        Gửi email qua SMTP (hỗ trợ Gmail, Mailtrap, AWS SES, v.v.)
        Trả về (is_success, error_or_info_message)
        """
        # Kiểm tra chế độ Mock và cấu hình SMTP
        use_mock = settings.MOCK_EMAIL_SEND

        has_smtp_credentials = bool(
            settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD
        )

        if use_mock:
            logger.info(
                "Mock email accepted; recipient=%s status=SENT",
                EmailSender._masked_recipient(to_email),
            )
            return True, "Email sent successfully (Simulation/Mock mode)"

        if not has_smtp_credentials:
            logger.error("SMTP mode is enabled but required SMTP settings are missing.")
            return False, "SMTP is enabled but its required settings are incomplete."

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
                server = smtplib.SMTP_SSL(
                    settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout
                )
                with server:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(
                        settings.SMTP_FROM_EMAIL, [to_email], msg.as_string()
                    )
            else:
                with smtplib.SMTP(
                    settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout
                ) as server:
                    if settings.SMTP_TLS:
                        server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(
                        settings.SMTP_FROM_EMAIL, [to_email], msg.as_string()
                    )
            logger.info(
                "SMTP email sent; recipient=%s status=SENT",
                EmailSender._masked_recipient(to_email),
            )
            return True, "Email sent successfully via SMTP"
        except smtplib.SMTPRecipientsRefused as exc:
            response_codes = [
                response[0]
                for response in exc.recipients.values()
                if isinstance(response, tuple)
                and response
                and isinstance(response[0], int)
            ]
            if response_codes and all(500 <= code < 600 for code in response_codes):
                logger.warning(
                    "SMTP rejected recipient permanently; recipient=%s",
                    EmailSender._masked_recipient(to_email),
                )
                return False, SMTP_RECIPIENT_REJECTED_PERMANENTLY
            logger.warning(
                "SMTP rejected recipient temporarily; recipient=%s",
                EmailSender._masked_recipient(to_email),
            )
            return False, "SMTP recipient was temporarily rejected."
        except (OSError, smtplib.SMTPException) as exc:
            error_msg = f"SMTP send failed ({type(exc).__name__})."
            logger.warning(
                "SMTP email failed; recipient=%s error_type=%s",
                EmailSender._masked_recipient(to_email),
                type(exc).__name__,
            )
            return False, error_msg

email_sender = EmailSender()
