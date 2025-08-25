#!/usr/bin/env node

/**
 * Health check script to verify all services are running
 */

const http = require('http');
const https = require('https');

const SERVICES = [
  { name: 'MCP Server', url: 'http://localhost:3001/health', port: 3001 },
  { name: 'Backend API', url: 'http://localhost:8000/health', port: 8000 },
  { name: 'Frontend', url: 'http://localhost:3000', port: 3000 }
];

const COLORS = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m'
};

function colorLog(color, message) {
  console.log(`${COLORS[color]}${message}${COLORS.reset}`);
}

function checkUrl(url) {
  return new Promise((resolve) => {
    const client = url.startsWith('https') ? https : http;
    const request = client.get(url, { timeout: 5000 }, (res) => {
      resolve({
        success: res.statusCode >= 200 && res.statusCode < 400,
        status: res.statusCode
      });
    });

    request.on('timeout', () => {
      request.destroy();
      resolve({ success: false, error: 'Timeout' });
    });

    request.on('error', (err) => {
      resolve({ success: false, error: err.message });
    });
  });
}

async function checkAllServices() {
  console.log('\n🔍 MCP E-commerce Demo - Health Check\n');
  
  let allHealthy = true;

  for (const service of SERVICES) {
    const result = await checkUrl(service.url);
    
    if (result.success) {
      colorLog('green', `✅ ${service.name} - Running (${service.url})`);
    } else {
      colorLog('red', `❌ ${service.name} - Failed (${result.error || `Status: ${result.status}`})`);
      allHealthy = false;
    }
  }

  console.log('\n' + '='.repeat(50));
  
  if (allHealthy) {
    colorLog('green', '🎉 All services are healthy!');
    colorLog('cyan', '\n🚀 Ready to test: http://localhost:3000');
    console.log('\n📋 Try these demo commands:');
    console.log('   • "Show me products"');
    console.log('   • "I want electronics"');
    console.log('   • "Add headphones to cart"');
    console.log('   • "What\'s in my cart?"');
    
    process.exit(0);
  } else {
    colorLog('red', '❌ Some services are not healthy');
    colorLog('yellow', '\n💡 Make sure all services are running:');
    console.log('   npm run dev  # Starts all services');
    console.log('\n   Or start individually:');
    console.log('   Terminal 1: npm run dev:mcp');
    console.log('   Terminal 2: npm run dev:backend');
    console.log('   Terminal 3: npm run dev:frontend');
    
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n👋 Health check interrupted');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n👋 Health check terminated');
  process.exit(0);
});

checkAllServices().catch((error) => {
  colorLog('red', `❌ Health check failed: ${error.message}`);
  process.exit(1);
});