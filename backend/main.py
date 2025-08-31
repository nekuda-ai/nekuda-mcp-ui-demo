#!/usr/bin/env python3
"""
E-commerce Demo Backend

FastAPI backend that handles:
- Chat interface with OpenAI integration
- MCP communication with the mock server
- Cart management
- Session handling
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import httpx
import openai
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

# Import Nekuda service
from nekuda_service import nekuda_service, CheckoutRequest, NekudaPaymentData


class Settings(BaseSettings):
    openai_api_key: str
    mcp_server_url: str = "http://localhost:3003"
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if not self.cors_origins:
            return []
        origins = [origin.strip() for origin in self.cors_origins.split(',')]
        return origins
    
    @property
    def cors_origins_full_urls(self) -> List[str]:
        """Convert hostnames to full URLs if needed"""
        full_urls = []
        for origin in self.cors_origins_list:
            if origin.startswith(('http://', 'https://')):
                full_urls.append(origin)
            else:
                full_urls.append(f"https://{origin}")
        return full_urls
    session_secret_key: str = "your-secret-key-change-in-production"
    
    @property
    def mcp_server_full_url(self) -> str:
        """Convert hostname to full URL if needed"""
        if self.mcp_server_url.startswith(('http://', 'https://')):
            return self.mcp_server_url
        else:
            return f"https://{self.mcp_server_url}"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env file


# Pydantic models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ui_resource: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: ChatMessage
    session_id: str
    is_mcp_response: bool = False


class MCPActionRequest(BaseModel):
    action_type: str = Field(..., description="Type of MCP action")
    tool_name: str = Field(..., description="Name of the MCP tool to call")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    session_id: Optional[str] = None


# Initialize FastAPI app
settings = Settings()

# Configure logging
def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Configure logging format
    if environment == "production":
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    else:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler()]
    )
    
    return logging.getLogger("backend")

logger = setup_logging()

app = FastAPI(
    title="MCP E-commerce Backend",
    description="Backend for MCP-UI e-commerce demo",
    version="1.0.0"
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_full_urls,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

# Enhanced session storage with metadata
chat_sessions: Dict[str, List[ChatMessage]] = {}
user_sessions: Dict[str, Dict[str, Any]] = {}
session_metadata: Dict[str, Dict[str, Any]] = {}


def get_session_id(request: Request) -> str:
    """Get or create a session ID with enhanced session management."""
    session_id = request.session.get("session_id")
    current_time = datetime.utcnow()
    
    if not session_id or session_id not in chat_sessions:
        # Create new session
        session_id = str(uuid.uuid4())
        request.session["session_id"] = session_id
        chat_sessions[session_id] = []
        user_sessions[session_id] = {"created_at": current_time}
        session_metadata[session_id] = {
            "created_at": current_time,
            "last_accessed": current_time,
            "access_count": 1,
            "user_agent": request.headers.get("user-agent", "unknown"),
            "client_ip": request.client.host if request.client else "unknown"
        }
    else:
        # Update existing session metadata
        session_metadata[session_id]["last_accessed"] = current_time
        session_metadata[session_id]["access_count"] = session_metadata[session_id].get("access_count", 0) + 1
    
    return session_id


# Cache for MCP tools to avoid repeated calls
_mcp_tools_cache: Optional[List[Dict[str, Any]]] = None
_tools_cache_timestamp: Optional[datetime] = None
_cache_ttl_seconds = 300  # 5 minutes cache

# Session cleanup configuration
SESSION_TIMEOUT_HOURS = 24  # Sessions expire after 24 hours of inactivity
CLEANUP_INTERVAL_MINUTES = 60  # Run cleanup every hour


def cleanup_expired_sessions():
    """Remove expired sessions to prevent memory leaks."""
    current_time = datetime.utcnow()
    expired_sessions = []
    
    for session_id, metadata in session_metadata.items():
        last_accessed = metadata.get("last_accessed", metadata.get("created_at"))
        if last_accessed:
            hours_since_access = (current_time - last_accessed).total_seconds() / 3600
            if hours_since_access > SESSION_TIMEOUT_HOURS:
                expired_sessions.append(session_id)
    
    # Clean up expired sessions
    for session_id in expired_sessions:
        chat_sessions.pop(session_id, None)
        user_sessions.pop(session_id, None)
        session_metadata.pop(session_id, None)
        logger.info(f"Cleaned up expired session: {session_id}")
    
    if expired_sessions:
        logger.info(f"Session cleanup: Removed {len(expired_sessions)} expired sessions")
    
    return len(expired_sessions)


async def periodic_session_cleanup():
    """Background task for periodic session cleanup."""
    while True:
        try:
            cleanup_expired_sessions()
            await asyncio.sleep(CLEANUP_INTERVAL_MINUTES * 60)  # Convert to seconds
        except Exception as e:
            logger.error(f"Error in session cleanup: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retry


async def get_mcp_tools() -> List[Dict[str, Any]]:
    """Fetch available tools from MCP server and transform to OpenAI format"""
    global _mcp_tools_cache, _tools_cache_timestamp
    
    # Check cache validity
    if (_mcp_tools_cache is not None and 
        _tools_cache_timestamp is not None and 
        (datetime.utcnow() - _tools_cache_timestamp).total_seconds() < _cache_ttl_seconds):
        return _mcp_tools_cache
    
    # Fetch tools from MCP server
    mcp_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/list",
        "params": {}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.mcp_server_full_url}/mcp",
                json=mcp_request,
                timeout=10.0
            )
            response.raise_for_status()
            mcp_response = response.json()
            
            if "error" in mcp_response and mcp_response["error"] is not None:
                raise Exception(f"MCP server error: {mcp_response['error']}")
            
            # Transform MCP tools to OpenAI function calling format
            mcp_tools = mcp_response.get("result", {}).get("tools", [])
            openai_tools = []
            
            for tool in mcp_tools:
                # Enhance descriptions for specific tools
                description = tool.get("description", "")
                if tool.get("name") == "get_products":
                    description = "Get all available products with interactive UI carousel. ALWAYS use this function when the user asks to see, browse, show, or view products. IMPORTANT: Do NOT specify a category parameter - always call this function without any parameters to show all products. Our store specializes in NBA jerseys from legendary players."
                elif tool.get("name") == "get_nba_jerseys":
                    description = "Show all NBA jerseys with interactive UI carousel. Use this when user asks to see NBA jerseys, basketball jerseys, or sports jerseys."
                elif tool.get("name") == "get_lebron_jersey":
                    description = "Show LeBron James Lakers Jersey #6 with detailed view. Use when user asks about LeBron, Lakers, or King James jersey."
                elif tool.get("name") == "get_jordan_jersey":
                    description = "Show Michael Jordan Bulls Jersey #23 with detailed view. Use when user asks about Jordan, Bulls, MJ, or GOAT jersey."
                elif tool.get("name") == "get_curry_jersey":
                    description = "Show Stephen Curry Warriors Jersey #30 with detailed view. Use when user asks about Curry, Warriors, or Chef Curry jersey."
                
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.get("name"),
                        "description": description,
                        "parameters": tool.get("inputSchema", {"type": "object", "properties": {}})
                    }
                }
                openai_tools.append(openai_tool)
            
            # Update cache
            _mcp_tools_cache = openai_tools
            _tools_cache_timestamp = datetime.utcnow()
            
            logger.debug(f"Fetched {len(openai_tools)} tools from MCP server")
            return openai_tools
            
        except Exception as e:
            logger.error(f"Failed to fetch tools from MCP server: {e}")
            # Return empty list if MCP server is unavailable
            return []


async def call_mcp_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Call an MCP tool on the mock server"""
    mcp_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": params
        }
    }
    
    logger.debug(f"MCP request to {settings.mcp_server_full_url}/mcp")
    logger.debug(f"MCP request payload: {mcp_request}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.mcp_server_full_url}/mcp",
                json=mcp_request,
                timeout=30.0
            )
            logger.debug(f"MCP response status: {response.status_code}")
            logger.debug(f"MCP response text: {response.text}")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.debug(f"MCP RequestError: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Failed to communicate with MCP server: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            logger.debug(f"MCP HTTPStatusError: {e}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"MCP server returned error: {e.response.text}"
            )




