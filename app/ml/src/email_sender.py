import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

def send_surge_email(to_emails: List[str], venue_name: str, alert_data: Dict):
    """
    Send surge alert email to list of recipients.
    """
    if not to_emails:
        logger.warning("No email recipients provided for surge alert")
        return

    subject = f"⚠️ SURGE ALERT - {venue_name}"
    
    # HTML Template (Matching Go Service Style)
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Rubik', Arial, sans-serif; background-color: #F2DFDF; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; }}
        .header {{ background: linear-gradient(135deg, #010440 0%, #031D40 100%); padding: 30px; text-align: center; color: #ffffff; }}
        .header h1 {{ font-size: 28px; margin: 0 0 5px 0; }}
        .content {{ padding: 35px 40px; color: #0D0D0D; }}
        .greeting {{ font-size: 22px; color: #010440; font-weight: 600; margin-bottom: 15px; }}
        .badge {{ display: inline-block; background: #f8d7da; color: #721c24; padding: 8px 18px; border-radius: 20px; font-weight: 600; font-size: 14px; margin: 15px 0; }}
        .detail-box {{ background: linear-gradient(135deg, #F2DFDF 0%, #ffffff 100%); border-left: 4px solid #BF4124; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .detail-label {{ font-weight: 600; color: #031D40; font-size: 13px; text-transform: uppercase; margin-bottom: 5px; }}
        .detail-value {{ font-size: 15px; color: #0D0D0D; margin-bottom: 12px; }}
        .message {{ font-size: 16px; line-height: 1.8; margin: 20px 0; }}
        .action-note {{ background: #fff3cd; border-left: 4px solid #856404; padding: 15px 20px; border-radius: 6px; margin: 20px 0; font-size: 14px; color: #856404; }}
        .footer {{ background-color: #F2DFDF; padding: 20px; text-align: center; font-size: 13px; color: #031D40; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⏰ AntiClockWise</h1>
            <p>Workforce Management & Scheduling</p>
        </div>
        <div class="content">
            <div class="greeting">High Demand Alert ⚠️</div>
            <div class="badge">SEVERITY: {alert_data.get('severity', 'UNKNOWN').upper()}</div>
            
            <p class="message">
                A significant surge in demand has been detected at <strong>{venue_name}</strong>.
            </p>
            
            <div class="detail-box">
                <div class="detail-label">Current Status</div>
                <div class="detail-value">
                    • <strong>Multiplier:</strong> {alert_data.get('avg_ratio', 0):.1f}x normal demand<br>
                    • <strong>Risk Score:</strong> {alert_data.get('risk_score', 0):.2f}/1.0<br>
                    • <strong>Trend:</strong> {alert_data.get('trend', 'unknown').title()}
                </div>
                
                <div class="detail-label">Root Cause</div>
                <div class="detail-value">{alert_data.get('root_cause', 'Unknown').replace('_', ' ').title()}</div>
                
                <div class="detail-label">Estimated Duration</div>
                <div class="detail-value">{alert_data.get('estimated_duration', 'Unknown')}</div>
            </div>

            <div class="action-note">
                <strong>📋 Recommended Actions:</strong>
                <ul>
                    {''.join(f'<li>{rec}</li>' for rec in alert_data.get('recommendations', []))}
                </ul>
            </div>
            
            <p style="font-size: 14px; color: #6c757d; margin-top: 25px;">
                Please verify staffing levels immediately.
            </p>
        </div>
        <div class="footer">
            <p><strong>AntiClockWise Surge Detection</strong></p>
            <p>This is an automated message.</p>
            <p>&copy; 2026 AntiClockWise. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"AntiClockWise Alerts <{SMTP_USERNAME}>"
    # To header only for first recipient to avoid revealing all, or use named group
    msg["To"] = to_emails[0] 

    part = MIMEText(html_content, "html")
    msg.attach(part)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            
            server.sendmail(SMTP_USERNAME, to_emails, msg.as_string())
            logger.info(f"Sent surge alert email to {len(to_emails)} recipients")
            
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

