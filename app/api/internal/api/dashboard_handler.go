package api

// TODO Demand is auto generated every day and store in the database -> Background Tasks
import (
	"log/slog"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type DashboardHandler struct {
	DemandStore database.DemandStore
	Logger      *slog.Logger
}

func NewDashboardHandler(Logger *slog.Logger) *DashboardHandler {
	return &DashboardHandler{
		Logger: Logger,
	}
}

type DemandPredictionRequest struct {
	Place                Place             `json:"place"`
	Orders               database.Order    `json:"orders"`
	Campaigns            database.Campaign `json:"campaigns"`
	PredicationStartDate time.Time         `json:"prediction_start_date"`
	PredictionDays       *int              `json:"prediction_days,omitempty"`
}

type Place struct {
	ID                 uuid.UUID                 `json:"place_id"`
	Name               string                    `json:"name"`
	Address            string                    `json:"address"`
	Email              string                    `json:"email"`
	Type               string                    `json:"type"`
	Latitude           *float64                  `json:"latitude,omitempty"`
	Longitude          *float64                  `json:"longitude,omitempty"`
	WaitingTime        int                       `json:"waiting_time"`
	ReceivingPhone     bool                      `json:"receiving_phone"`
	Delivery           bool                      `json:"delivery"`
	OpeningHours       []database.OperatingHours `json:"opening_hours"`
	FixedShifts        bool                      `json:"fixed_shifts"`
	NumberShiftsPerDay int                       `json:"number_of_shifts_per_day"`
	ShiftTimes         []database.ShiftTime      `json:"shift_time"`
	Rating             *float64                  `json:"rating"`
	AcceptingOrders    bool                      `json:"accepting_orders"`
}

type DemandPredictResponse struct {
	RestaurantName string `json:"restaurant_name"`
	PredictionPerion string `json:"prediction_period"`
	Days []PredictionDay `json:"days"`
}

type PredictionDay struct {
	Day   string           `json:"day_name"`
	Date  time.Time        `json:"date"` // Only Date change time format
	Hours []PredictionHour `json:"hours"`
}

type PredictionHour struct {
	HourNo     int `json:"hour"`
	OrderCount int `json:"order_count"`
	ItemCount  int `json:"item_count"`
}

func (dh *DashboardHandler) GetDemandHeatMapHandler(c *gin.Context) {

}

func (dh *DashboardHandler) RefreshDemandHeatMapHandler(c *gin.Context) {

}
