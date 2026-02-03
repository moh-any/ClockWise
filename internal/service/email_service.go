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
        <html>
        <body>
            <h3>Hello %s,</h3>
            <p>You have been invited to join ClockWise as a <b>%s</b> in the organization <b>%s</b>.</p>
            <p>Here are your login credentials:</p>
            <ul>
                <li><b>Email:</b> %s</li>
                <li><b>Password:</b> %s</li>
            </ul>
            <p>Please login and change your password immediately.</p>
        </body>
        </html>`, fullName, role, organization, toEmail, password)

	msg := []byte(subject + mime + body)
	addr := s.host + ":" + s.port

	if err := smtp.SendMail(addr, auth, s.username, []string{toEmail}, msg); err != nil {
		return fmt.Errorf("failed to send email: %w", err)
	}

	return nil
}
