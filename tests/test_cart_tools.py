import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure we can import the FastAPI app from this repo layout
THIS_DIR = os.path.dirname(__file__)
SERVER_DIR = os.path.abspath(os.path.join(THIS_DIR, '..'))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from main import app  # type: ignore


client = TestClient(app)


def mcp_call(method: str, params: dict):
    payload = {"jsonrpc": "2.0", "id": "test", "method": method, "params": params}
    r = client.post("/mcp", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def tools_call(name: str, arguments: dict):
    return mcp_call("tools/call", {"name": name, "arguments": arguments})


def test_cart_snapshot_happy_path():
    # fresh session id for isolation
    session_id = "test-session-1"

    # Ensure empty
    res = tools_call("get_cart_state", {"session_id": session_id})
    cart = res["result"]["data"]["cart"]
    assert cart["items"] == []
    assert cart["total"] == 0.0

    # Add item
    add = tools_call(
        "set_cart_quantity",
        {"session_id": session_id, "product_id": "smartphone-1", "variant_id": "storage-128", "quantity": 2},
    )
    cart = add["result"]["data"]["cart"]
    assert any(i["product_id"] == "smartphone-1" and i["quantity"] == 2 for i in cart["items"])
    assert cart["total"] > 0

    # Remove item
    rem = tools_call(
        "remove_from_cart", {"session_id": session_id, "product_id": "smartphone-1", "variant_id": "storage-128"}
    )
    cart = rem["result"]["data"]["cart"]
    assert cart["items"] == []
    assert cart["total"] == 0.0

    # Clear is idempotent
    clr = tools_call("clear_cart", {"session_id": session_id})
    cart = clr["result"]["data"]["cart"]
    assert cart["items"] == []
    assert cart["total"] == 0.0


