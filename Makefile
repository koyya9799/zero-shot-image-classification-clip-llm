.PHONY: help install install-backend install-frontend setup env-setup status start start-backend start-frontend start-backend-bg start-frontend-bg start-all-bg dev clean kill-backend kill-all test test-backend test-frontend lint lint-backend lint-frontend add-classes check-backend check-frontend check-all logs logs-backend logs-frontend version build build-backend build-frontend docker-build

# Python executable path (use 'python' for portability - add to PATH)
PYTHON = python
NODE = node
NPM = npm

# Colors for output
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help:
	@echo "$(BLUE)=========================================$(NC)"
	@echo "$(BLUE)Zero-Shot Image Classification - Makefile$(NC)"
	@echo "$(BLUE)=========================================$(NC)"
	@echo ""
	@echo "$(GREEN)SETUP & INSTALLATION$(NC)"
	@echo "  make setup            - First-time setup (install all dependencies)"
	@echo "  make install          - Install dependencies for both backend and frontend"
	@echo "  make install-backend  - Install only backend dependencies"
	@echo "  make install-frontend - Install only frontend dependencies"
	@echo "  make env-setup        - Setup environment variables"
	@echo ""
	@echo "$(GREEN)DEVELOPMENT$(NC)"
	@echo "  make start            - Start both backend & frontend (recommended)"
	@echo "  make dev              - Alias for 'make start'"
	@echo "  make start-backend    - Start FastAPI backend (http://127.0.0.1:8000)"
	@echo "  make start-frontend   - Start Next.js frontend (http://localhost:3000)"
	@echo "  make start-backend-bg - Start backend in new window"
	@echo "  make start-frontend-bg- Start frontend in new window"
	@echo "  make start-all-bg     - Start both in separate windows"
	@echo ""
	@echo "$(GREEN)STATUS & MONITORING$(NC)"
	@echo "  make status           - Check status of both servers"
	@echo "  make check-backend    - Check backend health & classes"
	@echo "  make check-frontend   - Check frontend availability"
	@echo "  make check-all        - Check all services"
	@echo "  make logs             - Show recent activity from logs"
	@echo ""
	@echo "$(GREEN)TESTING & QUALITY$(NC)"
	@echo "  make test             - Run all tests"
	@echo "  make test-backend     - Test backend health endpoint"
	@echo "  make test-frontend    - Run frontend tests"
	@echo "  make lint             - Run linters on all code"
	@echo "  make lint-backend     - Lint backend Python code"
	@echo "  make lint-frontend    - Lint frontend TypeScript/React"
	@echo ""
	@echo "$(GREEN)DATA & CLASSES$(NC)"
	@echo "  make add-classes      - Add default classes to backend"
	@echo ""
	@echo "$(GREEN)BUILD & DEPLOYMENT$(NC)"
	@echo "  make build            - Build for production"
	@echo "  make build-backend    - Build backend with all optimizations"
	@echo "  make build-frontend   - Build Next.js production bundle"
	@echo "  make docker-build     - Build Docker images"
	@echo ""
	@echo "$(GREEN)MAINTENANCE$(NC)"
	@echo "  make kill-backend     - Kill Python backend processes"
	@echo "  make kill-all         - Kill all backend & frontend processes"
	@echo "  make clean            - Clean up cache and dependencies"
	@echo "  make version          - Show installed versions"
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make setup && make start   # First time setup"
	@echo "  make start-all-bg         # Run both servers in background"
	@echo "  make status               # Check if servers are running"
	@echo ""

setup: install env-setup add-classes
	@echo ""
	@echo "$(GREEN)Setup complete!$(NC)"
	@echo "Run 'make start' to start development servers"
	@echo ""

install: install-backend install-frontend
	@echo ""
	@echo "$(GREEN)✓ All dependencies installed!$(NC)"
	@echo ""

install-backend:
	@echo "$(YELLOW)Installing backend dependencies...$(NC)"
	cd backend && $(PYTHON) -m pip install --upgrade pip
	cd backend && $(PYTHON) -m pip install -r requirements.txt
	@echo "$(GREEN)✓ Backend dependencies installed!$(NC)"

install-frontend:
	@echo "$(YELLOW)Installing frontend dependencies...$(NC)"
	cd frontend && $(NPM) install
	@echo "$(GREEN)✓ Frontend dependencies installed!$(NC)"

