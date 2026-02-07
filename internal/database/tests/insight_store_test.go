package database

import (
	"fmt"
	"regexp"
	"testing"

	"github.com/DATA-DOG/go-sqlmock"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

func TestGetInsightsForAdmin(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := &database.PostgresInsightStore{DB: db, Logger: logger}

	orgID := uuid.New()

	// Regex patterns to match the multi-line queries defined in insight_store.go
	qNumEmployees := regexp.QuoteMeta(`SELECT COUNT(*) FROM users WHERE organization_id = $1 AND user_role != 'admin'`)
	qEmpPerRole := regexp.QuoteMeta(`SELECT user_role, COUNT(*) as count FROM users WHERE organization_id = $1 AND user_role != 'admin' GROUP BY user_role`)
	qAvgSalary := regexp.QuoteMeta(`SELECT COALESCE(AVG(salary_per_hour), 0) FROM users WHERE organization_id = $1 AND user_role != 'admin'`)
	qAvgSalaryRole := regexp.QuoteMeta(`SELECT user_role, COALESCE(AVG(salary_per_hour), 0) as avg_salary FROM users WHERE organization_id = $1 AND user_role != 'admin' GROUP BY user_role`)
	qNumTables := regexp.QuoteMeta(`SELECT COUNT(*) FROM tables WHERE organization_id = $1`)
	qMaxCapacity := regexp.QuoteMeta(`SELECT COALESCE(SUM(number_of_people), 0) FROM tables WHERE organization_id = $1`)
	qCurrPeople := regexp.QuoteMeta(`SELECT COALESCE(SUM(number_of_people), 0) FROM order_tables WHERE organization_id = $1 AND start_time <= $2 AND end_time >= $2`)
	qAvgOrders := `SELECT COALESCE\(AVG\(daily_count\), 0\) FROM .*`
	qOrdersToday := regexp.QuoteMeta(`SELECT COUNT(*) FROM orders WHERE organization_id = $1 AND DATE(create_time) = CURRENT_DATE`)
	qOrdersType := regexp.QuoteMeta(`SELECT order_type, COUNT(*) as count FROM orders WHERE organization_id = $1 GROUP BY order_type`)
	qRevenue := regexp.QuoteMeta(`SELECT COALESCE(SUM(i.price), 0) FROM orders o JOIN order_items oi ON o.id = oi.order_id JOIN items i ON oi.item_id = i.id WHERE o.organization_id = $1`)
	qShiftEmp := regexp.QuoteMeta(`SELECT u.user_role, COUNT(*) as count FROM users u JOIN schedules s ON u.id = s.employee_id WHERE u.organization_id = $1 AND (s.schedule_date + s.start_hour) <= $2 AND (s.schedule_date + s.end_hour) >= $2 GROUP BY u.user_role`)
	qMostSelling := regexp.QuoteMeta(`SELECT i.name, COUNT(oi.item_id) as sold_count FROM items i JOIN order_items oi ON i.id = oi.item_id JOIN orders o ON oi.order_id = o.id WHERE o.organization_id = $1 GROUP BY i.id, i.name ORDER BY sold_count DESC LIMIT 5`)

	t.Run("Success", func(t *testing.T) {
		// 1. Number of Employees (1 Item)
		mock.ExpectQuery(qNumEmployees).WithArgs(orgID).WillReturnRows(NewRow(10))

		// 2. Employees per Role (2 Items: server, chef)
		mock.ExpectQuery(qEmpPerRole).WithArgs(orgID).WillReturnRows(
			sqlmock.NewRows([]string{"user_role", "count"}).AddRow("server", 5).AddRow("chef", 5),
		)

		// 3. Average Salary (1 Item)
		mock.ExpectQuery(qAvgSalary).WithArgs(orgID).WillReturnRows(NewRow(25.50))

		// 4. Average Salary per Role (2 Items: server, chef)
		mock.ExpectQuery(qAvgSalaryRole).WithArgs(orgID).WillReturnRows(
			sqlmock.NewRows([]string{"user_role", "avg_salary"}).AddRow("server", 20.0).AddRow("chef", 30.0),
		)

		// 5. Number of Tables (1 Item)
		mock.ExpectQuery(qNumTables).WithArgs(orgID).WillReturnRows(NewRow(15))

		// 6. Max Capacity (1 Item)
		mock.ExpectQuery(qMaxCapacity).WithArgs(orgID).WillReturnRows(NewRow(60))

		// 7. Current People (1 Item)
		mock.ExpectQuery(qCurrPeople).WithArgs(orgID, sqlmock.AnyArg()).WillReturnRows(NewRow(20))

		// 8. Avg Orders per Day (1 Item)
		mock.ExpectQuery(qAvgOrders).WithArgs(orgID).WillReturnRows(NewRow(50.5))

		// 9. Orders Today (1 Item)
		mock.ExpectQuery(qOrdersToday).WithArgs(orgID).WillReturnRows(NewRow(12))

		// 10. Orders per Type (2 Items: dine in, delivery)
		mock.ExpectQuery(qOrdersType).WithArgs(orgID).WillReturnRows(
			sqlmock.NewRows([]string{"order_type", "count"}).AddRow("dine in", 8).AddRow("delivery", 4),
		)

		// 11. Total Revenue (1 Item)
		mock.ExpectQuery(qRevenue).WithArgs(orgID).WillReturnRows(NewRow(1500.75))

		// 12. Employees in Shift (1 Item: server)
		mock.ExpectQuery(qShiftEmp).WithArgs(orgID, sqlmock.AnyArg()).WillReturnRows(
			sqlmock.NewRows([]string{"user_role", "count"}).AddRow("server", 3),
		)

		// 13. Most Selling Items (1 Item)
		mock.ExpectQuery(qMostSelling).WithArgs(orgID).WillReturnRows(
			sqlmock.NewRows([]string{"name", "sold_count"}).AddRow("Burger", 100).AddRow("Fries", 90),
		)

		insights, err := store.GetInsightsForAdmin(orgID)

		assert.NoError(t, err)
		// Corrected calculation: 1 + 2 + 1 + 2 + 1 + 1 + 1 + 1 + 1 + 2 + 1 + 1 + 1 = 16 items
		assert.Len(t, insights, 16)

		assert.Equal(t, "Number of Employees", insights[0].Title)
		assert.Equal(t, "10", insights[0].Statistic)

		// Verify the LAST item is Most Selling Items (Index 15)
		lastIdx := len(insights) - 1
		assert.Equal(t, "Most Selling Items", insights[lastIdx].Title)
		assert.Contains(t, insights[lastIdx].Statistic, "1. Burger (100)")

		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectQuery(qNumEmployees).WithArgs(orgID).WillReturnError(fmt.Errorf("db connection error"))

		insights, err := store.GetInsightsForAdmin(orgID)

		assert.Error(t, err)
		assert.Nil(t, insights)
		AssertExpectations(t, mock)
	})
}

func TestGetInsightsForManager(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := &database.PostgresInsightStore{DB: db, Logger: logger}

	orgID := uuid.New()
	managerID := uuid.New()

	qManagerSalary := regexp.QuoteMeta(`SELECT COALESCE(salary_per_hour, 0) FROM users WHERE id = $1 AND organization_id = $2`)
	qEmpPerRole := regexp.QuoteMeta(`SELECT user_role, COUNT(*) as count FROM users WHERE organization_id = $1 AND user_role != 'admin' GROUP BY user_role`)
	qNumTables := regexp.QuoteMeta(`SELECT COUNT(*) FROM tables WHERE organization_id = $1`)
	qMaxCapacity := regexp.QuoteMeta(`SELECT COALESCE(SUM(number_of_people), 0) FROM tables WHERE organization_id = $1`)
	qCurrPeople := regexp.QuoteMeta(`SELECT COALESCE(SUM(number_of_people), 0) FROM order_tables WHERE organization_id = $1 AND start_time <= $2 AND end_time >= $2`)
	qOrdersToday := regexp.QuoteMeta(`SELECT COUNT(*) FROM orders WHERE organization_id = $1 AND DATE(create_time) = CURRENT_DATE`)
	qShiftEmp := regexp.QuoteMeta(`SELECT u.user_role, COUNT(*) as count FROM users u JOIN schedules s ON u.id = s.employee_id WHERE u.organization_id = $1 AND (s.schedule_date + s.start_hour) <= $2 AND (s.schedule_date + s.end_hour) >= $2 GROUP BY u.user_role`)
	qOrdersType := regexp.QuoteMeta(`SELECT order_type, COUNT(*) as count FROM orders WHERE organization_id = $1 GROUP BY order_type`)
	qDeliveries := regexp.QuoteMeta(`SELECT COUNT(*) FROM orders WHERE organization_id = $1 AND order_type = 'delivery' AND DATE(create_time) = CURRENT_DATE`)

	t.Run("Success", func(t *testing.T) {
		// 1. Manager Salary (1 Item)
		mock.ExpectQuery(qManagerSalary).WithArgs(managerID, orgID).WillReturnRows(NewRow(35.00))

		// 2. Emp Per Role (2 Items: staff, intern)
		mock.ExpectQuery(qEmpPerRole).WithArgs(orgID).WillReturnRows(
			sqlmock.NewRows([]string{"user_role", "count"}).AddRow("staff", 5).AddRow("intern", 2),
		)

		// 3. Tables (1 Item)
		mock.ExpectQuery(qNumTables).WithArgs(orgID).WillReturnRows(NewRow(10))

		// 4. Capacity (1 Item)
		mock.ExpectQuery(qMaxCapacity).WithArgs(orgID).WillReturnRows(NewRow(40))

		// 5. Current People (1 Item)
		mock.ExpectQuery(qCurrPeople).WithArgs(orgID, sqlmock.AnyArg()).WillReturnRows(NewRow(15))

		// 6. Orders Today (1 Item)
		mock.ExpectQuery(qOrdersToday).WithArgs(orgID).WillReturnRows(NewRow(5))

		// 7. Shift Emps (1 Item)
		mock.ExpectQuery(qShiftEmp).WithArgs(orgID, sqlmock.AnyArg()).WillReturnRows(
			sqlmock.NewRows([]string{"user_role", "count"}).AddRow("staff", 3),
		)

		// 8. Orders Type (1 Item)
		mock.ExpectQuery(qOrdersType).WithArgs(orgID).WillReturnRows(
			sqlmock.NewRows([]string{"order_type", "count"}).AddRow("takeaway", 2),
		)

		// 9. Deliveries (1 Item)
		mock.ExpectQuery(qDeliveries).WithArgs(orgID).WillReturnRows(NewRow(1))

		insights, err := store.GetInsightsForManager(orgID, managerID)

		assert.NoError(t, err)
		// Corrected calculation: 1 + 2 + 1 + 1 + 1 + 1 + 1 + 1 + 1 = 10 items
		assert.Len(t, insights, 10)
		assert.Equal(t, "Your Salary (per hour)", insights[0].Title)
		assert.Equal(t, "$35.00", insights[0].Statistic)

		AssertExpectations(t, mock)
	})
}

func TestGetInsightsForEmployee(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := &database.PostgresInsightStore{DB: db, Logger: logger}

	orgID := uuid.New()
	employeeID := uuid.New()

	qEmpSalary := regexp.QuoteMeta(`SELECT COALESCE(salary_per_hour, 0) FROM users WHERE id = $1 AND organization_id = $2`)
	qRole := regexp.QuoteMeta(`SELECT user_role FROM users WHERE id = $1 AND organization_id = $2`)
	qNumTables := regexp.QuoteMeta(`SELECT COUNT(*) FROM tables WHERE organization_id = $1`)
	qManagers := regexp.QuoteMeta(`SELECT u.full_name FROM users u JOIN schedules s ON u.id = s.employee_id WHERE u.organization_id = $1 AND u.user_role = 'manager' AND (s.schedule_date + s.start_hour) <= $2 AND (s.schedule_date + s.end_hour) >= $2`)
	qMaxCapacity := regexp.QuoteMeta(`SELECT COALESCE(SUM(number_of_people), 0) FROM tables WHERE organization_id = $1`)
	qCurrPeople := regexp.QuoteMeta(`SELECT COALESCE(SUM(number_of_people), 0) FROM order_tables WHERE organization_id = $1 AND start_time <= $2 AND end_time >= $2`)
	qOrdersToday := regexp.QuoteMeta(`SELECT COUNT(*) FROM orders WHERE organization_id = $1 AND DATE(create_time) = CURRENT_DATE`)
	qShiftEmp := regexp.QuoteMeta(`SELECT u.user_role, COUNT(*) as count FROM users u JOIN schedules s ON u.id = s.employee_id WHERE u.organization_id = $1 AND (s.schedule_date + s.start_hour) <= $2 AND (s.schedule_date + s.end_hour) >= $2 GROUP BY u.user_role`)
	qOrdersTypeToday := regexp.QuoteMeta(`SELECT order_type, COUNT(*) as count FROM orders WHERE organization_id = $1 AND DATE(create_time) = CURRENT_DATE GROUP BY order_type`)

	t.Run("Success", func(t *testing.T) {
		// 1. Salary (1 Item)
		mock.ExpectQuery(qEmpSalary).WithArgs(employeeID, orgID).WillReturnRows(NewRow(15.00))

		// 2. Role (1 Item)
		mock.ExpectQuery(qRole).WithArgs(employeeID, orgID).WillReturnRows(NewRow("server"))

		// 3. Tables (1 Item)
		mock.ExpectQuery(qNumTables).WithArgs(orgID).WillReturnRows(NewRow(10))

		// 4. Managers (1 Item - Aggregated string)
		mock.ExpectQuery(qManagers).WithArgs(orgID, sqlmock.AnyArg()).WillReturnRows(
			sqlmock.NewRows([]string{"full_name"}).AddRow("Manager Jane"),
		)

		// 5. Capacity (1 Item)
		mock.ExpectQuery(qMaxCapacity).WithArgs(orgID).WillReturnRows(NewRow(40))

		// 6. Current People (1 Item)
		mock.ExpectQuery(qCurrPeople).WithArgs(orgID, sqlmock.AnyArg()).WillReturnRows(NewRow(5))

		// 7. Orders Today (1 Item)
		mock.ExpectQuery(qOrdersToday).WithArgs(orgID).WillReturnRows(NewRow(20))

		// 8. Shift Emps (1 Item)
		mock.ExpectQuery(qShiftEmp).WithArgs(orgID, sqlmock.AnyArg()).WillReturnRows(
			sqlmock.NewRows([]string{"user_role", "count"}).AddRow("server", 2),
		)

		// 9. Orders Type Today (1 Item)
		mock.ExpectQuery(qOrdersTypeToday).WithArgs(orgID).WillReturnRows(
			sqlmock.NewRows([]string{"order_type", "count"}).AddRow("dine in", 5),
		)

		insights, err := store.GetInsightsForEmployee(orgID, employeeID)

		assert.NoError(t, err)
		assert.Len(t, insights, 9)
		assert.Equal(t, "Manager(s) on Shift", insights[3].Title)
		assert.Contains(t, insights[3].Statistic, "Manager Jane")

		AssertExpectations(t, mock)
	})

	t.Run("NoManagerOnShift", func(t *testing.T) {
		mock.ExpectQuery(qEmpSalary).WithArgs(employeeID, orgID).WillReturnRows(NewRow(15.00))
		mock.ExpectQuery(qRole).WithArgs(employeeID, orgID).WillReturnRows(NewRow("server"))
		mock.ExpectQuery(qNumTables).WithArgs(orgID).WillReturnRows(NewRow(10))

		// Manager query returns empty rows
		mock.ExpectQuery(qManagers).WithArgs(orgID, sqlmock.AnyArg()).WillReturnRows(sqlmock.NewRows([]string{"full_name"}))

		mock.ExpectQuery(qMaxCapacity).WithArgs(orgID).WillReturnRows(NewRow(0))
		mock.ExpectQuery(qCurrPeople).WithArgs(orgID, sqlmock.AnyArg()).WillReturnRows(NewRow(0))
		mock.ExpectQuery(qOrdersToday).WithArgs(orgID).WillReturnRows(NewRow(0))
		mock.ExpectQuery(qShiftEmp).WithArgs(orgID, sqlmock.AnyArg()).WillReturnRows(sqlmock.NewRows([]string{"user_role", "count"}))
		mock.ExpectQuery(qOrdersTypeToday).WithArgs(orgID).WillReturnRows(sqlmock.NewRows([]string{"order_type", "count"}))

		insights, err := store.GetInsightsForEmployee(orgID, employeeID)

		assert.NoError(t, err)
		assert.Equal(t, "Manager(s) on Shift", insights[3].Title)
		assert.Equal(t, "No manager on shift", insights[3].Statistic)
	})
}
