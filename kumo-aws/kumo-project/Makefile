# Kumo ML Prediction Service Makefile
# Note: checkmake reports maxbodylength warnings for help/start/clean targets
# These are intentional - complex deployment tasks require multiple steps

.PHONY: all help start stop restart build clean train-models install setup-hooks test test-endpoint check-kumo start-api

# Default target
all: help

help:
	@echo "Kumo ML Prediction Service - Available Commands:"
	@echo ""
	@echo "  make install       - Install Python dependencies"
	@echo "  make train-models  - Train and save ML models"
	@echo "  make start         - Start Kumo and deploy the service"
	@echo "  make stop          - Stop Kumo and SAM API"
	@echo "  make restart       - Restart Kumo and redeploy"
	@echo "  make build         - Build SAM application"
	@echo "  make test-endpoint - Quick test of the prediction endpoint"
	@echo "  make clean         - Clean up everything"
	@echo ""

# Install dependencies
install:
	@echo "Installing dependencies..."
	uv pip install -r requirements.txt
	@echo "Done."

# Setup pre-commit hooks
setup-hooks:
	@echo "Setting up pre-commit hooks..."
	@uv tool install pre-commit
	@uv tool run pre-commit install
	@echo "Done."

# Train ML models
train-models:
	@echo "Training ML models..."
	@cd src && python train.py
	@echo "Done."

# Check Kumo health
check-kumo:
	@echo "Checking Kumo status..."
	@nc -z localhost 4566 2>/dev/null || \
		(echo "Starting Kumo..." && docker-compose up -d && sleep 5)
	@echo "Kumo is running."

# Build SAM application
build: train-models
	@echo "Building SAM application..."
	@sam build --use-container
	@echo "Build complete."

# Start SAM local API
start-api:
	@echo "Starting SAM local API..."
	@pkill -f "sam local start-api" 2>/dev/null || true
	@export AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 && \
		sam local start-api --warm-containers EAGER > sam_api.log 2>&1 &
	@echo "Waiting for API to be ready..."
	@for i in {1..30}; do \
		curl -s http://127.0.0.1:3000/predict > /dev/null 2>&1 && break || sleep 1; \
	done
	@echo "API is ready at http://127.0.0.1:3000"

# Full deployment
start: check-kumo build start-api test-endpoint
	@echo ""
	@echo "Service is running!"
	@PID=$$(ps aux | grep '[s]am local start-api' | awk '{print $$2}' | head -1); \
	if [ -n "$$PID" ]; then \
		echo "  PID: $$PID"; \
		echo ""; \
		echo "  Endpoint: http://127.0.0.1:3000/predict"; \
		echo ""; \
		echo "To stop: make stop (or kill $$PID)"; \
	fi

# Stop services
stop:
	@echo "Stopping services..."
	@pkill -f "sam local start-api" || true
	@docker-compose down
	@echo "Done."

# Restart everything
restart: stop start

# Run tests
test: test-endpoint

# Quick test endpoint
test-endpoint:
	@echo "Testing prediction endpoint..."
	@curl -s -X POST "http://127.0.0.1:3000/predict" \
		-H "Content-Type: application/json" \
		-d '{"features": [1.0, 2.0, 3.0, 4.0]}' | jq . 2>/dev/null || \
		curl -s -X POST "http://127.0.0.1:3000/predict" \
		-H "Content-Type: application/json" \
		-d '{"features": [1.0, 2.0, 3.0, 4.0]}'
	@echo ""
	@echo "Done."

# Clean up
clean:
	@echo "Cleaning up..."
	@pkill -f "sam local start-api" || true
	@docker-compose down -v
	@rm -rf .aws-sam sam_api.log
	@rm -f src/*.pkl
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Done."