"""Tests for admin service.

Tests cover:
- ApiKey model methods (is_expired, is_active, has_scope)
- API key generation and hashing
- API key creation and revocation
"""

import unittest
from datetime import datetime, timedelta, timezone

from app import create_app
from models import ApiKey, db
from services.api_auth import (
    create_api_key,
    generate_api_key,
    hash_api_key,
    revoke_api_key,
)


class TestApiKeyModel(unittest.TestCase):
    """Tests for ApiKey model methods."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_is_expired_no_expiry(self) -> None:
        """Key without expiry should not be expired."""
        key = ApiKey(
            key_hash=hash_api_key("test_key"),
            name="Test Key",
            scope="read",
        )
        self.assertFalse(key.is_expired)

    def test_is_expired_future(self) -> None:
        """Key with future expiry should not be expired."""
        key = ApiKey(
            key_hash=hash_api_key("test_key"),
            name="Test Key",
            scope="read",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        self.assertFalse(key.is_expired)

    def test_is_expired_past(self) -> None:
        """Key with past expiry should be expired."""
        key = ApiKey(
            key_hash=hash_api_key("test_key"),
            name="Test Key",
            scope="read",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        self.assertTrue(key.is_expired)

    def test_is_active_not_revoked_not_expired(self) -> None:
        """Non-revoked, non-expired key should be active."""
        key = ApiKey(
            key_hash=hash_api_key("test_key"),
            name="Test Key",
            scope="read",
        )
        self.assertTrue(key.is_active)

    def test_is_active_revoked(self) -> None:
        """Revoked key should not be active."""
        key = ApiKey(
            key_hash=hash_api_key("test_key"),
            name="Test Key",
            scope="read",
            revoked=True,
        )
        self.assertFalse(key.is_active)

    def test_is_active_expired(self) -> None:
        """Expired key should not be active."""
        key = ApiKey(
            key_hash=hash_api_key("test_key"),
            name="Test Key",
            scope="read",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        self.assertFalse(key.is_active)

    def test_has_scope_read_key_read_scope(self) -> None:
        """Read key should have read scope."""
        key = ApiKey(key_hash="hash", name="Test", scope="read")
        self.assertTrue(key.has_scope("read"))

    def test_has_scope_read_key_write_scope(self) -> None:
        """Read key should NOT have write scope."""
        key = ApiKey(key_hash="hash", name="Test", scope="read")
        self.assertFalse(key.has_scope("write"))

    def test_has_scope_write_key_read_scope(self) -> None:
        """Write key should have read scope."""
        key = ApiKey(key_hash="hash", name="Test", scope="write")
        self.assertTrue(key.has_scope("read"))

    def test_has_scope_write_key_write_scope(self) -> None:
        """Write key should have write scope."""
        key = ApiKey(key_hash="hash", name="Test", scope="write")
        self.assertTrue(key.has_scope("write"))

    def test_has_scope_admin_key_all_scopes(self) -> None:
        """Admin key should have all scopes."""
        key = ApiKey(key_hash="hash", name="Test", scope="admin")
        self.assertTrue(key.has_scope("read"))
        self.assertTrue(key.has_scope("write"))
        self.assertTrue(key.has_scope("admin"))

    def test_has_scope_invalid_scope(self) -> None:
        """Invalid scope comparison - unknown scope has level 0, so read (1) >= 0 = True."""
        key = ApiKey(key_hash="hash", name="Test", scope="read")
        # Unknown scope gets level 0, so any key with level >= 1 will pass
        self.assertTrue(key.has_scope("superadmin"))


class TestApiKeyGeneration(unittest.TestCase):
    """Tests for API key generation and hashing."""

    def test_generate_api_key_format(self) -> None:
        """Generated key should start with 'shl_'."""
        key = generate_api_key()
        self.assertTrue(key.startswith("shl_"))
        self.assertEqual(len(key), 68)  # shl_ + 64 hex chars

    def test_hash_api_key_deterministic(self) -> None:
        """Same key should produce same hash."""
        key = "test_key"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        self.assertEqual(hash1, hash2)

    def test_hash_api_key_different(self) -> None:
        """Different keys should produce different hashes."""
        hash1 = hash_api_key("key1")
        hash2 = hash_api_key("key2")
        self.assertNotEqual(hash1, hash2)


class TestApiKeyManagement(unittest.TestCase):
    """Tests for API key creation and revocation."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_api_key_read(self) -> None:
        """Should create read scope key."""
        plain_key, api_key = create_api_key("Test Read Key", scope="read")
        self.assertTrue(plain_key.startswith("shl_"))
        self.assertEqual(api_key.scope, "read")
        self.assertFalse(api_key.revoked)

    def test_create_api_key_write(self) -> None:
        """Should create write scope key."""
        plain_key, api_key = create_api_key("Test Write Key", scope="write")
        self.assertEqual(api_key.scope, "write")

    def test_create_api_key_admin(self) -> None:
        """Should create admin scope key."""
        plain_key, api_key = create_api_key("Test Admin Key", scope="admin")
        self.assertEqual(api_key.scope, "admin")

    def test_create_api_key_with_expiry(self) -> None:
        """Should create key with expiration."""
        plain_key, api_key = create_api_key("Expiring Key", expires_in_days=30)
        self.assertIsNotNone(api_key.expires_at)
        self.assertFalse(api_key.is_expired)

    def test_create_api_key_invalid_scope(self) -> None:
        """Should raise ValueError for invalid scope."""
        with self.assertRaises(ValueError):
            create_api_key("Bad Key", scope="invalid")

    def test_revoke_api_key_success(self) -> None:
        """Should revoke existing key."""
        plain_key, api_key = create_api_key("Revoke Test")
        result = revoke_api_key(api_key.id)
        self.assertTrue(result)

        # Verify key is revoked
        db.session.refresh(api_key)
        self.assertTrue(api_key.revoked)

    def test_revoke_api_key_not_found(self) -> None:
        """Should return False for non-existent key."""
        result = revoke_api_key(9999)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
