#!/bin/bash

# Manual setup script for users who want to manage their own virtual environments

echo "🔧 MCP E-commerce Demo - Manual Setup"
echo "====================================="

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${YELLOW}📋 Manual Setup Steps:${NC}"
echo ""

echo -e "${CYAN}1. Install Node.js dependencies:${NC}"
echo "   npm install"
echo "   cd frontend && npm install && cd .."
echo ""

echo -e "${CYAN}2. Create Python virtual environments:${NC}"
echo "   cd backend"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "   deactivate"
echo "   cd .."
echo ""
echo "   cd mcp-server"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "   deactivate"
echo "   cd .."
echo ""

echo -e "${CYAN}3. Set up environment:${NC}"
echo "   cp .env.example .env"
echo "   # Edit .env and add your OPENAI_API_KEY"
echo ""

echo -e "${CYAN}4. Start services:${NC}"
echo "   npm run dev  # Starts all services"
echo "   # OR start individually:"
echo "   # Terminal 1: npm run dev:mcp"
echo "   # Terminal 2: npm run dev:backend" 
echo "   # Terminal 3: npm run dev:frontend"
echo ""

echo -e "${GREEN}💡 Tip: Use './start.sh' for automatic setup with virtual environments!${NC}"