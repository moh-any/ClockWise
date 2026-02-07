package database

import (
	"database/sql"
	"fmt"
	"log/slog"

	"github.com/google/uuid"
)

type Campaign struct {
	ID              uuid.UUID `json:"id"`
	Name            string    `json:"name"`
	Status          string    `json:"status"`
	StartTime       string    `json:"start_time"`
	EndTime         string    `json:"end_time"`
	ItemsIncluded   []Item    `json:"items_included,omitempty"`
	DiscountPercent *float64  `json:"discount"`
}

type CampaignStore interface {
	StoreCampaign(org_id uuid.UUID, campaign Campaign) error
	StoreCampaignItems(org_id, campaign_id uuid.UUID, Items []Item) error
	GetAllCampaigns(org_id uuid.UUID) ([]Campaign, error)
	GetAllCampaignsFromLastWeek(org_ud uuid.UUID) ([]Campaign, error)
	GetCampaignInsights(org_id uuid.UUID) ([]Insight, error)
}

type PostgresCampaignStore struct {
	DB     *sql.DB
	Logger *slog.Logger
}

func NewPostgresCampaignStore(DB *sql.DB, Logger *slog.Logger) *PostgresCampaignStore {
	return &PostgresCampaignStore{
		DB:     DB,
		Logger: Logger,
	}
}

func (pgcs *PostgresCampaignStore) StoreCampaign(org_id uuid.UUID, campaign Campaign) error {
	tx, err := pgcs.DB.Begin()
	if err != nil {
		pgcs.Logger.Error("Failed to begin transaction", "error", err)
		return err
	}
	defer tx.Rollback()

	// Insert campaign
	query := `
		INSERT INTO marketing_campaigns (id, organization_id, name, status, start_time_date, end_time_date, discount_percent)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`
	campaignID := campaign.ID
	if campaignID == uuid.Nil {
		campaignID = uuid.New()
	}

	_, err = tx.Exec(query, campaignID, org_id, campaign.Name, campaign.Status, campaign.StartTime, campaign.EndTime, campaign.DiscountPercent)
	if err != nil {
		pgcs.Logger.Error("Failed to insert campaign", "error", err)
		return err
	}
	return tx.Commit()
}

func (pgcs *PostgresCampaignStore) StoreCampaignItems(org_id, campaign_id uuid.UUID, Items []Item) error {
	tx, err := pgcs.DB.Begin()
	if err != nil {
		pgcs.Logger.Error("Failed to begin transaction", "error", err)
		return err
	}
	defer tx.Rollback()

	// Check if campaign exists and belongs to the organization
	var exists bool
	err = tx.QueryRow(`
		SELECT EXISTS(SELECT 1 FROM marketing_campaigns WHERE id = $1 AND organization_id = $2)
	`, campaign_id, org_id).Scan(&exists)
	if err != nil {
		pgcs.Logger.Error("Failed to check campaign existence", "error", err)
		return err
	}
	if !exists {
		return fmt.Errorf("campaign not found or does not belong to organization")
	}

	// Add items to the campaign
	itemQuery := `INSERT INTO campaigns_items (campaign_id, item_id) VALUES ($1, $2) ON CONFLICT DO NOTHING`
	for _, item := range Items {
		_, err = tx.Exec(itemQuery, campaign_id, item.ItemID)
		if err != nil {
			pgcs.Logger.Error("Failed to insert campaign item", "error", err)
			return err
		}
	}

	return tx.Commit()
}

func (pgcs *PostgresCampaignStore) GetAllCampaigns(org_id uuid.UUID) ([]Campaign, error) {
	query := `
		SELECT id, name, status, start_time_date, end_time_date, discount_percent
		FROM marketing_campaigns
		WHERE organization_id = $1
		ORDER BY start_time_date DESC
	`

	rows, err := pgcs.DB.Query(query, org_id)
	if err != nil {
		pgcs.Logger.Error("Failed to query campaigns", "error", err)
		return nil, err
	}
	defer rows.Close()

	var campaigns []Campaign
	for rows.Next() {
		var c Campaign
		err := rows.Scan(&c.ID, &c.Name, &c.Status, &c.StartTime, &c.EndTime, &c.DiscountPercent)
		if err != nil {
			pgcs.Logger.Error("Failed to scan campaign", "error", err)
			return nil, err
		}

		// Fetch items for this campaign
		items, err := pgcs.getCampaignItems(c.ID)
		if err != nil {
			pgcs.Logger.Error("Failed to get campaign items", "error", err)
			return nil, err
		}
		c.ItemsIncluded = items

		campaigns = append(campaigns, c)
	}

	return campaigns, nil
}

