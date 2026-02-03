package service

import (
	"encoding/csv"
	"errors"
	"log/slog"
	"mime/multipart"
)

var (
	ErrEmptyFile     = errors.New("csv file is empty")
	ErrInvalidFormat = errors.New("invalid csv format")
)

type CSVData struct {
	Headers []string            `json:"headers"`
	Rows    []map[string]string `json:"rows"`
	Total   int                 `json:"total"`
}

type UploadService interface {
	ParseCSV(file multipart.File) (*CSVData, error)
}

type CSVUploadService struct {
	Logger *slog.Logger
}

func NewCSVUploadService(logger *slog.Logger) *CSVUploadService {
	return &CSVUploadService{
		Logger: logger,
	}
}

// ParseCSV parses a CSV file from a multipart upload and returns structured data
func (s *CSVUploadService) ParseCSV(file multipart.File) (*CSVData, error) {
	csvReader := csv.NewReader(file)
	csvReader.TrimLeadingSpace = true
	
	records, err := csvReader.ReadAll()
	if err != nil {
		s.Logger.Error("failed to read csv", "error", err)
		return nil, ErrInvalidFormat
	}
	
	if len(records) == 0 {
		s.Logger.Warn("csv file is empty")
		return nil, ErrEmptyFile
	}
	
	headers := records[0]
	
	rows := make([]map[string]string, 0, len(records)-1)
	for i := 1; i < len(records); i++ {
		row := make(map[string]string)
		for j, header := range headers {
			if j < len(records[i]) {
				row[header] = records[i][j]
			} else {
				row[header] = "" // Handle missing values
			}
		}
		rows = append(rows, row)
	}
	
	s.Logger.Info("csv parsed successfully", "headers", headers, "row_count", len(rows))
	
	return &CSVData{
		Headers: headers,
		Rows:    rows,
		Total:   len(rows),
	}, nil
}
