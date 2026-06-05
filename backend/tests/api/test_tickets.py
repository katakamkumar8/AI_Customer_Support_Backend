"""
tests/api/test_tickets.py
Integration tests for the /tickets endpoints.
"""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "AI Customer Support Agent"


async def test_create_ticket(client: AsyncClient):
    payload = {
        "customer_name": "Alice Smith",
        "email": "alice@example.com",
        "issue_description": "My order never arrived.",
        "priority": "high",
    }
    resp = await client.post("/tickets", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"].startswith("SUP-")
    assert data["customer_name"] == "Alice Smith"
    assert data["status"] == "open"
    assert data["priority"] == "high"


async def test_list_tickets(client: AsyncClient):
    # Create two tickets
    for i in range(2):
        await client.post(
            "/tickets",
            json={
                "customer_name": f"User {i}",
                "email": f"user{i}@example.com",
                "issue_description": "Test issue",
            },
        )
    resp = await client.get("/tickets")
    assert resp.status_code == 200
    data = resp.json()
    assert "tickets" in data
    assert "total" in data
    assert data["total"] >= 2


async def test_get_ticket_by_id(client: AsyncClient):
    create_resp = await client.post(
        "/tickets",
        json={
            "customer_name": "Bob",
            "email": "bob@example.com",
            "issue_description": "Refund needed.",
        },
    )
    ticket_id = create_resp.json()["id"]

    get_resp = await client.get(f"/tickets/{ticket_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == ticket_id


async def test_get_ticket_not_found(client: AsyncClient):
    resp = await client.get("/tickets/SUP-ZZZZZZ")
    assert resp.status_code == 404


async def test_update_ticket_status(client: AsyncClient):
    create_resp = await client.post(
        "/tickets",
        json={
            "customer_name": "Carol",
            "email": "carol@example.com",
            "issue_description": "Cannot login.",
        },
    )
    ticket_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/tickets/{ticket_id}", json={"status": "resolved"}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "resolved"


async def test_ticket_pagination(client: AsyncClient):
    resp = await client.get("/tickets?skip=0&limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tickets"]) <= 2
