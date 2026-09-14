import pytest

import email_service
from email_service import EmailDeliveryError, send_candidate_invitation


def test_invitation_requires_mail_configuration(monkeypatch):
    for key in ('SMTP_HOST', 'SMTP_FROM', 'APP_URL'):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(EmailDeliveryError, match='SMTP_HOST'):
        send_candidate_invitation('candidate@example.com', 'Candidate', 'candidate', 'temporary-123', '2026-09-10')


def test_invitation_contains_schedule_and_credentials(monkeypatch):
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            sent['connection'] = (host, port, timeout)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def starttls(self):
            sent['tls'] = True

        def login(self, username, password):
            sent['login'] = (username, password)

        def send_message(self, message):
            sent['message'] = message

    settings = {
        'SMTP_HOST': 'smtp.example.com', 'SMTP_PORT': '587',
        'SMTP_FROM': 'qc@example.com', 'SMTP_USERNAME': 'mailer',
        'SMTP_PASSWORD': 'smtp-secret', 'APP_URL': 'https://qc.example.com/',
    }
    for key, value in settings.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr('email_service.smtplib.SMTP', FakeSMTP)

    send_candidate_invitation(
        'candidate@example.com', 'Candidate Name', 'candidate.user',
        'Temp!Pass123', '2026-09-10', 'Welding QC',
    )

    message = sent['message']
    body = message.get_content()
    assert message['To'] == 'candidate@example.com'
    assert 'Thursday, 10 September 2026' in body
    assert 'Welding QC' in body
    assert 'candidate.user' in body
    assert 'Temp!Pass123' in body
    assert 'valid only on Thursday, 10 September 2026' in body
    assert 'https://qc.example.com' in body
    assert sent['tls'] is True


def test_reviewer_credentials_have_meaningful_instructions(monkeypatch):
    sent = {}
    monkeypatch.setattr(
        email_service, '_email_settings',
        lambda: ('smtp.example.com', 'qc@example.com', 'https://qc.example.com'),
    )
    monkeypatch.setattr(
        email_service, '_deliver',
        lambda message, host: sent.update(message=message, host=host),
    )

    email_service.send_reviewer_credentials(
        'reviewer@example.com', 'Reviewer Name', 'reviewer.user', 'Start!Pass123'
    )

    message = sent['message']
    body = message.get_content()
    assert message['To'] == 'reviewer@example.com'
    assert 'Reviewer account has been created' in body
    assert 'https://qc.example.com' in body
    assert 'reviewer.user' in body
    assert 'Start!Pass123' in body
    assert 'Change password in the sidebar' in body
    assert 'Keep these credentials confidential' in body


def test_test_email_contains_portal_link(monkeypatch):
    sent = {}
    monkeypatch.setattr(email_service, '_email_settings', lambda: ('smtp.example.com', 'qc@example.com', 'https://qc.example.com'))
    monkeypatch.setattr(email_service, '_deliver', lambda message, host: sent.update(message=message, host=host))

    email_service.send_test_email('admin@example.com', 'Admin Name')

    message = sent['message']
    assert message['To'] == 'admin@example.com'
    assert message['Subject'] == 'Competency Technical Assessment (CTA) email test'
    assert 'SMTP configuration is working correctly' in message.get_content()
    assert 'https://qc.example.com' in message.get_content()
