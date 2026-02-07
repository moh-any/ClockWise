package database

import (
	"database/sql"
	"fmt"
	"regexp"
	"testing"

	"github.com/DATA-DOG/go-sqlmock"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

func TestStoreAlert(t *testing.T) {
	db, _ := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresAlertStore(db, logger)

	orgID := uuid.New()
	alert := &database.Alert{
		Id:           uuid.New(),
		Organization: orgID,
		Severity:     "critical",
		Subject:      "Test Alert",
		Message:      "Test message",
	}

	t.Run("NoOp", func(t *testing.T) {
		// StoreAlert is a no-op, should always return nil
		err := store.StoreAlert(orgID, alert)
		assert.NoError(t, err)
	})
}

func TestGetAllAlerts(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresAlertStore(db, logger)

	orgID := uuid.New()
	alertID1 := uuid.New()
	alertID2 := uuid.New()

	query := regexp.QuoteMeta(`SELECT id, organization_id, severity, subject, message FROM alerts WHERE organization_id = $1 ORDER BY id DESC`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"id", "organization_id", "severity", "subject", "message"}).
			AddRow(alertID2, orgID, "high", "Alert 2", "Message 2").
			AddRow(alertID1, orgID, "critical", "Alert 1", "Message 1")

		mock.ExpectQuery(query).WithArgs(orgID).WillReturnRows(rows)

		alerts, err := store.GetAllAlerts(orgID)
		assert.NoError(t, err)
		assert.Len(t, alerts, 2)
		assert.Equal(t, alertID2, alerts[0].Id)
		assert.Equal(t, "high", alerts[0].Severity)
		assert.Equal(t, alertID1, alerts[1].Id)
		assert.Equal(t, "critical", alerts[1].Severity)
		AssertExpectations(t, mock)
	})

	t.Run("EmptyResult", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"id", "organization_id", "severity", "subject", "message"})
		mock.ExpectQuery(query).WithArgs(orgID).WillReturnRows(rows)

		alerts, err := store.GetAllAlerts(orgID)
		assert.NoError(t, err)
		assert.Nil(t, alerts)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectQuery(query).WithArgs(orgID).WillReturnError(fmt.Errorf("db error"))

		alerts, err := store.GetAllAlerts(orgID)
		assert.Error(t, err)
		assert.Nil(t, alerts)
		AssertExpectations(t, mock)
	})
}

func TestGetAllAlertsForLastWeek(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresAlertStore(db, logger)

	orgID := uuid.New()
	alertID := uuid.New()

	// The query is complex with subqueries; use a regex pattern to match
	query := `SELECT id, organization_id, severity, subject, message\s+FROM alerts\s+WHERE organization_id = \$1`

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"id", "organization_id", "severity", "subject", "message"}).
			AddRow(alertID, orgID, "moderate", "Weekly Alert", "Recent alert")

		mock.ExpectQuery(query).WithArgs(orgID).WillReturnRows(rows)

		alerts, err := store.GetAllAlertsForLastWeek(orgID)
		assert.NoError(t, err)
		assert.Len(t, alerts, 1)
		assert.Equal(t, alertID, alerts[0].Id)
		assert.Equal(t, "moderate", alerts[0].Severity)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectQuery(query).WithArgs(orgID).WillReturnError(fmt.Errorf("db error"))

		alerts, err := store.GetAllAlertsForLastWeek(orgID)
		assert.Error(t, err)
		assert.Nil(t, alerts)
		AssertExpectations(t, mock)
	})
}

func TestGetAlertInsights(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresAlertStore(db, logger)

	orgID := uuid.New()

	qTotal := regexp.QuoteMeta(`SELECT COUNT(*) FROM alerts WHERE organization_id = $1`)
	qCritical := regexp.QuoteMeta(`SELECT COUNT(*) FROM alerts WHERE organization_id = $1 AND severity = 'critical'`)
	qHigh := regexp.QuoteMeta(`SELECT COUNT(*) FROM alerts WHERE organization_id = $1 AND severity = 'high'`)
	qMostCommon := `SELECT severity\s+FROM alerts\s+WHERE organization_id = \$1`

	t.Run("Success", func(t *testing.T) {
		mock.ExpectQuery(qTotal).WithArgs(orgID).WillReturnRows(NewRow(25))
		mock.ExpectQuery(qCritical).WithArgs(orgID).WillReturnRows(NewRow(5))
		mock.ExpectQuery(qHigh).WithArgs(orgID).WillReturnRows(NewRow(10))
		mock.ExpectQuery(qMostCommon).WithArgs(orgID).WillReturnRows(NewRow("high"))

		insights, err := store.GetAlertInsights(orgID)
		assert.NoError(t, err)
		assert.Len(t, insights, 4)

		assert.Equal(t, "Total Alerts", insights[0].Title)
		assert.Equal(t, "25", insights[0].Statistic)

		assert.Equal(t, "Critical Alerts", insights[1].Title)
		assert.Equal(t, "5", insights[1].Statistic)

		assert.Equal(t, "High Severity Alerts", insights[2].Title)
		assert.Equal(t, "10", insights[2].Statistic)

		assert.Equal(t, "Most Common Severity", insights[3].Title)
		assert.Equal(t, "high", insights[3].Statistic)

		AssertExpectations(t, mock)
	})

	t.Run("NoAlerts_MostCommonReturnsNA", func(t *testing.T) {
		mock.ExpectQuery(qTotal).WithArgs(orgID).WillReturnRows(NewRow(0))
		mock.ExpectQuery(qCritical).WithArgs(orgID).WillReturnRows(NewRow(0))
		mock.ExpectQuery(qHigh).WithArgs(orgID).WillReturnRows(NewRow(0))
		mock.ExpectQuery(qMostCommon).WithArgs(orgID).WillReturnError(sql.ErrNoRows)

		insights, err := store.GetAlertInsights(orgID)
		assert.NoError(t, err)
		assert.Len(t, insights, 4)
		assert.Equal(t, "N/A", insights[3].Statistic)

		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectQuery(qTotal).WithArgs(orgID).WillReturnError(fmt.Errorf("db error"))

		insights, err := store.GetAlertInsights(orgID)
		assert.Error(t, err)
		assert.Nil(t, insights)
		AssertExpectations(t, mock)
	})
}
