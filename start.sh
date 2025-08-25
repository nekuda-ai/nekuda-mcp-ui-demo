#!/bin/bash

# MCP E-commerce Demo - Quick Start Script

set -e  # Exit on any error

echo "🚀 MCP E-commerce Demo - Quick Start"
echo "===================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${RED}❗ Please edit .env and add your OPENAI_API_KEY${NC}"
    echo -e "${CYAN}   Then run this script again.${NC}"
    exit 1
fi

# Check if OPENAI_API_KEY is set
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo -e "${RED}❗ Please set your OPENAI_API_KEY in .env file${NC}"
    echo -e "${CYAN}   Edit .env and replace 'your_openai_api_key_here' with your actual OpenAI API key${NC}"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❗ Node.js is required but not installed.${NC}"
    echo -e "${CYAN}   Please install Node.js 18+ from https://nodejs.org/${NC}"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}❗ Python is required but not installed.${NC}"
    echo -e "${CYAN}   Please install Python 3.8+ from https://python.org/${NC}"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"

# Install root dependencies (concurrently)
if [ ! -d "node_modules" ]; then
    echo "Installing root dependencies..."
    npm install
fi

# Install frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Create and activate virtual environment for backend
echo "Setting up backend virtual environment..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Installing backend dependencies..."
source venv/bin/activate
if [ ! -f ".deps_installed" ]; then
    pip install -r requirements.txt
    touch .deps_installed
fi
deactivate
cd ..

# Create and activate virtual environment for MCP server
echo "Setting up MCP server virtual environment..."
cd mcp-server
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Installing MCP server dependencies..."
source venv/bin/activate
if [ ! -f ".deps_installed" ]; then
    pip install -r requirements.txt
    touch .deps_installed
fi
deactivate
cd ..

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Start services
echo -e "${YELLOW}🌟 Starting all services...${NC}"
echo -e "${CYAN}   MCP Server: http://localhost:3003${NC}"
echo -e "${CYAN}   Backend API: http://localhost:8001${NC}" 
echo -e "${CYAN}   Frontend: http://localhost:5173${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Start all services with concurrently
npm run dev