#!/bin/bash

# Deployment script for Render
# This script helps prepare the repository for Render deployment

set -e

echo "🚀 Preparing Nekuda MCP UI Demo for Render deployment..."

# Check if we're in the right directory
if [ ! -f "render.yaml" ]; then
    echo "❌ Error: render.yaml not found. Please run this script from the project root."
    exit 1
fi

# Check if git is initialized and has a remote
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "❌ Error: No git remote 'origin' found."
    echo "Please push your code to: https://github.com/nekuda-ai/nekuda-mcp-ui-demo.git"
    exit 1
fi

# Get the current git remote URL
REMOTE_URL=$(git remote get-url origin)
echo "📁 Current repository: $REMOTE_URL"

# Check if all files are committed
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes. Consider committing them first."
    git status --short
    echo ""
fi

echo "✅ Pre-deployment checklist:"
echo "   - render.yaml configuration file created"
echo "   - Health check endpoints available"
echo "   - Environment variable support added"
echo "   - Production-ready server configurations"

echo ""
echo "📋 Next steps for Render deployment:"
echo ""
echo "1. 🌐 Go to https://render.com and log in"
echo "2. ➕ Click 'New' → 'Blueprint'"
echo "3. 🔗 Connect your GitHub repository: https://github.com/nekuda-ai/nekuda-mcp-ui-demo.git"
echo "4. 📝 Name your blueprint: 'nekuda-mcp-ui-demo'"
echo "5. ⚙️  Set the following environment variables in Render dashboard:"
echo ""
echo "   For Backend Service (nekuda-mcp-ui-backend):"
echo "   - OPENAI_API_KEY=your_openai_api_key_here"
echo "   - CORS_ORIGINS=https://nekuda-mcp-ui-frontend-xxx.onrender.com"
echo ""
echo "6. 🚀 Click 'Apply' to deploy"
echo "7. ⏱️  Wait for all services to deploy (MCP Server → Backend → Frontend)"
echo "8. 🔍 Update the CORS_ORIGINS with your actual frontend URL after deployment"
echo ""
echo "📖 For detailed instructions, see DEPLOYMENT.md"
echo ""
echo "🎉 Ready for deployment!"
