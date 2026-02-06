package database

import (
	"database/sql"
	"fmt"
	"log/slog"
	"time"

	"github.com/google/uuid"
)

type Insight struct {
	Title     string `json:"title"`
	Statistic string `json:"statistic"`
}

type InsightStore interface {
	GetInsightsForAdmin(org_id uuid.UUID) ([]Insight, error)
	GetInsightsForManager(org_id, manager_id uuid.UUID) ([]Insight, error)
	GetInsightsForEmployee(org_id, employee_id uuid.UUID) ([]Insight, error)
}

type PostgresInsightStore struct {
	DB     *sql.DB
	Logger *slog.Logger
}

// SQL Queries for Admin Insights
const (
	// Number of Employees in the organization
	queryNumberOfEmployees = `
		SELECT COUNT(*) 
		FROM users 
		WHERE organization_id = $1 AND user_role != 'admin'
	`

	// Number of employees for every role in the organization
	queryEmployeesPerRole = `
		SELECT user_role, COUNT(*) as count 
		FROM users 
		WHERE organization_id = $1 AND user_role != 'admin'
		GROUP BY user_role
	`

	// Average Employee Salaries
	queryAverageEmployeeSalary = `
		SELECT COALESCE(AVG(salary_per_hour), 0) 
		FROM users 
		WHERE organization_id = $1 AND user_role != 'admin'
	`

	// Average Employee Salaries per role
	queryAverageSalaryPerRole = `
		SELECT user_role, COALESCE(AVG(salary_per_hour), 0) as avg_salary 
		FROM users 
		WHERE organization_id = $1 AND user_role != 'admin'
		GROUP BY user_role
	`

	// Number of tables
	queryNumberOfTables = `
		SELECT COUNT(*) 
		FROM tables 
		WHERE organization_id = $1
	`

	// Max capacity (total number of people that can be served by tables)
	queryMaxTableCapacity = `
		SELECT COALESCE(SUM(number_of_people), 0)
		FROM tables
		WHERE organization_id = $1
	`

	// Number of people currently at tables
	queryCurrentPeopleAtTables = `
		SELECT COALESCE(SUM(number_of_people), 0)
		FROM order_tables
		WHERE organization_id = $1
		AND start_time <= $2
		AND end_time >= $2
	`

	// Average Orders per day
	queryAverageOrdersPerDay = `
		SELECT COALESCE(AVG(daily_count), 0)
		FROM (
			SELECT DATE(create_time) as order_date, COUNT(*) as daily_count
			FROM orders
			WHERE organization_id = $1
			GROUP BY DATE(create_time)
		) AS daily_orders
	`

	// Orders Served Today
	queryOrdersServedToday = `
		SELECT COUNT(*) 
		FROM orders 
		WHERE organization_id = $1 
		AND DATE(create_time) = CURRENT_DATE
	`

	// Total Revenue (sum of item prices for all orders)
	queryTotalRevenue = `
		SELECT COALESCE(SUM(i.price), 0)
		FROM orders o
		JOIN order_items oi ON o.id = oi.order_id
		JOIN items i ON oi.item_id = i.id
		WHERE o.organization_id = $1
	`

	// Number of employees for every role in the current shift
	queryEmployeesPerRoleCurrentShift = `
		SELECT u.user_role, COUNT(*) as count
		FROM users u
		JOIN schedules s ON u.id = s.employee_id
		WHERE u.organization_id = $1 
		AND (s.schedule_date + s.start_hour) <= $2 
		AND (s.schedule_date + s.end_hour) >= $2
		GROUP BY u.user_role
	`

	// Most Selling items (top 5)
	queryMostSellingItems = `
		SELECT i.name, COUNT(oi.item_id) as sold_count
		FROM items i
		JOIN order_items oi ON i.id = oi.item_id
		JOIN orders o ON oi.order_id = o.id
		WHERE o.organization_id = $1
		GROUP BY i.id, i.name
		ORDER BY sold_count DESC
		LIMIT 5
	`

	// Number of orders per type (dine in, delivery, takeaway)
	queryOrdersPerType = `
		SELECT order_type, COUNT(*) as count
		FROM orders
		WHERE organization_id = $1
		GROUP BY order_type
	`

	// Manager Salary
	queryManagerSalary = `
		SELECT COALESCE(salary_per_hour, 0)
		FROM users
		WHERE id = $1 AND organization_id = $2
	`

	// Number of deliveries today
	queryDeliveriesToday = `
		SELECT COUNT(*)
		FROM orders
		WHERE organization_id = $1
		AND order_type = 'delivery'
		AND DATE(create_time) = CURRENT_DATE
	`

	// Employee/User Role
	queryUserRole = `
		SELECT user_role
		FROM users
		WHERE id = $1 AND organization_id = $2
	`

	// Managers currently in shift
	queryManagersInCurrentShift = `
		SELECT u.full_name
		FROM users u
		JOIN schedules s ON u.id = s.employee_id
		WHERE u.organization_id = $1
		AND u.user_role = 'manager'
		AND (s.schedule_date + s.start_hour) <= $2
		AND (s.schedule_date + s.end_hour) >= $2
	`

	// Number of orders per type today
	queryOrdersPerTypeToday = `
		SELECT order_type, COUNT(*) as count
		FROM orders
		WHERE organization_id = $1
		AND DATE(create_time) = CURRENT_DATE
		GROUP BY order_type
	`
)

