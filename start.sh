#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Track if any checks fail
ERRORS=0

echo "=========================================="
echo "Real-Time Stock Analysis - Startup Check"
echo "=========================================="
echo ""

# Check 1: Docker installation
echo "Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_success "Docker is installed: $DOCKER_VERSION"
else
    print_error "Docker is not installed. Please install Docker first."
    ERRORS=$((ERRORS + 1))
fi

# Check 2: Docker Compose installation
echo "Checking Docker Compose installation..."
COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    print_success "Docker Compose is installed: $COMPOSE_VERSION"
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_VERSION=$(docker compose version)
    print_success "Docker Compose (plugin) is installed: $COMPOSE_VERSION"
    COMPOSE_CMD="docker compose"
else
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    ERRORS=$((ERRORS + 1))
fi

# Check 3: Docker daemon is running
echo "Checking Docker daemon..."
if docker info &> /dev/null; then
    print_success "Docker daemon is running"
else
    print_error "Docker daemon is not running. Please start Docker."
    echo ""
    print_info "To start Docker:"
    echo "  - macOS: Open Docker Desktop from Applications"
    echo "  - Linux: sudo systemctl start docker"
    echo "  - Or run: open -a Docker (macOS)"
    echo ""
    # Try to start Docker on macOS if possible
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_info "Attempting to start Docker Desktop..."
        if open -a Docker &> /dev/null; then
            print_info "Docker Desktop launch command sent. Waiting 10 seconds..."
            sleep 10
            if docker info &> /dev/null; then
                print_success "Docker daemon is now running!"
            else
                print_warning "Docker Desktop is starting. Please wait a moment and run this script again."
                ERRORS=$((ERRORS + 1))
            fi
        else
            ERRORS=$((ERRORS + 1))
        fi
    else
        ERRORS=$((ERRORS + 1))
    fi
fi

echo ""
echo "Checking project structure..."

# Check 4: docker-compose.yml exists
if [ -f "docker-compose.yml" ]; then
    print_success "docker-compose.yml found"
else
    print_error "docker-compose.yml not found"
    ERRORS=$((ERRORS + 1))
fi

# Check 5: Analysis service files
echo "Checking analysis-service..."
ANALYSIS_FILES=("analysis-service/app.py" "analysis-service/Dockerfile" "analysis-service/requirements.txt" 
                "analysis-service/src/db.py" "analysis-service/src/dash_app.py" "analysis-service/src/indicators.py")
for file in "${ANALYSIS_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "  $file"
    else
        print_error "  $file is missing"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check 6: Price service files
echo "Checking price-service..."
PRICE_FILES=("price-service/app.py" "price-service/Dockerfile" "price-service/requirements.txt"
             "price-service/src/client.py" "price-service/src/schema.py" "price-service/src/log.py")
for file in "${PRICE_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "  $file"
    else
        print_error "  $file is missing"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check 7: Fundamentals service files
echo "Checking fundementals-service..."
FUNDAMENTALS_FILES=("fundementals-service/app.py" "fundementals-service/Dockerfile" "fundementals-service/requirements.txt"
                    "fundementals-service/src/client.py" "fundementals-service/src/schema.py" "fundementals-service/src/log.py")
for file in "${FUNDAMENTALS_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "  $file"
    else
        print_error "  $file is missing"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "Checking configuration..."

# Check 8: .env file
if [ -f ".env" ]; then
    print_success ".env file exists"
    # Check if TICKERS is set
    if grep -q "^TICKERS=" .env; then
        TICKERS=$(grep "^TICKERS=" .env | cut -d '=' -f2)
        if [ -n "$TICKERS" ] && [ "$TICKERS" != "" ]; then
            print_success "  TICKERS is set: $TICKERS"
        else
            print_warning "  TICKERS is empty in .env, adding default"
            echo "TICKERS=AAPL,MSFT,GOOGL" >> .env
            print_success "  Added TICKERS=AAPL,MSFT,GOOGL to .env"
        fi
    else
        print_warning "  TICKERS not found in .env, adding default"
        echo "TICKERS=AAPL,MSFT,GOOGL" >> .env
        print_success "  Added TICKERS=AAPL,MSFT,GOOGL to .env"
    fi
else
    print_warning ".env file not found"
    if [ -f ".env.example" ]; then
        print_info "Creating .env from .env.example..."
        cp .env.example .env
        print_success "Created .env file"
    else
        print_info "Creating default .env file..."
        echo "TICKERS=AAPL,MSFT,GOOGL" > .env
        print_success "Created default .env file with TICKERS=AAPL,MSFT,GOOGL"
    fi
fi

# Check 9: Port availability
echo ""
echo "Checking port availability..."
if lsof -Pi :8050 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    print_warning "Port 8050 is already in use. The dashboard may not be accessible."
else
    print_success "Port 8050 is available"
fi

if lsof -Pi :5432 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    print_warning "Port 5432 is already in use. There may be a conflict with the database."
    print_info "  If you have another Postgres instance running, you may need to stop it or change the port in docker-compose.yml"
else
    print_success "Port 5432 is available"
fi

# Summary
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    print_success "All checks passed!"
    echo ""
    echo "Starting services..."
    echo "=========================================="
    echo ""
    
    # Build and start containers
    $COMPOSE_CMD up --build -d
    
    if [ $? -eq 0 ]; then
        echo ""
        print_success "Services started successfully!"
        echo ""
        echo "Dashboard will be available at: http://localhost:8050"
        echo ""
        echo "To view logs, run: $COMPOSE_CMD logs -f"
        echo "To stop services, run: $COMPOSE_CMD down"
        echo ""
    else
        print_error "Failed to start services. Check the logs above for details."
        exit 1
    fi
else
    print_error "$ERRORS error(s) found. Please fix the issues above before starting."
    exit 1
fi