env-setup:
	@echo "$(YELLOW)Setting up environment variables...$(NC)"
	@if not exist backend\.env (echo Creating backend/.env ...) else (echo backend/.env already exists)
	@if not exist backend\.env (copy backend\.env.example backend\.env 2>nul || echo "Note: Create backend/.env with your GEMINI_API_KEY")
	@echo "$(GREEN)✓ Environment setup complete$(NC)"
	@echo "Remember to add your GEMINI_API_KEY to backend/.env"
	@echo ""

start: 
	@echo "$(BLUE)=========================================$(NC)"
	@echo "$(BLUE)Starting Development Environment$(NC)"
	@echo "$(BLUE)=========================================$(NC)"
	@echo ""
	@echo "Backend:  $(GREEN)http://127.0.0.1:8000$(NC)"
	@echo "Frontend: $(GREEN)http://localhost:3000$(NC)"
	@echo "API Docs: $(GREEN)http://127.0.0.1:8000/docs$(NC)"
	@echo ""
	@echo "$(YELLOW)Note:$(NC) Start backend and frontend in separate terminals:"
	@echo "  Terminal 1: make start-backend"
	@echo "  Terminal 2: make start-frontend"
	@echo ""
	@echo "$(YELLOW)Or run in background:$(NC)"
	@echo "  make start-all-bg"
	@echo ""
	@echo "Press Ctrl+C to stop"
	@echo ""

start-backend:
	cd backend && $(PYTHON) -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

start-frontend:
	cd frontend && $(NPM) run dev

start-backend-bg:
	@echo "$(YELLOW)Starting backend in new window...$(NC)"
	@powershell -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd ''S:\Siddu\Final Year\zero-shot''; make start-backend'"
	@echo "$(GREEN)✓ Backend started in new window$(NC)"

start-frontend-bg:
	@echo "$(YELLOW)Starting frontend in new window...$(NC)"
	@powershell -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd ''S:\Siddu\Final Year\zero-shot''; make start-frontend'"
	@echo "$(GREEN)✓ Frontend started in new window$(NC)"

start-all-bg: start-backend-bg
	@powershell -Command "Start-Sleep -Seconds 3"
	@$(MAKE) start-frontend-bg
	@echo ""
	@echo "$(GREEN)✓ Both servers started in separate windows!$(NC)"
	@echo "Backend:  $(GREEN)http://127.0.0.1:8000$(NC)"
	@echo "Frontend: $(GREEN)http://localhost:3000$(NC)"
	@echo ""

dev: start

status: check-all

check-backend:
	@echo "$(YELLOW)Checking backend health...$(NC)"
	@powershell -Command "try { $$r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2; Write-Host 'Backend Status: $(GREEN)RUNNING$(NC) - '$$r.status -ForegroundColor Green; $$classes = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/classes'; Write-Host 'Classes Defined: '$$classes.classes.Count } catch { Write-Host 'Backend Status: $(RED)NOT RUNNING$(NC)' -ForegroundColor Red }"

check-frontend:
	@echo "$(YELLOW)Checking frontend availability...$(NC)"
	@powershell -Command "try { $$r = Invoke-RestMethod -Uri 'http://localhost:3000' -TimeoutSec 2 -Method Head; Write-Host 'Frontend Status: $(GREEN)RUNNING$(NC)' } catch { Write-Host 'Frontend Status: $(RED)NOT RUNNING$(NC)' -ForegroundColor Red }"

check-all: check-backend check-frontend
	@echo "$(GREEN)✓ Status check complete$(NC)"

test-backend:
	@echo "$(YELLOW)Testing backend health endpoint...$(NC)"
	@powershell -Command "try { $$r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health'; Write-Host 'Status: $(GREEN)'$$r.status'$(NC)' } catch { Write-Host 'Error: Backend not running or unreachable' -ForegroundColor Red }"

test-frontend:
	@echo "$(YELLOW)Running frontend tests...$(NC)"
	cd frontend && $(NPM) run test

test: test-backend test-frontend
	@echo "$(GREEN)✓ Tests complete$(NC)"

