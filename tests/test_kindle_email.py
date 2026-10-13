import smtplib
from email import policy
from email.parser import BytesParser

import pytest

from docs2epub.kindle_email import SmtpSettings, send_epub_to_kindle


def env(**overrides):
  return {
    "DOCS2EPUB_SMTP_HOST": "smtp.example.com",
    "DOCS2EPUB_SMTP_FROM": "sender@example.com",
    **overrides,
  }


def test_settings_require_host_and_sender():
  with pytest.raises(ValueError, match="SMTP_HOST"):
    SmtpSettings.from_env({})
  with pytest.raises(ValueError, match="SMTP_FROM"):
    SmtpSettings.from_env({"DOCS2EPUB_SMTP_HOST": "smtp.example.com"})


@pytest.mark.parametrize("overrides", [
  {"DOCS2EPUB_SMTP_PORT": "wrong"},
  {"DOCS2EPUB_SMTP_PORT": "0"},
  {"DOCS2EPUB_SMTP_SECURITY": "plain"},
  {"DOCS2EPUB_SMTP_USER": "user"},
  {"DOCS2EPUB_SMTP_PASSWORD": "secret"},
  {"DOCS2EPUB_SMTP_FROM": "sender@example.com\nBcc: other@example.com"},
])
def test_settings_reject_invalid_configuration(overrides):
  with pytest.raises(ValueError):
    SmtpSettings.from_env(env(**overrides))


@pytest.mark.parametrize("security,port", [("starttls", 587), ("ssl", 465)])
def test_sender_uses_tls_and_sends_exact_epub(monkeypatch, tmp_path, security, port):
  calls = []
  class FakeSmtp:
    def __init__(self, host, smtp_port, **kwargs):
      assert (host, smtp_port) == ("smtp.example.com", port)
      assert kwargs["timeout"] == 30
      if security == "ssl":
        assert kwargs["context"].check_hostname
      calls.append("connect")
    def __enter__(self): return self
    def __exit__(self, *args): calls.append("close")
    def ehlo(self): calls.append("ehlo")
    def starttls(self, *, context):
      assert context.check_hostname
      calls.append("tls")
    def login(self, user, password):
      assert (user, password) == ("smtp-user", "secret")
      calls.append("login")
    def send_message(self, message):
      calls.append("send")
      parsed = BytesParser(policy=policy.default).parsebytes(message.as_bytes())
      assert parsed["To"] == "reader@kindle.com"
      assert parsed["From"] == "sender@example.com"
      attachments = list(parsed.iter_attachments())
      assert len(attachments) == 1
      assert attachments[0].get_content_type() == "application/epub+zip"
      assert attachments[0].get_filename() == "book.epub"
      assert attachments[0].get_payload(decode=True) == b"PK\x03\x04epub-content"
  monkeypatch.setattr(smtplib, "SMTP", FakeSmtp)
  monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSmtp)
  path = tmp_path / "book.epub"
  path.write_bytes(b"PK\x03\x04epub-content")
  settings = SmtpSettings.from_env(env(DOCS2EPUB_SMTP_SECURITY=security,
    DOCS2EPUB_SMTP_USER="smtp-user", DOCS2EPUB_SMTP_PASSWORD="secret"))
  send_epub_to_kindle(path, "reader@kindle.com", settings)
  assert calls[-3:] == ["login", "send", "close"]
  assert ("tls" in calls) == (security == "starttls")
  assert calls.index("login") > calls.index("connect")
  if security == "starttls":
    assert calls.index("tls") < calls.index("login")


def test_sender_does_not_leak_authentication_error_or_delete_epub(monkeypatch, tmp_path):
  class FailedSmtp:
    def __init__(self, *args, **kwargs):
      raise smtplib.SMTPAuthenticationError(535, b"secret credential detail")
  monkeypatch.setattr(smtplib, "SMTP", FailedSmtp)
  path = tmp_path / "book.epub"
  path.write_bytes(b"epub")
  with pytest.raises(RuntimeError, match="authentication") as exc:
    send_epub_to_kindle(path, "reader@kindle.com", SmtpSettings.from_env(env()))
  assert "secret" not in str(exc.value)
  assert path.read_bytes() == b"epub"


def test_sender_rejects_invalid_recipient_before_connect(monkeypatch, tmp_path):
  monkeypatch.setattr(smtplib, "SMTP", lambda *a, **k: pytest.fail("must not connect"))
  with pytest.raises(ValueError, match="email"):
    send_epub_to_kindle(tmp_path / "book.epub", "not-an-email", SmtpSettings.from_env(env()))


def test_failed_starttls_does_not_authenticate_or_send(monkeypatch, tmp_path):
  class NoTls:
    def __init__(self, *args, **kwargs): pass
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def ehlo(self): pass
    def starttls(self, **kwargs): raise smtplib.SMTPNotSupportedError("no TLS")
    def login(self, *args): pytest.fail("must not authenticate without TLS")
    def send_message(self, *args): pytest.fail("must not send without TLS")
  monkeypatch.setattr(smtplib, "SMTP", NoTls)
  path = tmp_path / "book.epub"
  path.write_bytes(b"epub")
  settings = SmtpSettings.from_env(env(DOCS2EPUB_SMTP_USER="user", DOCS2EPUB_SMTP_PASSWORD="password"))
  with pytest.raises(RuntimeError, match="SMTP delivery failed"):
    send_epub_to_kindle(path, "reader@kindle.com", settings)