@app.get("/")
async def root():
    return {"message": "MCP E-commerce Backend", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test MCP server connection
        async with httpx.AsyncClient() as client:
            mcp_response = await client.get(f"{settings.mcp_server_full_url}/", timeout=5.0)
            mcp_healthy = mcp_response.status_code == 200
    except:
        mcp_healthy = False
    
    return {
        "status": "healthy" if mcp_healthy else "degraded",
        "mcp_server": "connected" if mcp_healthy else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest, request: Request):
    """Main chat endpoint using proper OpenAI function calling with MCP tools"""
    session_id = get_session_id(request)
    
    # Add user message to history
    user_message = ChatMessage(
        role="user",
        content=chat_request.message,
        timestamp=datetime.utcnow()
    )
    chat_sessions[session_id].append(user_message)
    
    try:
        # Build conversation history for OpenAI
        openai_messages = [
            {
                "role": "system", 
                "content": "You are a helpful NBA jersey store assistant. Our store specializes in authentic NBA jerseys from legendary superstars like LeBron James, Stephen Curry, Giannis, Luka Dončić, Jayson Tatum, and Michael Jordan. You have access to tools to show real product data and interactive UI components with hover effects. IMPORTANT: ALWAYS use the appropriate tools - never generate fake content. Available tools: get_products (all products), get_nba_jerseys (NBA only), get_lebron_jersey, get_jordan_jersey, get_curry_jersey (specific jerseys), get_product_details, add_to_cart, and checkout. When users ask to see specific jerseys, use the dedicated jersey tools. When they ask to see/view/show/check their cart, tell them to use the shopping cart icon in the top right corner of the page - do not try to display cart contents yourself. Be enthusiastic about basketball and our jerseys!"
            }
        ]
        
        # Add conversation history (limit to last 10 messages to avoid token limits)
        recent_messages = chat_sessions[session_id][-10:]
        for msg in recent_messages[:-1]:  # Exclude the current user message 
            if msg.ui_resource is None:  # Only include text messages in OpenAI context
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add the current user message
        openai_messages.append({
            "role": "user",
            "content": chat_request.message
        })
        
        # Get available tools from MCP server
        available_tools = await get_mcp_tools()
        
        # Debug logging
        logger.debug(f"About to call OpenAI with {len(openai_messages)} messages")
        logger.debug(f"Last user message: {openai_messages[-1]}")
        logger.debug(f"Number of tools from MCP server: {len(available_tools)}")
        
        # Call OpenAI with function calling capability
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=openai_messages,
            tools=available_tools,
            tool_choice="auto",  # Let OpenAI decide when to use tools
            max_tokens=1000,
            temperature=0.7
        )
        
        assistant_message = response.choices[0].message
        
        # Debug logging
        logger.debug(f"OpenAI response received")
        logger.debug(f"Assistant message content: {assistant_message.content}")
        logger.debug(f"Tool calls: {assistant_message.tool_calls}")
        
        # Check if OpenAI wants to call a function/tool
        if assistant_message.tool_calls:
            # Handle tool calls
            tool_results = []
            ui_resource = None
            
            for tool_call in assistant_message.tool_calls:
                try:
                    # Extract tool information
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # Add session_id to params if needed for cart operations
                    if tool_name in ["add_to_cart", "checkout"]:
                        tool_args["session_id"] = session_id
                    
                    # Call MCP tool
                    logger.debug(f"Calling MCP tool {tool_name} with args {tool_args}")
                    mcp_response = await call_mcp_tool(tool_name, tool_args)
                    logger.debug(f"MCP response: {mcp_response}")
                    
                    if "error" in mcp_response and mcp_response["error"] is not None:
                        # Tool error
                        error_msg = mcp_response["error"].get("message", "Tool execution failed")
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "content": f"Error: {error_msg}"
                        })
                    else:
                        # Successful tool response
                        ui_resources = mcp_response.get("result", {}).get("content", [])
                        
                        # Handle UI resources - both legacy HTML and new remote-dom
                        if ui_resources:
                            first_resource = ui_resources[0]
                            
                            if first_resource.get("type") == "html":
                                # Legacy HTML format
                                ui_resource = {
                                    "type": "resource",
                                    "resource": {
                                        "uri": f"ui://{tool_name}/{str(uuid.uuid4())}",
                                        "mimeType": "text/html",
                                        "text": first_resource.get("content", "")
                                    }
                                }
                            elif first_resource.get("type") == "resource":
                                # New MCP-UI resource format (remote-dom and HTML)
                                ui_resource = first_resource
                        
                        # Provide structured result for OpenAI
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool", 
                            "content": f"Successfully executed {tool_name} with parameters {tool_args}. Interactive UI component available for user."
                        })
                        
                except Exception as e:
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": f"Error executing {tool_name}: {str(e)}"
                    })
            
            # Send tool results back to OpenAI for final response
            openai_messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function", 
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in assistant_message.tool_calls
                ]
            })
            
            # Add tool results
            for result in tool_results:
                openai_messages.append(result)
            
            # Get final response from OpenAI
            final_response = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=openai_messages,
                max_tokens=500,
                temperature=0.7
            )
            
            final_content = final_response.choices[0].message.content
            
            # If we have a UI resource, don't show text content to keep interface clean
            display_content = "" if ui_resource else final_content
            
            assistant_message_obj = ChatMessage(
                role="assistant",
                content=display_content,
                timestamp=datetime.utcnow(),
                ui_resource=ui_resource
            )
            
            chat_sessions[session_id].append(assistant_message_obj)
            
            return ChatResponse(
                message=assistant_message_obj,
                session_id=session_id,
                is_mcp_response=ui_resource is not None
            )
            
        else:
            # Regular chat response without tool calls
            assistant_message_obj = ChatMessage(
                role="assistant",
                content=assistant_message.content,
                timestamp=datetime.utcnow()
            )
            
            chat_sessions[session_id].append(assistant_message_obj)
            
            return ChatResponse(
                message=assistant_message_obj,
                session_id=session_id
            )
        
    except openai.RateLimitError:
        raise HTTPException(status_code=429, detail="OpenAI rate limit exceeded")
    except openai.APIError as e:
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/mcp-action")
async def mcp_action_endpoint(action_request: MCPActionRequest, request: Request):
    """Handle direct MCP tool calls from the frontend"""
    # Use session_id from request if provided, otherwise get from request headers/cookies
    session_id = action_request.session_id or get_session_id(request)
    
    try:
        # Add session_id to params for MCP tools that need it
        params_with_session = action_request.params.copy() if action_request.params else {}
        params_with_session["session_id"] = session_id
        
        mcp_response = await call_mcp_tool(
            action_request.tool_name,
            params_with_session
        )
        
        if "error" in mcp_response and mcp_response["error"] is not None:
            error_msg = "Unknown error"
            if isinstance(mcp_response["error"], dict):
                error_msg = mcp_response["error"].get("message", "Unknown error")
            raise HTTPException(
                status_code=400,
                detail=f"MCP tool error: {error_msg}"
            )
        
        # Add this action to chat history for context
        ui_resource = None
        result = mcp_response.get("result")
        if result and isinstance(result, dict):
            content = result.get("content")
            if content and isinstance(content, list) and len(content) > 0:
                ui_content = content[0]
                if ui_content and ui_content.get("type") == "html":
                    ui_resource = {
                        "type": "resource",
                        "resource": {
                            "uri": f"ui://{action_request.tool_name}/{str(uuid.uuid4())}",
                            "mimeType": "text/html",
                            "text": ui_content.get("content", "")
                        }
                    }
        
        action_message = ChatMessage(
            role="assistant",
            content=f"Processed {action_request.tool_name} action",
            timestamp=datetime.utcnow(),
            ui_resource=ui_resource
        )
        chat_sessions[session_id].append(action_message)
        
        return mcp_response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error in mcp_action_endpoint: {e}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/chat-history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    history = chat_sessions.get(session_id, [])
    return {"session_id": session_id, "messages": history}


