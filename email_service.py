"""SMTP invitation delivery for scheduled candidate assessments."""
import os
import smtplib
from datetime import date
from email.message import EmailMessage
import streamlit as st


class EmailDeliveryError(ValueError):
    """Safe, user-facing email configuration or delivery error."""


def _setting(name, default=''):
    """Read environment variables, falling back to Streamlit Secrets."""
    value = os.environ.get(name, '').strip()
    if value:
        return value
    try:
        return str(st.secrets.get(name, default)).strip()
    except (FileNotFoundError, KeyError, AttributeError):
        return str(default).strip()


def _email_settings():
    host = _setting('SMTP_HOST')
    sender = _setting('SMTP_FROM')
    app_url = _setting('APP_URL').rstrip('/')
    if not host or not sender or not app_url:
        raise EmailDeliveryError('Set SMTP_HOST, SMTP_FROM, and APP_URL before sending invitations.')
    return host, sender, app_url


def _deliver(message, host):
    try:
        port = int(_setting('SMTP_PORT', '587'))
    except ValueError as exc:
        raise EmailDeliveryError('SMTP_PORT must be a number.') from exc
    username_setting = _setting('SMTP_USERNAME')
    password = _setting('SMTP_PASSWORD')
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.starttls()
        if username_setting:
            smtp.login(username_setting, password)
        smtp.send_message(message)


def send_candidate_invitation(email, name, username, temporary_password, test_date, discipline=''):
    host, sender, app_url = _email_settings()

    message = EmailMessage()
    if isinstance(test_date, date):
        display_date = test_date.strftime('%A, %d %B %Y')
    else:
        try:
            display_date = date.fromisoformat(str(test_date)).strftime('%A, %d %B %Y')
        except ValueError:
            display_date = str(test_date)

    message['Subject'] = f'QC Candidate Assessment Scheduled - {display_date}'
    message['From'] = sender
    message['To'] = email
    message.set_content(
        f'Dear {name},\n\n'
        'Your QC Candidate Assessment has been scheduled. Please review the details below and '
        'keep this message available for the assessment date.\n\n'
        f'Scheduled date: {display_date}\n'
        f'Discipline: {discipline or "As assigned in the portal"}\n'
        f'Assessment portal: {app_url}\n\n'
        'Login credentials\n'
        f'Username: {username}\n'
        f'Temporary password: {temporary_password}\n\n'
        f'Your login is valid only on {display_date}. The portal will not accept your candidate '
        'login before or after this scheduled date.\n\n'
        'Please be presentable and maintain a professional appearance and conduct throughout the '
        'assessment, including the oral and practical portions.\n\n'
        'On the scheduled date, open the assessment portal, enter the credentials above, and '
        'follow the on-screen instructions. Please keep these credentials confidential and do '
        'not forward this email.\n\n'
        'If your schedule or candidate information is incorrect, contact your assessment '
        'coordinator before the test date.\n\n'
        'Regards,\nCompetency Technical Assessment (CTA)\n'
    )
    _deliver(message, host)


def send_reviewer_credentials(email, name, username, initial_password):
    host, sender, app_url = _email_settings()
    message = EmailMessage()
    message['Subject'] = 'Your Competency Technical Assessment (CTA) reviewer account'
    message['From'] = sender
    message['To'] = email
    message.set_content(
        f'Dear {name},\n\n'
        'A Reviewer account has been created for you in the Competency Technical Assessment (CTA) portal. '
        'You can use this account to manage candidate schedules, review assigned assessments, '
        'and record grades and feedback.\n\n'
        f'Portal link: {app_url}\n'
        'Role: Reviewer\n'
        f'Username: {username}\n'
        f'Initial password: {initial_password}\n\n'
        'Open the portal and sign in with the credentials above. After signing in, use '
        'Change password in the sidebar to choose your own password.\n\n'
        'Keep these credentials confidential and do not forward this email. If you did not '
        'expect this account or cannot sign in, contact the portal administrator.\n\n'
        'Regards,\nCompetency Technical Assessment (CTA)\n'
    )
    _deliver(message, host)


def send_test_email(email, name='Administrator'):
    """Send a harmless message to verify the portal's SMTP configuration."""
    host, sender, app_url = _email_settings()
    message = EmailMessage()
    message['Subject'] = 'Competency Technical Assessment (CTA) email test'
    message['From'] = sender
    message['To'] = email
    message.set_content(
        f'Dear {name},\n\n'
        'This is a test email from the Competency Technical Assessment (CTA) portal. '
        'Your SMTP configuration is working correctly.\n\n'
        f'Portal link: {app_url}\n\n'
        'Regards,\nCompetency Technical Assessment (CTA)\n'
    )
    _deliver(message, host)


def send_candidate_result(email, name, pdf_bytes):
    """Email a generated candidate result PDF as an attachment."""
    host, sender, app_url = _email_settings()
    message = EmailMessage()
    message['Subject'] = 'QC Candidate Assessment Result'
    message['From'] = sender
    message['To'] = email
    message.set_content(
        f'Dear {name},\n\n'
        'Please find attached your Competency Technical Assessment (CTA) result. '
        'The report includes your result by question type, overall result, and the pass/fail rules used by the portal.\n\n'
        f'Assessment portal: {app_url}\n\n'
        'Regards,\nQUALITY DEPARTMENT | C.A.T. INTERNATIONAL L.L.C.\n'
    )
    message.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename='candidate-result.pdf')
    _deliver(message, host)