lint-backend:
	@echo "$(YELLOW)Linting backend Python code...$(NC)"
	cd backend && $(PYTHON) -m pylint app/ --disable=all --enable=E,F 2>&1 || true
	@echo "$(GREEN)✓ Backend linting complete$(NC)"

lint-frontend:
	@echo "$(YELLOW)Linting frontend TypeScript code...$(NC)"
	cd frontend && $(NPM) run lint || true
	@echo "$(GREEN)✓ Frontend linting complete$(NC)"

lint: lint-backend lint-frontend
	@echo "$(GREEN)✓ All linting complete$(NC)"

logs:
	@echo "$(YELLOW)Backend URLs:$(NC)"
	@echo "  Main API:  http://127.0.0.1:8000"
	@echo "  API Docs:  http://127.0.0.1:8000/docs"
	@echo ""
	@echo "$(YELLOW)Frontend URL:$(NC)"
	@echo "  App:       http://localhost:3000"
	@echo ""

logs-backend:
	@echo "$(YELLOW)Backend logs would be shown in terminal where 'make start-backend' runs$(NC)"

logs-frontend:
	@echo "$(YELLOW)Frontend logs would be shown in terminal where 'make start-frontend' runs$(NC)"

version:
	@echo "$(BLUE)Installed Versions:$(NC)"
	@echo -n "Python: " && $(PYTHON) --version
	@echo -n "Node.js: " && $(NODE) --version
	@echo -n "npm: " && $(NPM) --version
	@echo ""
	@echo "$(YELLOW)System Info:$(NC)"
	@powershell -Command "Write-Host 'OS: ' -NoNewline; [System.Environment]::OSVersion.VersionString"

add-classes:
	@echo "$(YELLOW)Classes management removed in optimization$(NC)"
	@echo "$(YELLOW)Define classes in your configuration files$(NC)"

build: build-backend build-frontend
	@echo ""
	@echo "$(GREEN)✓ Build complete!$(NC)"

build-backend:
	@echo "$(YELLOW)Building backend for production...$(NC)"
	@echo "Backend is ready to deploy (FastAPI is production-ready as-is)"
	@echo "$(GREEN)✓ Backend build complete$(NC)"

build-frontend:
	@echo "$(YELLOW)Building frontend for production...$(NC)"
	cd frontend && $(NPM) run build
	@echo "$(GREEN)✓ Frontend build complete$(NC)"

docker-build:
	@echo "$(YELLOW)Building Docker images...$(NC)"
	@if exist Dockerfile (docker build -t zero-shot:latest .) else (echo "Dockerfile not found. Create one to build Docker image.")
	@echo "$(GREEN)✓ Docker build complete$(NC)"

kill-backend:
	@echo "$(YELLOW)Killing backend processes...$(NC)"
	@taskkill /F /IM python.exe /T 2>nul || echo "No Python processes found"
	@taskkill /F /FI "WINDOWTITLE eq *uvicorn*" 2>nul || echo "No uvicorn processes found"
	@echo "$(GREEN)✓ Backend processes killed$(NC)"

kill-all: kill-backend
	@echo "$(YELLOW)Killing frontend processes...$(NC)"
	@taskkill /F /IM node.exe /T 2>nul || echo "No Node.js processes found"
	@echo "$(GREEN)✓ All processes killed$(NC)"

clean:
	@echo "$(YELLOW)Cleaning backend cache...$(NC)"
	@if exist backend\__pycache__ rd /s /q backend\__pycache__ 2>nul || true
	@if exist backend\app\__pycache__ rd /s /q backend\app\__pycache__ 2>nul || true
	@if exist backend\evaluation\__pycache__ rd /s /q backend\evaluation\__pycache__ 2>nul || true
	@del /s /q backend\*.pyc 2>nul || true
	@if exist backend\.pytest_cache rd /s /q backend\.pytest_cache 2>nul || true
	@echo "$(YELLOW)Cleaning frontend cache...$(NC)"
	@if exist frontend\.next rd /s /q frontend\.next 2>nul || true
	@if exist frontend\.swc rd /s /q frontend\.swc 2>nul || true
	@if exist frontend\node_modules rd /s /q frontend\node_modules 2>nul || true
	@del /s /q frontend\.eslintcache 2>nul || true
	@echo "$(GREEN)✓ Clean complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Optional: To reinstall dependencies after cleaning:$(NC)"
	@echo "  make install"