@app.delete("/chat-history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a session"""
    if session_id in chat_sessions:
        chat_sessions[session_id] = []
    return {"message": "Chat history cleared", "session_id": session_id}


@app.get("/sessions")
async def get_session_info():
    """Get information about active sessions"""
    active_sessions = len(chat_sessions)
    total_messages = sum(len(messages) for messages in chat_sessions.values())
    
    return {
        "active_sessions": active_sessions,
        "total_messages": total_messages,
        "session_timeout_hours": SESSION_TIMEOUT_HOURS
    }


@app.post("/sessions/cleanup")
async def manual_session_cleanup():
    """Manually trigger session cleanup"""
    cleaned_count = cleanup_expired_sessions()
    return {
        "message": "Session cleanup completed",
        "cleaned_sessions": cleaned_count,
        "remaining_sessions": len(chat_sessions)
    }


@app.get("/sessions/{session_id}/info")
async def get_session_details(session_id: str):
    """Get details about a specific session"""
    if session_id not in session_metadata:
        raise HTTPException(status_code=404, detail="Session not found")
    
    metadata = session_metadata[session_id]
    message_count = len(chat_sessions.get(session_id, []))
    
    return {
        "session_id": session_id,
        "created_at": metadata.get("created_at"),
        "last_accessed": metadata.get("last_accessed"),
        "access_count": metadata.get("access_count", 0),
        "message_count": message_count,
        "user_agent": metadata.get("user_agent"),
        "client_ip": metadata.get("client_ip")
    }


# Nekuda Wallet Integration Endpoints

class AtomicCheckoutRequest(BaseModel):
    """Request model for atomic checkout with mandate creation"""
    user_id: str
    cart_total: float
    cart_items: List[Dict[str, Any]]
    product_summary: str = "E-commerce Cart Purchase"
    currency: str = "USD"
    checkout_context: str = "user_clicked_checkout_button"

@app.post("/api/atomic-nekuda-checkout")
async def atomic_nekuda_checkout(checkout_request: AtomicCheckoutRequest):
    """
    Atomic checkout flow: Create mandate when user clicks checkout → get token → get PAN
    This represents the user's explicit intent to purchase when they click checkout
    """
    try:
        logger.debug(f"Starting atomic checkout for user {checkout_request.user_id}")
        logger.debug(f"Cart total: ${checkout_request.cart_total}, Items: {len(checkout_request.cart_items)}")
        logger.debug(f"Checkout context: {checkout_request.checkout_context}")
        
        # Create mandate with checkout context immediately
        mandate_id = await nekuda_service.create_mandate_for_checkout(
            user_id=checkout_request.user_id,
            cart_total=checkout_request.cart_total,
            product_name=checkout_request.product_summary,
            currency=checkout_request.currency,
            checkout_context=checkout_request.checkout_context,
            cart_items=checkout_request.cart_items
        )
        
        logger.debug(f"Created mandate {mandate_id} for checkout action")
        
        # Immediately get payment credentials using the mandate
        payment_data = await nekuda_service.get_payment_credentials(
            user_id=checkout_request.user_id,
            mandate_id=mandate_id
        )
        
        logger.debug(f"Retrieved payment credentials for mandate {mandate_id}")
        
        return {
            "success": True,
            "mandate_id": mandate_id,
            "token": payment_data.token,
            "pan": payment_data.pan,
            "expiryMonth": payment_data.expiry_month,
            "expiryYear": payment_data.expiry_year,
            "cvv": payment_data.cvv,
            "cardholderName": payment_data.cardholder_name,
            "checkout_context": checkout_request.checkout_context
        }
        
    except Exception as e:
        logger.error(f"Error in atomic checkout: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Atomic checkout failed: {str(e)}"
        )

@app.post("/api/get-nekuda-payment")
async def get_nekuda_payment(checkout_request: CheckoutRequest):
    """
    DEPRECATED: Use atomic-nekuda-checkout instead
    This endpoint is kept for backward compatibility
    """
    try:
        payment_data = await nekuda_service.complete_checkout_flow(checkout_request)
        
        return {
            "success": True,
            "token": payment_data.token,
            "pan": payment_data.pan,
            "expiryMonth": payment_data.expiry_month,
            "expiryYear": payment_data.expiry_year,
            "cvv": payment_data.cvv,
            "cardholderName": payment_data.cardholder_name
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve Nekuda payment data: {str(e)}"
        )


@app.get("/api/nekuda-wallet-status")
async def get_nekuda_wallet_status(userId: str):
    """Check if user has stored payment methods in Nekuda wallet"""
    try:
        has_payment_methods = await nekuda_service.has_stored_payment_methods(userId)
        return {
            "success": True,
            "hasPaymentMethods": has_payment_methods,
            "userId": userId
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check wallet status: {str(e)}"
        )


@app.post("/api/initialize-nekuda-collection") 
async def initialize_nekuda_collection(request: Dict[str, Any]):
    """Initialize Nekuda payment collection for adding new cards"""
    try:
        user_id = request.get("userId")
        if not user_id:
            raise HTTPException(status_code=400, detail="userId is required")
        
        collection_data = await nekuda_service.initialize_payment_collection(user_id)
        return {
            "success": True,
            **collection_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize payment collection: {str(e)}"
        )

@app.post("/api/nekuda-payment-added")
async def mark_payment_added(request: Dict[str, Any]):
    """Mark that user has successfully added a payment method"""
    try:
        user_id = request.get("userId")
        if not user_id:
            raise HTTPException(status_code=400, detail="userId is required")
        
        # Mark user as having payment methods
        nekuda_service.add_payment_method_for_user(user_id)
        
        return {
            "success": True,
            "message": "Payment method marked as added",
            "userId": user_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark payment method: {str(e)}"
        )


# Startup event to initialize background tasks
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    logger.info("Starting session cleanup background task...")
    asyncio.create_task(periodic_session_cleanup())


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    environment = os.getenv("ENVIRONMENT", "development")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=environment == "development",
        log_level="info"
    )