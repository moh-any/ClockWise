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

func TestStoreCampaign(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresCampaignStore(db, logger)

	orgID := uuid.New()
	campaignID := uuid.New()
	campaign := database.Campaign{
		ID:              campaignID,
		Name:            "Summer Sale",
		Status:          "active",
		StartTime:       "2024-06-01",
		EndTime:         "2024-06-30",
		DiscountPercent: func() *float64 { f := 15.0; return &f }(),
	}

	query := regexp.QuoteMeta(`INSERT INTO marketing_campaigns (id, organization_id, name, status, start_time_date, end_time_date, discount_percent) VALUES ($1, $2, $3, $4, $5, $6, $7)`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectBegin()
		mock.ExpectExec(query).
			WithArgs(campaignID, orgID, campaign.Name, campaign.Status, campaign.StartTime, campaign.EndTime, campaign.DiscountPercent).
			WillReturnResult(sqlmock.NewResult(1, 1))
		mock.ExpectCommit()

		err := store.StoreCampaign(orgID, campaign)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectBegin()
		mock.ExpectExec(query).WillReturnError(fmt.Errorf("insert failed"))
		mock.ExpectRollback()

		err := store.StoreCampaign(orgID, campaign)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}

func TestStoreCampaignItems(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresCampaignStore(db, logger)

	orgID := uuid.New()
	campaignID := uuid.New()
	itemID1 := uuid.New()
	itemID2 := uuid.New()

	items := []database.Item{
		{ItemID: itemID1, Name: "Burger"},
		{ItemID: itemID2, Name: "Fries"},
	}

	qExists := regexp.QuoteMeta(`SELECT EXISTS(SELECT 1 FROM marketing_campaigns WHERE id = $1 AND organization_id = $2)`)
	qInsert := regexp.QuoteMeta(`INSERT INTO campaigns_items (campaign_id, item_id) VALUES ($1, $2) ON CONFLICT DO NOTHING`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectBegin()
		mock.ExpectQuery(qExists).WithArgs(campaignID, orgID).WillReturnRows(NewRow(true))

		for _, item := range items {
			mock.ExpectExec(qInsert).WithArgs(campaignID, item.ItemID).WillReturnResult(sqlmock.NewResult(1, 1))
		}
		mock.ExpectCommit()

		err := store.StoreCampaignItems(orgID, campaignID, items)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("CampaignNotFound", func(t *testing.T) {
		mock.ExpectBegin()
		mock.ExpectQuery(qExists).WithArgs(campaignID, orgID).WillReturnRows(NewRow(false))
		mock.ExpectRollback()

		err := store.StoreCampaignItems(orgID, campaignID, items)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "campaign not found")
		AssertExpectations(t, mock)
	})
}

func TestGetAllCampaigns(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresCampaignStore(db, logger)

	orgID := uuid.New()
	campaignID := uuid.New()

	qCampaigns := regexp.QuoteMeta(`SELECT id, name, status, start_time_date, end_time_date, discount_percent FROM marketing_campaigns WHERE organization_id = $1 ORDER BY start_time_date DESC`)
	qItems := regexp.QuoteMeta(`SELECT i.id, i.name, i.needed_num_to_prepare, i.price FROM items i JOIN campaigns_items ci ON i.id = ci.item_id WHERE ci.campaign_id = $1`)

	t.Run("Success", func(t *testing.T) {
		campaignRows := sqlmock.NewRows([]string{"id", "name", "status", "start_time_date", "end_time_date", "discount_percent"}).
			AddRow(campaignID, "Summer Sale", "active", "2024-06-01", "2024-06-30", 15.0)
		mock.ExpectQuery(qCampaigns).WithArgs(orgID).WillReturnRows(campaignRows)

		// Items for this campaign
		itemRows := sqlmock.NewRows([]string{"id", "name", "needed_num_to_prepare", "price"}).
			AddRow(uuid.New(), "Burger", 2, 10.0)
		mock.ExpectQuery(qItems).WithArgs(campaignID).WillReturnRows(itemRows)

		campaigns, err := store.GetAllCampaigns(orgID)
		assert.NoError(t, err)
		assert.Len(t, campaigns, 1)
		assert.Equal(t, "Summer Sale", campaigns[0].Name)
		assert.Len(t, campaigns[0].ItemsIncluded, 1)
		assert.Equal(t, "Burger", campaigns[0].ItemsIncluded[0].Name)
		AssertExpectations(t, mock)
	})

	t.Run("EmptyResult", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"id", "name", "status", "start_time_date", "end_time_date", "discount_percent"})
		mock.ExpectQuery(qCampaigns).WithArgs(orgID).WillReturnRows(rows)

		campaigns, err := store.GetAllCampaigns(orgID)
		assert.NoError(t, err)
		assert.Nil(t, campaigns)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectQuery(qCampaigns).WithArgs(orgID).WillReturnError(fmt.Errorf("db error"))

		campaigns, err := store.GetAllCampaigns(orgID)
		assert.Error(t, err)
		assert.Nil(t, campaigns)
		AssertExpectations(t, mock)
	})
}

