"""
infrastructure/email/email_service.py

Asynchronous transactional email dispatch service for Clinora.
Handles:
- Account verification emails
- Password reset recovery links with 1-hour expiry
- Fallback logging when mail is disabled
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from core.config import settings

log = logging.getLogger(__name__)


def _render_email_html(
    headline: str,
    greeting_name: str,
    body_text: str,
    button_label: str,
    action_url: str,
    footer_note: str,
) -> str:
    """Renders a responsive, modern HTML email with Clinora clinical branding."""
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{headline} · Clinora</title>
    <style>
      body {{ margin: 0; padding: 0; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f8fafc; }}
      strong {{ color: #ffffff; }}
      .email-wrapper {{ background-color: #0f172a; padding: 40px 16px; width: 100%; }}
      .email-card {{ max-width: 540px; margin: 0 auto; background-color: #1e293b; border-radius: 12px; border: 1px solid #334155; overflow: hidden; padding: 36px 32px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3); }}
      .email-brand {{ text-align: center; padding-bottom: 24px; }}
      .email-brand-logo {{ display: inline-block; background: #2563eb; border-radius: 8px; width: 36px; height: 36px; line-height: 36px; color: #ffffff; font-weight: bold; font-size: 20px; }}
      .email-brand-name {{ display: inline-block; padding-left: 10px; font-size: 22px; font-weight: 700; color: #ffffff; vertical-align: middle; }}
      .email-headline {{ margin: 0 0 16px 0; font-size: 22px; font-weight: 700; color: #ffffff; text-align: center; line-height: 1.3; }}
      .email-text {{ font-size: 15px; line-height: 1.6; color: #cbd5e1; text-align: center; margin-bottom: 28px; }}
      .email-btn-wrap {{ text-align: center; margin-bottom: 28px; }}
      .email-btn {{ display: inline-block; background: #2563eb; color: #ffffff !important; text-decoration: none; font-size: 15px; font-weight: 600; padding: 13px 32px; border-radius: 8px; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4); }}
      .email-fallback {{ border-top: 1px solid #334155; padding-top: 16px; font-size: 13px; color: #94a3b8; word-break: break-all; text-align: center; }}
      .email-note {{ margin-top: 20px; font-size: 12px; line-height: 1.5; color: #64748b; text-align: center; }}
      .email-footer {{ max-width: 540px; margin: 20px auto 0 auto; text-align: center; font-size: 12px; color: #64748b; }}
    </style>
  </head>
  <body>
    <div class="email-wrapper">
      <div class="email-card">
        <div class="email-brand">
          <span class="email-brand-logo">C</span>
          <span class="email-brand-name">Clinora</span>
        </div>
        <h1 class="email-headline">{headline}</h1>
        <p class="email-text">
          Hi <strong>{greeting_name}</strong>,<br><br>
          {body_text}
        </p>
        <div class="email-btn-wrap">
          <a href="{action_url}" class="email-btn" target="_blank">{button_label}</a>
        </div>
        <div class="email-fallback">
          If the button doesn't work, copy and paste this link in your browser:<br>
          <a href="{action_url}" style="color: #60a5fa;">{action_url}</a>
        </div>
        <div class="email-note">{footer_note}</div>
      </div>
      <div class="email-footer">
        © Clinora Clinical Platform · Private & Confidential
      </div>
    </div>
  </body>
</html>"""


class EmailService:
    """Async email dispatcher with SMTP and local development fallback."""

    @classmethod
    def _send_smtp_sync(cls, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Synchronous SMTP transport executed in a thread pool."""
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.mail_default_sender or settings.mail_username or "noreply@clinora.com"
        msg["To"] = to_email
        msg.set_content(text_content)
        msg.add_alternative(html_content, subtype="html")

        try:
            with smtplib.SMTP(settings.mail_server, settings.mail_port, timeout=15) as server:
                if settings.mail_use_tls:
                    server.starttls()
                if settings.mail_username and settings.mail_password:
                    server.login(settings.mail_username, settings.mail_password)
                server.send_message(msg)
            log.info("Email sent to %s with subject: %s", to_email, subject)
            return True
        except Exception as e:
            log.error("Failed to send email to %s via SMTP: %s", to_email, e)
            return False

    @classmethod
    async def send_verification_email(cls, to_email: str, recipient_name: str, token: str) -> bool:
        """Send account email verification link."""
        verify_url = f"{settings.frontend_url}/verify-email/{token}"

        if not settings.mail_enabled:
            log.info("[EMAIL DISABLED] Verification link for %s: %s", to_email, verify_url)
            print(f"\n[EMAIL DEV MOCK] Verification link for {to_email}:\n{verify_url}\n")
            return True

        subject = "Verify your Clinora account"
        body_text = "Welcome to Clinora! Please confirm your email address to activate your clinical workspace account."
        footer_note = "If you did not sign up for a Clinora account, please ignore this email."

        html = _render_email_html(
            headline="Verify Your Email Address",
            greeting_name=recipient_name or "there",
            body_text=body_text,
            button_label="Verify Email Address",
            action_url=verify_url,
            footer_note=footer_note,
        )

        plain = (
            f"Hi {recipient_name or 'there'},\n\n"
            f"Please verify your Clinora email address by visiting:\n{verify_url}\n\n"
            f"If you did not create an account, you can safely ignore this email.\n\n"
            f"— The Clinora Team"
        )

        return await asyncio.to_thread(cls._send_smtp_sync, to_email, subject, html, plain)

    @classmethod
    async def send_password_reset_email(cls, to_email: str, recipient_name: str, token: str) -> bool:
        """Send password recovery link (1-hour expiry)."""
        reset_url = f"{settings.frontend_url}/reset-password/{token}"

        if not settings.mail_enabled:
            log.info("[EMAIL DISABLED] Password reset link for %s: %s", to_email, reset_url)
            print(f"\n[EMAIL DEV MOCK] Password reset link for {to_email}:\n{reset_url}\n")
            return True

        subject = "Reset your Clinora password"
        body_text = (
            "We received a request to reset your password. Click the button below to choose a new password. "
            "This link will expire in 1 hour."
        )
        footer_note = "If you did not request a password reset, no action is needed. Your account remains secure."

        html = _render_email_html(
            headline="Reset Your Password",
            greeting_name=recipient_name or "there",
            body_text=body_text,
            button_label="Reset Password",
            action_url=reset_url,
            footer_note=footer_note,
        )

        plain = (
            f"Hi {recipient_name or 'there'},\n\n"
            f"We received a request to reset your Clinora password. Visit:\n{reset_url}\n\n"
            f"This link expires in 1 hour. If you did not request this, please ignore this email.\n\n"
            f"— The Clinora Team"
        )

        return await asyncio.to_thread(cls._send_smtp_sync, to_email, subject, html, plain)
