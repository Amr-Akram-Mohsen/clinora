"""
tests/factories.py

factory_boy factories for creating test data.

All factories produce ORM objects ready for session.add().
They do not commit; tests are responsible for flushing/committing.
"""

import uuid
from datetime import UTC, datetime, timedelta

import factory
from factory import LazyFunction

from core.security import hash_password
from infrastructure.database.models.organization import Organization
from infrastructure.database.models.user import RefreshToken, Role, User

PASSWORD_PLAIN = "TestPassword123!"


class OrganizationFactory(factory.Factory):
    class Meta:
        model = Organization

    id = LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Test Clinic {n}")
    slug = factory.Sequence(lambda n: f"test-clinic-{n}")
    is_active = True


class RoleFactory(factory.Factory):
    class Meta:
        model = Role

    id = LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"ROLE_{n}")
    description = "Test role"


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = LazyFunction(uuid.uuid4)
    organization_id = LazyFunction(uuid.uuid4)  # Override with real org.id in tests
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password_hash = LazyFunction(lambda: hash_password(PASSWORD_PLAIN))
    full_name = factory.Sequence(lambda n: f"Test User {n}")
    is_active = True
    is_superuser = False


class RefreshTokenFactory(factory.Factory):
    class Meta:
        model = RefreshToken

    id = LazyFunction(uuid.uuid4)
    user_id = LazyFunction(uuid.uuid4)
    token_hash = LazyFunction(lambda: uuid.uuid4().hex)
    family_id = LazyFunction(uuid.uuid4)
    issued_at = LazyFunction(lambda: datetime.now(tz=UTC))
    expires_at = LazyFunction(
        lambda: datetime.now(tz=UTC) + timedelta(days=30)
    )
    revoked_at = None
    replaced_by = None