func TestGetAllCampaignsFromLastWeek(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresCampaignStore(db, logger)

	orgID := uuid.New()
	campaignID := uuid.New()

	qCampaigns := regexp.QuoteMeta(`SELECT id, name, status, start_time_date, end_time_date, discount_percent FROM marketing_campaigns WHERE organization_id = $1 AND start_time_date >= NOW() - INTERVAL '7 days' ORDER BY start_time_date DESC`)
	qItems := regexp.QuoteMeta(`SELECT i.id, i.name, i.needed_num_to_prepare, i.price FROM items i JOIN campaigns_items ci ON i.id = ci.item_id WHERE ci.campaign_id = $1`)

	t.Run("Success", func(t *testing.T) {
		campaignRows := sqlmock.NewRows([]string{"id", "name", "status", "start_time_date", "end_time_date", "discount_percent"}).
			AddRow(campaignID, "Flash Sale", "active", "2024-06-28", "2024-06-30", 20.0)
		mock.ExpectQuery(qCampaigns).WithArgs(orgID).WillReturnRows(campaignRows)

		itemRows := sqlmock.NewRows([]string{"id", "name", "needed_num_to_prepare", "price"})
		mock.ExpectQuery(qItems).WithArgs(campaignID).WillReturnRows(itemRows)

		campaigns, err := store.GetAllCampaignsFromLastWeek(orgID)
		assert.NoError(t, err)
		assert.Len(t, campaigns, 1)
		assert.Equal(t, "Flash Sale", campaigns[0].Name)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectQuery(qCampaigns).WithArgs(orgID).WillReturnError(fmt.Errorf("db error"))

		campaigns, err := store.GetAllCampaignsFromLastWeek(orgID)
		assert.Error(t, err)
		assert.Nil(t, campaigns)
		AssertExpectations(t, mock)
	})
}

func TestGetCampaignInsights(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresCampaignStore(db, logger)

	orgID := uuid.New()

	qCount := regexp.QuoteMeta(`SELECT COUNT(*) FROM marketing_campaigns WHERE organization_id = $1`)
	qLongest := `SELECT MAX\(EXTRACT\(EPOCH FROM \(end_time_date - start_time_date\)\) / 86400\)\s+FROM marketing_campaigns\s+WHERE organization_id = \$1`
	qBiggest := `SELECT MAX\(discount_percent\)\s+FROM marketing_campaigns\s+WHERE organization_id = \$1`
	qMostFeatured := `SELECT i\.name, COUNT\(ci\.item_id\) as appearance_count`

	t.Run("Success", func(t *testing.T) {
		mock.ExpectQuery(qCount).WithArgs(orgID).WillReturnRows(NewRow(10))

		mock.ExpectQuery(qLongest).WithArgs(orgID).WillReturnRows(
			sqlmock.NewRows([]string{"max"}).AddRow(30.0),
		)

		mock.ExpectQuery(qBiggest).WithArgs(orgID).WillReturnRows(
			sqlmock.NewRows([]string{"max"}).AddRow(25.0),
		)

		mock.ExpectQuery(qMostFeatured).WithArgs(orgID).WillReturnRows(
			sqlmock.NewRows([]string{"name", "appearance_count"}).AddRow("Burger", 5),
		)

		insights, err := store.GetCampaignInsights(orgID)
		assert.NoError(t, err)
		assert.Len(t, insights, 4)

		assert.Equal(t, "Total Campaigns", insights[0].Title)
		assert.Equal(t, "10", insights[0].Statistic)

		assert.Equal(t, "Longest Campaign (days)", insights[1].Title)
		assert.Equal(t, "30.0", insights[1].Statistic)

		assert.Equal(t, "Biggest Discount (%)", insights[2].Title)
		assert.Contains(t, insights[2].Statistic, "25.00%")

		assert.Equal(t, "Most Featured Item", insights[3].Title)
		assert.Equal(t, "Burger", insights[3].Statistic)

		AssertExpectations(t, mock)
	})

	t.Run("NoCampaigns_NullValues", func(t *testing.T) {
		mock.ExpectQuery(qCount).WithArgs(orgID).WillReturnRows(NewRow(0))

		mock.ExpectQuery(qLongest).WithArgs(orgID).WillReturnRows(
			sqlmock.NewRows([]string{"max"}).AddRow(nil),
		)

		mock.ExpectQuery(qBiggest).WithArgs(orgID).WillReturnRows(
			sqlmock.NewRows([]string{"max"}).AddRow(nil),
		)

		mock.ExpectQuery(qMostFeatured).WithArgs(orgID).WillReturnError(sql.ErrNoRows)

		insights, err := store.GetCampaignInsights(orgID)
		assert.NoError(t, err)
		// Only Total Campaigns should be present (longest, biggest, most featured are nil/empty)
		assert.Equal(t, "Total Campaigns", insights[0].Title)
		assert.Equal(t, "0", insights[0].Statistic)

		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectQuery(qCount).WithArgs(orgID).WillReturnError(fmt.Errorf("db error"))

		insights, err := store.GetCampaignInsights(orgID)
		assert.Error(t, err)
		assert.Nil(t, insights)
		AssertExpectations(t, mock)
	})
}
