"""ResendのHTTP APIを使ったDjango email backend。"""

import logging
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        import resend
        from django.conf import settings

        resend.api_key = settings.RESEND_API_KEY
        sent = 0

        for message in email_messages:
            try:
                resend.Emails.send({
                    "from": message.from_email,
                    "to": message.to,
                    "subject": message.subject,
                    "html": message.body if message.content_subtype == "html" else f"<pre>{message.body}</pre>",
                })
                sent += 1
            except Exception as e:
                logger.error("Resend send failed: %s", e)
                if not self.fail_silently:
                    raise

        return sent
