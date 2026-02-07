package database

import (
	"fmt"
	"regexp"
	"testing"
	"time"

	"github.com/DATA-DOG/go-sqlmock"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

func TestStoreDemandHeatMap(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresDemandStore(db, logger)

	orgID := uuid.New()
	date := time.Date(2024, 6, 15, 0, 0, 0, 0, time.UTC)

	demand := database.DemandPredictResponse{
		RestaurantName:   "Test Restaurant",
		PredictionPerion: "2024-06-15 to 2024-06-16",
		Days: []database.PredictionDay{
			{
				Day:  "Saturday",
				Date: date,
				Hours: []database.PredictionHour{
					{HourNo: 10, OrderCount: 15, ItemCount: 45},
					{HourNo: 11, OrderCount: 20, ItemCount: 60},
				},
			},
		},
	}

	deleteQuery := regexp.QuoteMeta(`DELETE FROM demand WHERE organization_id = $1`)
	insertQuery := regexp.QuoteMeta(`INSERT INTO demand (organization_id, demand_date, day, hour, order_count, item_count) VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (organization_id, demand_date, day, hour) DO UPDATE SET order_count = EXCLUDED.order_count, item_count = EXCLUDED.item_count`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectBegin()
		mock.ExpectExec(deleteQuery).WithArgs(orgID).WillReturnResult(sqlmock.NewResult(0, 0))

		// Expect inserts for each hour in each day
		for _, day := range demand.Days {
			for _, hour := range day.Hours {
				mock.ExpectExec(insertQuery).
					WithArgs(orgID, day.Date, day.Day, hour.HourNo, hour.OrderCount, hour.ItemCount).
					WillReturnResult(sqlmock.NewResult(1, 1))
			}
		}

		mock.ExpectCommit()

		err := store.StoreDemandHeatMap(orgID, demand)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("TransactionRollbackOnInsertError", func(t *testing.T) {
		mock.ExpectBegin()
		mock.ExpectExec(deleteQuery).WithArgs(orgID).WillReturnResult(sqlmock.NewResult(0, 0))
		mock.ExpectExec(insertQuery).WillReturnError(fmt.Errorf("insert failed"))
		mock.ExpectRollback()

		err := store.StoreDemandHeatMap(orgID, demand)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("TransactionRollbackOnDeleteError", func(t *testing.T) {
		mock.ExpectBegin()
		mock.ExpectExec(deleteQuery).WithArgs(orgID).WillReturnError(fmt.Errorf("delete failed"))
		mock.ExpectRollback()

		err := store.StoreDemandHeatMap(orgID, demand)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}

func TestGetLatestDemandHeatMap(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresDemandStore(db, logger)

	orgID := uuid.New()

	query := regexp.QuoteMeta(`SELECT demand_date, day, hour, order_count, item_count FROM demand WHERE organization_id = $1 AND demand_date >= CURRENT_DATE AND demand_date < CURRENT_DATE + INTERVAL '7 days' ORDER BY demand_date, hour`)

	t.Run("Success", func(t *testing.T) {
		date1 := time.Date(2024, 6, 15, 0, 0, 0, 0, time.UTC)
		date2 := time.Date(2024, 6, 16, 0, 0, 0, 0, time.UTC)

		rows := sqlmock.NewRows([]string{"demand_date", "day", "hour", "order_count", "item_count"}).
			AddRow(date1, "Saturday", 10, 15, 45).
			AddRow(date1, "Saturday", 11, 20, 60).
			AddRow(date2, "Sunday", 10, 12, 36)

		mock.ExpectQuery(query).WithArgs(orgID).WillReturnRows(rows)

		result, err := store.GetLatestDemandHeatMap(orgID)
		assert.NoError(t, err)
		assert.NotNil(t, result)
		assert.Len(t, result.Days, 2)
		assert.Equal(t, "Saturday", result.Days[0].Day)
		assert.Len(t, result.Days[0].Hours, 2)
		assert.Equal(t, 15, result.Days[0].Hours[0].OrderCount)
		assert.Equal(t, "Sunday", result.Days[1].Day)
		assert.Len(t, result.Days[1].Hours, 1)
		AssertExpectations(t, mock)
	})

	t.Run("NoData", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"demand_date", "day", "hour", "order_count", "item_count"})
		mock.ExpectQuery(query).WithArgs(orgID).WillReturnRows(rows)

		result, err := store.GetLatestDemandHeatMap(orgID)
		assert.NoError(t, err)
		assert.Nil(t, result)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectQuery(query).WithArgs(orgID).WillReturnError(fmt.Errorf("db error"))

		result, err := store.GetLatestDemandHeatMap(orgID)
		assert.Error(t, err)
		assert.Nil(t, result)
		AssertExpectations(t, mock)
	})
}

func TestDeleteDemandByOrganization(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresDemandStore(db, logger)

	orgID := uuid.New()
	query := regexp.QuoteMeta(`DELETE FROM demand WHERE organization_id = $1`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(orgID).WillReturnResult(sqlmock.NewResult(0, 10))

		rowsAffected, err := store.DeleteDemandByOrganization(orgID)
		assert.NoError(t, err)
		assert.Equal(t, int64(10), rowsAffected)
		AssertExpectations(t, mock)
	})

	t.Run("NoData", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(orgID).WillReturnResult(sqlmock.NewResult(0, 0))

		rowsAffected, err := store.DeleteDemandByOrganization(orgID)
		assert.NoError(t, err)
		assert.Equal(t, int64(0), rowsAffected)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(orgID).WillReturnError(fmt.Errorf("db error"))

		rowsAffected, err := store.DeleteDemandByOrganization(orgID)
		assert.Error(t, err)
		assert.Equal(t, int64(0), rowsAffected)
		AssertExpectations(t, mock)
	})
}
