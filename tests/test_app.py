import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, get_db
import httpx
from main import app

async def run_tests():
    print("--- STARTING TESTS ---")
    init_db()

    # Use AsyncClient with ASGI transport
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register User 1
        u1_email = f"user1_{os.urandom(3).hex()}@example.com"
        r1 = await client.post("/api/auth/register", json={"email": u1_email, "password": "password123"})
        assert r1.status_code == 200, f"Register U1 failed: {r1.text}"
        print("✓ User 1 registration successful")

        # Extract U1 cookie
        u1_cookie = r1.cookies.get("access_token")
        assert u1_cookie is not None, "Cookie not set on registration"

        # 2. Test Word Lookup & Automatic Save for User 1
        headers_u1 = {"Cookie": f"access_token={u1_cookie}"}
        r_lookup = await client.post(
            "/api/lookup",
            json={"query": "resilient", "source_lang": "English", "target_lang": "Spanish"},
            headers=headers_u1
        )
        assert r_lookup.status_code == 200, f"Lookup failed: {r_lookup.text}"
        data = r_lookup.json()
        assert data["success"] is True
        assert data["auto_saved"] is True
        saved_word_id = data["data"]["id"]
        print(f"✓ Lookup successful & auto-saved word ID: {saved_word_id}")

        # 3. Verify word appears in User 1's vocabulary
        r_vocab1 = await client.get("/api/vocab", headers=headers_u1)
        assert r_vocab1.status_code == 200
        items1 = r_vocab1.json()["items"]
        assert len(items1) == 1
        assert items1[0]["clean_word"] == "resilient"
        print("✓ Word verified in User 1 vocabulary bank")

        # 4. Toggle Important (⭐)
        r_star = await client.patch(f"/api/vocab/{saved_word_id}/important", headers=headers_u1)
        assert r_star.status_code == 200
        assert r_star.json()["is_important"] is True
        print("✓ Star toggle (Important) working")

        # 5. Add Notes
        r_notes = await client.patch(
            f"/api/vocab/{saved_word_id}/notes",
            json={"notes": "Key word for leadership interview."},
            headers=headers_u1
        )
        assert r_notes.status_code == 200
        # Verify notes saved
        r_item = await client.get(f"/api/vocab/{saved_word_id}", headers=headers_u1)
        assert r_item.json()["notes"] == "Key word for leadership interview."
        print("✓ Personal notes saving working")

        # 6. REGISTER USER 2 & TEST PRIVACY ISOLATION
        u2_email = f"user2_{os.urandom(3).hex()}@example.com"
        r2 = await client.post("/api/auth/register", json={"email": u2_email, "password": "password123"})
        assert r2.status_code == 200
        u2_cookie = r2.cookies.get("access_token")
        headers_u2 = {"Cookie": f"access_token={u2_cookie}"}
        print("✓ User 2 registration successful")

        # Verify User 2 sees 0 words (CANNOT SEE USER 1's VOCAB)
        r_vocab2 = await client.get("/api/vocab", headers=headers_u2)
        assert r_vocab2.status_code == 200
        items2 = r_vocab2.json()["items"]
        assert len(items2) == 0, f"Privacy breach! User 2 saw {len(items2)} items"
        print("✓ Privacy Isolation: User 2 sees 0 words, User 1's vocabulary is strictly protected")

        # Verify User 2 CANNOT access User 1's word details directly by ID
        r_unauth_access = await client.get(f"/api/vocab/{saved_word_id}", headers=headers_u2)
        assert r_unauth_access.status_code == 404, "User 2 was able to view User 1's word!"
        print("✓ Privacy Protection: User 2 cannot access User 1's word by ID (returned 404)")

        # 7. Delete Word for User 1
        r_del = await client.delete(f"/api/vocab/{saved_word_id}", headers=headers_u1)
        assert r_del.status_code == 200
        r_vocab1_after = await client.get("/api/vocab", headers=headers_u1)
        assert len(r_vocab1_after.json()["items"]) == 0
        print("✓ Word deletion working")

    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    asyncio.run(run_tests())
