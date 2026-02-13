"""Database seeding script to create initial admin user."""
import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


async def seed_admin_user():
    """Create default admin user if none exists."""
    async with AsyncSessionLocal() as db:
        # Check if any admin exists
        result = await db.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        admin = result.scalar_one_or_none()
        
        if admin:
            print(f"Admin user already exists: {admin.email}")
            return
        
        # Create default admin
        admin = User(
            email="admin@hillmann.com",
            password_hash=get_password_hash("admin123"),
            full_name="System Admin",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print("Created default admin user:")
        print("  Email: admin@hillmann.com")
        print("  Password: admin123")
        print("  (Change this password after first login!)")


if __name__ == "__main__":
    asyncio.run(seed_admin_user())