func (pgis *PostgresInsightStore) GetInsightsForAdmin(org_id uuid.UUID) ([]Insight, error) {
	/*
		Retrieved Insights
		- Number of Employees
		- Number of for Every Role in the organization
		- Average Employee Salaries
		- Average Employee Salaries per role
		- Number of tables
		- Number of people can be served by tables (Max)
		- Number of people currently at tables
		- Average Orders per day
		- Orders Served Today
		- Number of orders per type (dine in, delivery, takeaway)
		- Total Revenue
		- Number of employees for every role in the current shift
		- Most Selling items
	*/

	var insights []Insight

	// 1. Number of Employees
	var employeeCount int
	err := pgis.DB.QueryRow(queryNumberOfEmployees, org_id).Scan(&employeeCount)
	if err != nil {
		return nil, fmt.Errorf("failed to get employee count: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Number of Employees",
		Statistic: fmt.Sprintf("%d", employeeCount),
	})

	// 2. Number of employees for every role
	rows, err := pgis.DB.Query(queryEmployeesPerRole, org_id)
	if err != nil {
		return nil, fmt.Errorf("failed to get employees per role: %w", err)
	}
	defer rows.Close()
	for rows.Next() {
		var role string
		var count int
		if err := rows.Scan(&role, &count); err != nil {
			return nil, fmt.Errorf("failed to scan employees per role: %w", err)
		}
		insights = append(insights, Insight{
			Title:     fmt.Sprintf("Number of %ss", role),
			Statistic: fmt.Sprintf("%d", count),
		})
	}

	// 3. Average Employee Salary
	var avgSalary float64
	err = pgis.DB.QueryRow(queryAverageEmployeeSalary, org_id).Scan(&avgSalary)
	if err != nil {
		return nil, fmt.Errorf("failed to get average salary: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Average Employee Salary (per hour)",
		Statistic: fmt.Sprintf("$%.2f", avgSalary),
	})

	// 4. Average Salary per role
	rows, err = pgis.DB.Query(queryAverageSalaryPerRole, org_id)
	if err != nil {
		return nil, fmt.Errorf("failed to get average salary per role: %w", err)
	}
	defer rows.Close()
	for rows.Next() {
		var role string
		var avgRoleSalary float64
		if err := rows.Scan(&role, &avgRoleSalary); err != nil {
			return nil, fmt.Errorf("failed to scan average salary per role: %w", err)
		}
		insights = append(insights, Insight{
			Title:     fmt.Sprintf("Average %s Salary (per hour)", role),
			Statistic: fmt.Sprintf("$%.2f", avgRoleSalary),
		})
	}

	// 5. Number of Tables
	var tableCount int
	err = pgis.DB.QueryRow(queryNumberOfTables, org_id).Scan(&tableCount)
	if err != nil {
		return nil, fmt.Errorf("failed to get table count: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Number of Tables",
		Statistic: fmt.Sprintf("%d", tableCount),
	})

	// 6. Max Table Capacity
	var maxCapacity int
	err = pgis.DB.QueryRow(queryMaxTableCapacity, org_id).Scan(&maxCapacity)
	if err != nil {
		return nil, fmt.Errorf("failed to get max table capacity: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Max Table Capacity",
		Statistic: fmt.Sprintf("%d people", maxCapacity),
	})

	// 7. Current People at Tables
	currentTime := time.Now()
	var currentPeople int
	err = pgis.DB.QueryRow(queryCurrentPeopleAtTables, org_id, currentTime).Scan(&currentPeople)
	if err != nil {
		return nil, fmt.Errorf("failed to get current people at tables: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Current People at Tables",
		Statistic: fmt.Sprintf("%d people", currentPeople),
	})

	// 8. Average Orders per Day
	var avgOrders float64
	err = pgis.DB.QueryRow(queryAverageOrdersPerDay, org_id).Scan(&avgOrders)
	if err != nil {
		return nil, fmt.Errorf("failed to get average orders per day: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Average Orders per Day",
		Statistic: fmt.Sprintf("%.1f", avgOrders),
	})

	// 9. Orders Served Today
	var ordersToday int
	err = pgis.DB.QueryRow(queryOrdersServedToday, org_id).Scan(&ordersToday)
	if err != nil {
		return nil, fmt.Errorf("failed to get orders served today: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Orders Served Today",
		Statistic: fmt.Sprintf("%d", ordersToday),
	})

	// 10. Orders per Type (dine in, delivery, takeaway)
	rows, err = pgis.DB.Query(queryOrdersPerType, org_id)
	if err != nil {
		return nil, fmt.Errorf("failed to get orders per type: %w", err)
	}
	defer rows.Close()
	for rows.Next() {
		var orderType string
		var count int
		if err := rows.Scan(&orderType, &count); err != nil {
			return nil, fmt.Errorf("failed to scan orders per type: %w", err)
		}
		insights = append(insights, Insight{
			Title:     fmt.Sprintf("%s Orders", orderType),
			Statistic: fmt.Sprintf("%d", count),
		})
	}

	// 9. Total Revenue
	var totalRevenue float64
	err = pgis.DB.QueryRow(queryTotalRevenue, org_id).Scan(&totalRevenue)
	if err != nil {
		return nil, fmt.Errorf("failed to get total revenue: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Total Revenue",
		Statistic: fmt.Sprintf("$%.2f", totalRevenue),
	})

	// 12. Employees per role in current shift
	rows, err = pgis.DB.Query(queryEmployeesPerRoleCurrentShift, org_id, currentTime)

	if err != nil {
		return nil, fmt.Errorf("failed to get employees per role in current shift: %w", err)
	}
	defer rows.Close()

	for rows.Next() {
		var role string
		var count int
		if err := rows.Scan(&role, &count); err != nil {
			return nil, fmt.Errorf("failed to scan employees per role in current shift: %w", err)
		}
		insights = append(insights, Insight{
			Title:     fmt.Sprintf("Current Shift %ss", role),
			Statistic: fmt.Sprintf("%d", count),
		})
	}

	// 13. Most Selling Items
	rows, err = pgis.DB.Query(queryMostSellingItems, org_id)
	if err != nil {
		return nil, fmt.Errorf("failed to get most selling items: %w", err)
	}
	defer rows.Close()
	var topItems string
	rank := 1
	for rows.Next() {
		var itemName string
		var soldCount int
		if err := rows.Scan(&itemName, &soldCount); err != nil {
			return nil, fmt.Errorf("failed to scan most selling items: %w", err)
		}
		if topItems != "" {
			topItems += ", "
		}
		topItems += fmt.Sprintf("%d. %s (%d)", rank, itemName, soldCount)
		rank++
	}
	if topItems != "" {
		insights = append(insights, Insight{
			Title:     "Most Selling Items",
			Statistic: topItems,
		})
	}

	return insights, nil
}

