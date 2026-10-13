from __future__ import annotations

import os
import smtplib
import ssl
from collections.abc import Mapping
from dataclasses import dataclass, field
from email.message import EmailMessage
from email.utils import parseaddr
from pathlib import Path


def validate_email(address: str) -> str:
  value = address.strip()
  name, mailbox = parseaddr(value)
  if (not value or name or mailbox != value or value.count("@") != 1
      or any(c.isspace() for c in value) or not all(value.split("@"))):
    raise ValueError("Provide a single valid email address.")
  return value


@dataclass(frozen=True)
class SmtpSettings:
  host: str
  sender: str
  port: int = 587
  security: str = "starttls"
  username: str | None = None
  password: str | None = field(default=None, repr=False)

  @classmethod
  def from_env(cls, environ: Mapping[str, str] | None = None) -> SmtpSettings:
    env = os.environ if environ is None else environ
    host = env.get("DOCS2EPUB_SMTP_HOST", "").strip()
    sender = env.get("DOCS2EPUB_SMTP_FROM", "").strip()
    if not host:
      raise ValueError("Set DOCS2EPUB_SMTP_HOST for Kindle email delivery.")
    if not sender:
      raise ValueError("Set DOCS2EPUB_SMTP_FROM to an Amazon-approved sender.")
    validate_email(sender)
    security = env.get("DOCS2EPUB_SMTP_SECURITY", "starttls").lower().strip()
    if security not in {"starttls", "ssl"}:
      raise ValueError("DOCS2EPUB_SMTP_SECURITY must be starttls or ssl.")
    try:
      port = int(env.get("DOCS2EPUB_SMTP_PORT", "465" if security == "ssl" else "587"))
    except ValueError:
      raise ValueError("DOCS2EPUB_SMTP_PORT must be a number from 1 to 65535.") from None
    if not 1 <= port <= 65535:
      raise ValueError("DOCS2EPUB_SMTP_PORT must be a number from 1 to 65535.")
    username = env.get("DOCS2EPUB_SMTP_USER") or None
    password = env.get("DOCS2EPUB_SMTP_PASSWORD") or None
    if bool(username) != bool(password):
      raise ValueError("Set both DOCS2EPUB_SMTP_USER and DOCS2EPUB_SMTP_PASSWORD, or neither.")
    return cls(host=host, sender=sender, port=port, security=security,
      username=username, password=password)


def send_epub_to_kindle(path: str | Path, recipient: str, settings: SmtpSettings) -> None:
  recipient = validate_email(recipient)
  epub_path = Path(path)
  message = EmailMessage()
  message["From"] = settings.sender
  message["To"] = recipient
  message["Subject"] = "docs2epub EPUB"
  message.set_content("Your documentation EPUB is attached.")
  message.add_attachment(epub_path.read_bytes(), maintype="application",
    subtype="epub+zip", filename=epub_path.name)
  context = ssl.create_default_context()
  try:
    if settings.security == "ssl":
      connection = smtplib.SMTP_SSL(settings.host, settings.port, timeout=30, context=context)
    else:
      connection = smtplib.SMTP(settings.host, settings.port, timeout=30)
    with connection as smtp:
      smtp.ehlo()
      if settings.security == "starttls":
        smtp.starttls(context=context)
        smtp.ehlo()
      if settings.username is not None:
        smtp.login(settings.username, settings.password)
      smtp.send_message(message)
  except smtplib.SMTPAuthenticationError:
    raise RuntimeError("SMTP authentication failed; check the user and password. The EPUB is saved locally.") from None
  except (smtplib.SMTPException, OSError):
    raise RuntimeError("SMTP delivery failed; check the server, TLS settings and recipient. The EPUB is saved locally.") from None