func (pgcs *PostgresCampaignStore) GetAllCampaignsFromLastWeek(org_id uuid.UUID) ([]Campaign, error) {
	query := `
		SELECT id, name, status, start_time_date, end_time_date, discount_percent
		FROM marketing_campaigns
		WHERE organization_id = $1
		AND start_time_date >= NOW() - INTERVAL '7 days'
		ORDER BY start_time_date DESC
	`

	rows, err := pgcs.DB.Query(query, org_id)
	if err != nil {
		pgcs.Logger.Error("Failed to query campaigns from last week", "error", err)
		return nil, err
	}
	defer rows.Close()

	var campaigns []Campaign
	for rows.Next() {
		var c Campaign
		err := rows.Scan(&c.ID, &c.Name, &c.Status, &c.StartTime, &c.EndTime, &c.DiscountPercent)
		if err != nil {
			pgcs.Logger.Error("Failed to scan campaign", "error", err)
			return nil, err
		}

		// Fetch items for this campaign
		items, err := pgcs.getCampaignItems(c.ID)
		if err != nil {
			pgcs.Logger.Error("Failed to get campaign items", "error", err)
			return nil, err
		}
		c.ItemsIncluded = items

		campaigns = append(campaigns, c)
	}

	return campaigns, nil
}

func (pgcs *PostgresCampaignStore) GetCampaignInsights(org_id uuid.UUID) ([]Insight, error) {
	var insights []Insight

	// 1. Number of campaigns
	var numCampaigns int
	err := pgcs.DB.QueryRow(`
		SELECT COUNT(*) FROM marketing_campaigns WHERE organization_id = $1
	`, org_id).Scan(&numCampaigns)
	if err != nil {
		pgcs.Logger.Error("Failed to get campaign count", "error", err)
		return nil, err
	}
	insights = append(insights, Insight{
		Title:     "Total Campaigns",
		Statistic: fmt.Sprintf("%d", numCampaigns),
	})

	// 2. Longest Campaign (in days)
	var longestDays *float64
	err = pgcs.DB.QueryRow(`
		SELECT MAX(EXTRACT(EPOCH FROM (end_time_date - start_time_date)) / 86400)
		FROM marketing_campaigns
		WHERE organization_id = $1
	`, org_id).Scan(&longestDays)
	if err != nil {
		pgcs.Logger.Error("Failed to get longest campaign", "error", err)
		return nil, err
	}
	if longestDays != nil {
		insights = append(insights, Insight{
			Title:     "Longest Campaign (days)",
			Statistic: fmt.Sprintf("%.1f", *longestDays),
		})
	}

	// 3. Biggest Discount Ever
	var biggestDiscount *float64
	err = pgcs.DB.QueryRow(`
		SELECT MAX(discount_percent)
		FROM marketing_campaigns
		WHERE organization_id = $1
	`, org_id).Scan(&biggestDiscount)
	if err != nil {
		pgcs.Logger.Error("Failed to get biggest discount", "error", err)
		return nil, err
	}
	if biggestDiscount != nil {
		insights = append(insights, Insight{
			Title:     "Biggest Discount (%)",
			Statistic: fmt.Sprintf("%.2f%%", *biggestDiscount),
		})
	}

	// 4. Item that appeared most on campaigns
	var mostFrequentItem *string
	var itemCount *int
	err = pgcs.DB.QueryRow(`
		SELECT i.name, COUNT(ci.item_id) as appearance_count
		FROM campaigns_items ci
		JOIN items i ON ci.item_id = i.id
		JOIN marketing_campaigns mc ON ci.campaign_id = mc.id
		WHERE mc.organization_id = $1
		GROUP BY i.id, i.name
		ORDER BY appearance_count DESC
		LIMIT 1
	`, org_id).Scan(&mostFrequentItem, &itemCount)
	if err != nil && err.Error() != "sql: no rows in result set" {
		pgcs.Logger.Error("Failed to get most frequent item", "error", err)
		return nil, err
	}
	if mostFrequentItem != nil {
		insights = append(insights, Insight{
			Title:     "Most Featured Item",
			Statistic: *mostFrequentItem,
		})
	}

	return insights, nil
}

// getCampaignItems fetches all items associated with a campaign
func (pgcs *PostgresCampaignStore) getCampaignItems(campaignID uuid.UUID) ([]Item, error) {
	query := `
		SELECT i.id, i.name, i.needed_num_to_prepare, i.price
		FROM items i
		JOIN campaigns_items ci ON i.id = ci.item_id
		WHERE ci.campaign_id = $1
	`

	rows, err := pgcs.DB.Query(query, campaignID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var items []Item
	for rows.Next() {
		var item Item
		err := rows.Scan(&item.ItemID, &item.Name, &item.NeededNumEmployeesToPrepare, &item.Price)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}

	return items, nil
}