func (pgis *PostgresInsightStore) GetInsightsForManager(org_id, manager_id uuid.UUID) ([]Insight, error) {
	/*
		- Manager Salary
		- Number of for Every Role in the organization
		- Number of tables
		- Number of people can be served by tables (Max)
		- Number of people currently at tables
		- Orders Served Today
		- Number of employees for every role in the current shift
		- Number of orders per type (dine in, delivery, takeaway)
		- Number of deliveries
	*/

	var insights []Insight

	// 1. Manager Salary
	var managerSalary float64
	err := pgis.DB.QueryRow(queryManagerSalary, manager_id, org_id).Scan(&managerSalary)
	if err != nil {
		return nil, fmt.Errorf("failed to get manager salary: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Your Salary (per hour)",
		Statistic: fmt.Sprintf("$%.2f", managerSalary),
	})

	// 2. Number of employees for every role
	rows, err := pgis.DB.Query(queryEmployeesPerRole, org_id)
	if err != nil {
		return nil, fmt.Errorf("failed to get employees per role: %w", err)
	}
	defer rows.Close()
	for rows.Next() {
		var role string
		var count int
		if err := rows.Scan(&role, &count); err != nil {
			return nil, fmt.Errorf("failed to scan employees per role: %w", err)
		}
		insights = append(insights, Insight{
			Title:     fmt.Sprintf("Number of %ss", role),
			Statistic: fmt.Sprintf("%d", count),
		})
	}

	// 3. Number of Tables
	var tableCount int
	err = pgis.DB.QueryRow(queryNumberOfTables, org_id).Scan(&tableCount)
	if err != nil {
		return nil, fmt.Errorf("failed to get table count: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Number of Tables",
		Statistic: fmt.Sprintf("%d", tableCount),
	})

	// 4. Max Table Capacity
	var maxCapacity int
	err = pgis.DB.QueryRow(queryMaxTableCapacity, org_id).Scan(&maxCapacity)
	if err != nil {
		return nil, fmt.Errorf("failed to get max table capacity: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Max Table Capacity",
		Statistic: fmt.Sprintf("%d people", maxCapacity),
	})

	// 5. Current People at Tables
	currentTime := time.Now()
	var currentPeople int
	err = pgis.DB.QueryRow(queryCurrentPeopleAtTables, org_id, currentTime).Scan(&currentPeople)
	if err != nil {
		return nil, fmt.Errorf("failed to get current people at tables: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Current People at Tables",
		Statistic: fmt.Sprintf("%d people", currentPeople),
	})

	// 6. Orders Served Today
	var ordersToday int
	err = pgis.DB.QueryRow(queryOrdersServedToday, org_id).Scan(&ordersToday)
	if err != nil {
		return nil, fmt.Errorf("failed to get orders served today: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Orders Served Today",
		Statistic: fmt.Sprintf("%d", ordersToday),
	})

	// 7. Employees per role in current shift
	rows, err = pgis.DB.Query(queryEmployeesPerRoleCurrentShift, org_id, currentTime)
	if err != nil {
		return nil, fmt.Errorf("failed to get employees per role in current shift: %w", err)
	}
	defer rows.Close()
	for rows.Next() {
		var role string
		var count int
		if err := rows.Scan(&role, &count); err != nil {
			return nil, fmt.Errorf("failed to scan employees per role in current shift: %w", err)
		}
		insights = append(insights, Insight{
			Title:     fmt.Sprintf("Current Shift %ss", role),
			Statistic: fmt.Sprintf("%d", count),
		})
	}

	// 8. Orders per Type (dine in, delivery, takeaway)
	rows, err = pgis.DB.Query(queryOrdersPerType, org_id)
	if err != nil {
		return nil, fmt.Errorf("failed to get orders per type: %w", err)
	}
	defer rows.Close()
	for rows.Next() {
		var orderType string
		var count int
		if err := rows.Scan(&orderType, &count); err != nil {
			return nil, fmt.Errorf("failed to scan orders per type: %w", err)
		}
		insights = append(insights, Insight{
			Title:     fmt.Sprintf("%s Orders", orderType),
			Statistic: fmt.Sprintf("%d", count),
		})
	}

	// 9. Number of Deliveries Today
	var deliveriesToday int
	err = pgis.DB.QueryRow(queryDeliveriesToday, org_id).Scan(&deliveriesToday)
	if err != nil {
		return nil, fmt.Errorf("failed to get deliveries today: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Deliveries Today",
		Statistic: fmt.Sprintf("%d", deliveriesToday),
	})

	return insights, nil
}

