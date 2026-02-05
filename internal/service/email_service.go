package service

import (
	"fmt"
	"log"
	"log/slog"
	"net/smtp"
	"os"
)

type EmailService interface {
	SendWelcomeEmail(toEmail, username, password, role string, organization string) error
}

type SMTPEmailService struct {
	host     string
	port     string
	username string
	password string
	Logger   *slog.Logger
}

func NewSMTPEmailService(Logger *slog.Logger) *SMTPEmailService {
	return &SMTPEmailService{
		host:     os.Getenv("SMTP_HOST"),
		port:     os.Getenv("SMTP_PORT"),
		username: os.Getenv("SMTP_USERNAME"),
		password: os.Getenv("SMTP_PASSWORD"),
		Logger:   Logger,
	}
}

func (s *SMTPEmailService) SendWelcomeEmail(toEmail, fullName, password, role string, organization string) error {
	// Fallback for development if no SMTP is configured
	if s.host == "" {
		log.Printf("\n[MOCK EMAIL] To: %s | User: %s | Pass: %s | Role: %s | Organization: %s\n", toEmail, fullName, password, role, organization)
		return nil
	}

	auth := smtp.PlainAuth("", s.username, s.password, s.host)

	subject := "Subject: Welcome to ClockWise - Account Details\n"
	mime := "MIME-version: 1.0;\nContent-Type: text/html; charset=\"UTF-8\";\n\n"
	body := fmt.Sprintf(`
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Rubik', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }
        body {
            font-family: 'Rubik', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #F2DFDF;
            padding: 0;
            margin: 0;
            line-height: 1.6;
        }
        .email-container {
            width: 100%%;
            margin: 0;
            background-color: #ffffff;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #010440 0%%, #031D40 100%%);
            padding: 40px 30px;
            text-align: center;
            color: #ffffff;
        }
        .header h1 {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }
        .header p {
            font-size: 16px;
            opacity: 0.95;
            font-weight: 300;
        }
        .content {
            padding: 40px 60px;
            color: #0D0D0D;
        }
        .greeting {
            font-size: 24px;
            color: #010440;
            margin-bottom: 20px;
            font-weight: 600;
        }
        .intro-text {
            font-size: 16px;
            color: #0D0D0D;
            margin-bottom: 30px;
            line-height: 1.8;
        }
        .highlight {
            color: #BF4124;
            font-weight: 600;
        }
        .credentials-box {
            background: linear-gradient(135deg, #F2DFDF 0%%, #ffffff 100%%);
            border-left: 4px solid #BF4124;
            border-radius: 8px;
            padding: 25px;
            margin: 25px 0;
        }
        .credentials-title {
            font-size: 18px;
            font-weight: 600;
            color: #010440;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }
        .credentials-title::before {
            content: "🔐";
            margin-right: 8px;
            font-size: 20px;
        }
        .credential-item {
            background-color: #ffffff;
            padding: 12px 16px;
            margin-bottom: 10px;
            border-radius: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(1, 4, 64, 0.08);
            border: 1px solid #F2DFDF;
        }
        .credential-item:last-child {
            margin-bottom: 0;
        }
        .credential-label {
            font-weight: 600;
            color: #031D40;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-right: 12px;
        }
        .credential-value {
            font-family: 'Courier New', Courier, monospace;
            color: #0D0D0D;
            font-size: 15px;
            font-weight: 500;
        }
        .warning-box {
            background-color: #fff3e0;
            border-left: 4px solid #BF4124;
            padding: 15px 20px;
            border-radius: 6px;
            margin: 25px 0;
        }
        .warning-box p {
            color: #8B2E1C;
            font-size: 14px;
            margin: 0;
            display: flex;
            align-items: center;
        }
        .warning-box p::before {
            content: "⚠️";
            margin-right: 8px;
            font-size: 16px;
        }
        .cta-button {
            display: inline-block;
            background: linear-gradient(135deg, #010440 0%%, #031D40 100%%);
            color: #ffffff;
            text-decoration: none;
            padding: 14px 32px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 4px 12px rgba(1, 4, 64, 0.3);
            transition: transform 0.2s;
        }
        .footer {
            background-color: #F2DFDF;
            padding: 25px 30px;
            text-align: center;
            border-top: 1px solid #031D40;
        }
        .footer p {
            font-size: 13px;
            color: #031D40;
            margin: 5px 0;
        }
        .footer .company-name {
            font-weight: 600;
            color: #010440;
        }
        .divider {
            height: 1px;
            background: linear-gradient(to right, transparent, #F2DFDF, transparent);
            margin: 25px 0;
        }
        @media only screen and (max-width: 768px) {
            .header {
                padding: 30px 20px;
            }
            .content {
                padding: 30px 20px;
            }
            .greeting {
                font-size: 22px;
            }
            .credentials-box {
                padding: 20px;
            }
            .credential-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
            }
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>⏰ ClockWise</h1>
            <p>Workforce Management & Scheduling</p>
        </div>
        
        <div class="content">
            <div class="greeting">Hello, %s! 👋</div>
            
            <p class="intro-text">
                Welcome to ClockWise! You have been invited to join 
                <span class="highlight">%s</span> as a 
                <span class="highlight">%s</span>. 
                We're excited to have you on board!
            </p>
            
            <div class="credentials-box">
                <div class="credentials-title">Your Login Credentials</div>
                
                <div class="credential-item">
                    <span class="credential-label">Email:</span>
                    <span class="credential-value">%s</span>
                </div>
                
                <div class="credential-item">
                    <span class="credential-label">Password:</span>
                    <span class="credential-value">%s</span>
                </div>
            </div>
            
            <div class="warning-box">
                <p>Please login and change your password immediately for security purposes.</p>
            </div>
            
            <div class="divider"></div>
            
            <p style="font-size: 14px; color: #6c757d; margin-top: 20px;">
                If you have any questions or need assistance, please don't hesitate to reach out to your administrator.
            </p>
        </div>
        
        <div class="footer">
            <p class="company-name">ClockWise</p>
            <p>This is an automated message. Please do not reply to this email.</p>
            <p style="margin-top: 15px;">&copy; 2026 ClockWise. All rights reserved.</p>
        </div>
    </div>
</body>
</html>`, fullName, organization, role, toEmail, password)

	msg := []byte(subject + mime + body)
	addr := s.host + ":" + s.port

	if err := smtp.SendMail(addr, auth, s.username, []string{toEmail}, msg); err != nil {
		return fmt.Errorf("failed to send email: %w", err)
	}

	return nil
}
