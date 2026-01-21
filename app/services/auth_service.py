"""
Authentication service - handles user registration, login, password verification.
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.models import User, Role
from app.security import get_password_hash, verify_password, create_access_token


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        """Find user by email."""
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_user_by_id(self, user_id: int) -> User | None:
        """Find user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(
        self,
        email: str,
        password: str,
        role: str = Role.ADVERTISER,
        first_name: str = None,
        last_name: str = None,
    ) -> User:
        """Create a new user."""
        user = User(
            email=email.lower().strip(),
            hashed_password=get_password_hash(password),
            role=role,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def authenticate(self, email: str, password: str) -> User | None:
        """Authenticate user by email and password."""
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        return user

    def create_token_for_user(self, user: User) -> str:
        """Create JWT access token for user."""
        return create_access_token(data={"sub": str(user.id), "role": user.role})

    def ensure_admin_exists(self):
        """Create default admin user if none exists."""
        from app.settings import settings
        
        admin = self.db.query(User).filter(User.role == Role.ADMIN).first()
        if not admin:
            self.create_user(
                email=settings.ADMIN_EMAIL,
                password=settings.ADMIN_PASSWORD,
                role=Role.ADMIN,
                first_name="Admin",
            )
            print(f"Created default admin user: {settings.ADMIN_EMAIL}")