func (pgis *PostgresInsightStore) GetInsightsForEmployee(org_id, employee_id uuid.UUID) ([]Insight, error) {
	/*
		- Employee Salary
		- Employee Role
		- Number of tables
		- Manager Currently in Shift from schedules table
		- Number of people can be served by tables (Max)
		- Number of people currently at tables
		- Number of orders served today
		- Number of employees for every role in the current shift
		- Number of orders per type (dine in, delivery, takeaway) today
	*/

	var insights []Insight
	currentTime := time.Now()

	// 1. Employee Salary
	var employeeSalary float64
	err := pgis.DB.QueryRow(queryManagerSalary, employee_id, org_id).Scan(&employeeSalary)
	if err != nil {
		return nil, fmt.Errorf("failed to get employee salary: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Your Salary (per hour)",
		Statistic: fmt.Sprintf("$%.2f", employeeSalary),
	})

	// 2. Employee Role
	var employeeRole string
	err = pgis.DB.QueryRow(queryUserRole, employee_id, org_id).Scan(&employeeRole)
	if err != nil {
		return nil, fmt.Errorf("failed to get employee role: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Your Role",
		Statistic: employeeRole,
	})

	// 3. Number of Tables
	var tableCount int
	err = pgis.DB.QueryRow(queryNumberOfTables, org_id).Scan(&tableCount)
	if err != nil {
		return nil, fmt.Errorf("failed to get table count: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Number of Tables",
		Statistic: fmt.Sprintf("%d", tableCount),
	})

	// 4. Managers Currently in Shift
	rows, err := pgis.DB.Query(queryManagersInCurrentShift, org_id, currentTime)
	if err != nil {
		return nil, fmt.Errorf("failed to get managers in current shift: %w", err)
	}
	defer rows.Close()
	var managers string
	for rows.Next() {
		var managerName string
		if err := rows.Scan(&managerName); err != nil {
			return nil, fmt.Errorf("failed to scan manager name: %w", err)
		}
		if managers != "" {
			managers += ", "
		}
		managers += managerName
	}
	if managers == "" {
		managers = "No manager on shift"
	}
	insights = append(insights, Insight{
		Title:     "Manager(s) on Shift",
		Statistic: managers,
	})

	// 5. Max Table Capacity
	var maxCapacity int
	err = pgis.DB.QueryRow(queryMaxTableCapacity, org_id).Scan(&maxCapacity)
	if err != nil {
		return nil, fmt.Errorf("failed to get max table capacity: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Max Table Capacity",
		Statistic: fmt.Sprintf("%d people", maxCapacity),
	})

	// 6. Current People at Tables
	var currentPeople int
	err = pgis.DB.QueryRow(queryCurrentPeopleAtTables, org_id, currentTime).Scan(&currentPeople)
	if err != nil {
		return nil, fmt.Errorf("failed to get current people at tables: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Current People at Tables",
		Statistic: fmt.Sprintf("%d people", currentPeople),
	})

	// 7. Orders Served Today
	var ordersToday int
	err = pgis.DB.QueryRow(queryOrdersServedToday, org_id).Scan(&ordersToday)
	if err != nil {
		return nil, fmt.Errorf("failed to get orders served today: %w", err)
	}
	insights = append(insights, Insight{
		Title:     "Orders Served Today",
		Statistic: fmt.Sprintf("%d", ordersToday),
	})

	// 8. Employees per role in current shift
	rows, err = pgis.DB.Query(queryEmployeesPerRoleCurrentShift, org_id, currentTime)
	if err != nil {
		return nil, fmt.Errorf("failed to get employees per role in current shift: %w", err)
	}
	defer rows.Close()
	for rows.Next() {
		var role string
		var count int
		if err := rows.Scan(&role, &count); err != nil {
			return nil, fmt.Errorf("failed to scan employees per role in current shift: %w", err)
		}
		insights = append(insights, Insight{
			Title:     fmt.Sprintf("Current Shift %ss", role),
			Statistic: fmt.Sprintf("%d", count),
		})
	}

	// 9. Orders per Type Today
	rows, err = pgis.DB.Query(queryOrdersPerTypeToday, org_id)
	if err != nil {
		return nil, fmt.Errorf("failed to get orders per type today: %w", err)
	}
	defer rows.Close()
	for rows.Next() {
		var orderType string
		var count int
		if err := rows.Scan(&orderType, &count); err != nil {
			return nil, fmt.Errorf("failed to scan orders per type today: %w", err)
		}
		insights = append(insights, Insight{
			Title:     fmt.Sprintf("%s Orders Today", orderType),
			Statistic: fmt.Sprintf("%d", count),
		})
	}

	return insights, nil
}
