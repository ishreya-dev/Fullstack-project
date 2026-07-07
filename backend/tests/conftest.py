# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport

from api import app
from api.common.enums.gender import Gender
from api.common.seeder_utils import get_seed_roles
from api.domain.dtos.role_dto import CreateRoleDto, UpdateRoleDto
from api.domain.dtos.user_dto import UserDto
from api.domain.entities.role import Role
from api.domain.entities.tenant import Tenant
from api.domain.entities.user_password_reset import UserPasswordReset
from api.domain.entities.user_preference import UserPreference
from api.infrastructure.persistence.mongodb import Database
from api.domain.entities.user import User
from api.infrastructure.security.current_user import get_current_user
from api.core.container import get_role_service

TEST_MONGO_URI = "mongodb://localhost:27012/test_db"


@pytest.fixture
async def test_app():
    # Initialize test database per test function (same loop as the test)
    db = Database(
        uri=TEST_MONGO_URI,
        models=[User, Tenant, Role, UserPasswordReset, UserPreference],
    )
    await db.init_db("api_test_db", is_tenant=False)

    # Seed roles in the test database
    role_service = get_role_service()
    seeded_role_id = None
    for role in get_seed_roles():
        existing = await role_service.role_repository.single_or_none(name=role.name)
        if existing is None:
            create_role = CreateRoleDto(
                name=role.name,
                description=role.description,
            )
            role_id = await role_service.role_repository.create(data=create_role)
            update_role = UpdateRoleDto(
                name=role.name,
                description=role.description,
                permissions=role.permissions,
            )
            await role_service.role_repository.update(
                role_id=str(role_id), data=update_role
            )
            if role.name == "admin":
                seeded_role_id = str(role_id)

    # If no admin role was seeded, get the first role
    if seeded_role_id is None:
        admin_role = await role_service.role_repository.single_or_none(name="admin")
        if admin_role:
            seeded_role_id = str(admin_role.id)
        else:
            # Get any role
            roles = await role_service.role_repository.list()
            if roles:
                seeded_role_id = str(roles[0].id)

    # Override the get_current_user dependency to return a mocked test user
    async def override_get_current_user():
        return UserDto(
            first_name="Admin",
            last_name="User",
            id="68c302ef6bf7a039b7e9b385",
            email="admin@example.com",
            gender=Gender.OTHER,
            is_active=True,
            role_id=seeded_role_id,
            created_at="2024-10-01T00:00:00Z",
            updated_at="2024-10-01T00:00:00Z",
        )

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield app
    await db.drop()


@pytest.fixture
async def client(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test/api/v1"
    ) as client:
        yield client
