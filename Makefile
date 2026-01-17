.PHONY: help install install-backend install-frontend dev dev-back dev-front build test lint format check clean manual-test manual-test-stop

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

help:
	@echo "$(CYAN)Voice Lab - 開發指令$(RESET)"
	@echo ""
	@echo "$(GREEN)安裝指令:$(RESET)"
	@echo "  make install          - 安裝所有依賴（前後端）"
	@echo "  make install-backend  - 安裝後端依賴"
	@echo "  make install-frontend - 安裝前端依賴"
	@echo ""
	@echo "$(GREEN)開發指令:$(RESET)"
	@echo "  make dev              - 同時啟動前後端開發伺服器"
	@echo "  make dev-back         - 啟動後端開發伺服器 (port 8000)"
	@echo "  make dev-front        - 啟動前端開發伺服器 (port 5173)"
	@echo ""
	@echo "$(GREEN)建構指令:$(RESET)"
	@echo "  make build            - 建構前端產品版本"
	@echo ""
	@echo "$(GREEN)測試指令:$(RESET)"
	@echo "  make test             - 執行所有測試"
	@echo "  make test-back        - 執行後端測試"
	@echo "  make test-front       - 執行前端測試"
	@echo ""
	@echo "$(GREEN)程式碼品質:$(RESET)"
	@echo "  make lint             - 檢查程式碼風格"
	@echo "  make format           - 格式化程式碼"
	@echo "  make check            - 執行所有檢查（lint + typecheck）"
	@echo ""
	@echo "$(GREEN)手動測試:$(RESET)"
	@echo "  make manual-test      - 啟動手動測試環境（背景執行）"
	@echo "  make manual-test-stop - 停止手動測試環境"
	@echo ""
	@echo "$(GREEN)其他指令:$(RESET)"
	@echo "  make clean            - 清除建構產物"
	@echo "  make db-migrate       - 執行資料庫遷移"

# =============================================================================
# Installation
# =============================================================================

install: install-backend install-frontend
	@echo "$(GREEN)✓ 所有依賴安裝完成$(RESET)"

install-backend:
	@echo "$(CYAN)安裝後端依賴...$(RESET)"
	cd backend && uv sync --all-extras

install-frontend:
	@echo "$(CYAN)安裝前端依賴...$(RESET)"
	cd frontend && npm install

# =============================================================================
# Development
# =============================================================================

dev:
	@echo "$(CYAN)啟動開發伺服器...$(RESET)"
	@make -j2 dev-back dev-front

dev-back:
	@echo "$(CYAN)啟動後端伺服器 (http://localhost:8000)...$(RESET)"
	cd backend && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

dev-front:
	@echo "$(CYAN)啟動前端伺服器 (http://localhost:5173)...$(RESET)"
	cd frontend && npm run dev

# =============================================================================
# Build
# =============================================================================

build:
	@echo "$(CYAN)建構前端...$(RESET)"
	cd frontend && npm run build

# =============================================================================
# Testing
# =============================================================================

test: test-back test-front
	@echo "$(GREEN)✓ 所有測試完成$(RESET)"

test-back:
	@echo "$(CYAN)執行後端測試...$(RESET)"
	cd backend && pytest

test-front:
	@echo "$(CYAN)執行前端測試...$(RESET)"
	cd frontend && npm run test

test-cov:
	@echo "$(CYAN)執行測試並產生覆蓋率報告...$(RESET)"
	cd backend && pytest --cov=src --cov-report=html
	cd frontend && npm run test:coverage

# =============================================================================
# Code Quality
# =============================================================================

lint: lint-back lint-front
	@echo "$(GREEN)✓ 程式碼檢查完成$(RESET)"

lint-back:
	@echo "$(CYAN)檢查後端程式碼...$(RESET)"
	cd backend && ruff check src tests

lint-front:
	@echo "$(CYAN)檢查前端程式碼...$(RESET)"
	cd frontend && npm run lint

format: format-back format-front
	@echo "$(GREEN)✓ 程式碼格式化完成$(RESET)"

format-back:
	@echo "$(CYAN)格式化後端程式碼...$(RESET)"
	cd backend && ruff format src tests
	cd backend && ruff check --fix src tests

format-front:
	@echo "$(CYAN)格式化前端程式碼...$(RESET)"
	cd frontend && npm run lint:fix

check: lint typecheck
	@echo "$(GREEN)✓ 所有檢查完成$(RESET)"

typecheck:
	@echo "$(CYAN)執行型別檢查...$(RESET)"
	cd backend && mypy src
	cd frontend && npm run typecheck

# =============================================================================
# Database
# =============================================================================

db-migrate:
	@echo "$(CYAN)執行資料庫遷移...$(RESET)"
	cd backend && alembic upgrade head

db-revision:
	@echo "$(CYAN)建立新的資料庫遷移...$(RESET)"
	@read -p "遷移描述: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"

# =============================================================================
# Cleanup
# =============================================================================

clean:
	@echo "$(CYAN)清除建構產物...$(RESET)"
	rm -rf backend/.pytest_cache
	rm -rf backend/.mypy_cache
	rm -rf backend/.ruff_cache
	rm -rf backend/htmlcov
	rm -rf backend/.coverage
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.vite
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ 清除完成$(RESET)"

# =============================================================================
# Manual Testing
# =============================================================================

manual-test: manual-test-stop
	@echo "$(CYAN)啟動手動測試環境...$(RESET)"
	@cd backend && nohup uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/voice-lab_backend.log 2>&1 &
	@cd frontend && nohup npm run dev > /tmp/voice-lab_frontend.log 2>&1 &
	@sleep 4
	@echo "$(GREEN)=== Backend Health ===$(RESET)"
	@curl -s http://localhost:8000/health | head -100 || echo "Backend not responding"
	@echo ""
	@echo "$(GREEN)=== Frontend Status ===$(RESET)"
	@curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:5173 || echo "Frontend not responding"
	@echo ""
	@echo "$(GREEN)✓ 測試環境已啟動$(RESET)"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend logs:  tail -f /tmp/voice-lab_backend.log"
	@echo "  Frontend logs: tail -f /tmp/voice-lab_frontend.log"
	@open http://localhost:5173

manual-test-stop:
	@echo "$(CYAN)停止測試環境...$(RESET)"
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@lsof -ti:5173 | xargs kill -9 2>/dev/null || true
	@echo "$(GREEN)✓ 測試環境已停止$(RESET)"

# =============================================================================
# Docker (optional)
# =============================================================================

docker-build:
	@echo "$(CYAN)建構 Docker 映像...$(RESET)"
	docker-compose build

docker-up:
	@echo "$(CYAN)啟動 Docker 容器...$(RESET)"
	docker-compose up -d

docker-down:
	@echo "$(CYAN)停止 Docker 容器...$(RESET)"
	docker-compose down

docker-logs:
	docker-compose logs -f
