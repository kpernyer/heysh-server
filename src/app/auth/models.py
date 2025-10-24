"""Authentication data models."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog

from src.app.clients.supabase import get_supabase_client

logger = structlog.get_logger()


class InviteCodeModel:
    """Invite code database model."""

    @staticmethod
    async def create_invite(
        domain_id: str | None = None,
        role: str = "contributor",
        expires_in_days: int = 30,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """Create a new invite code.

        Args:
            domain_id: Domain UUID (optional, restrict to specific domain)
            role: User role when registering with this invite
            expires_in_days: Days until invite expires
            created_by: Admin user ID who created the invite

        Returns:
            Created invite code record

        Raises:
            ValueError: If creation fails

        """
        try:
            supabase = get_supabase_client()

            # Generate 8-character code (e.g., ABC-123-XYZ)
            code = f"{uuid.uuid4().hex[:8].upper()}"

            expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

            result = (
                supabase.table("invite_codes")
                .insert(
                    {
                        "code": code,
                        "domain_id": domain_id,
                        "role": role,
                        "expires_at": expires_at.isoformat(),
                        "created_by": created_by,
                        "used_at": None,
                        "used_by": None,
                    }
                )
                .execute()
            )

            logger.info("Invite code created", code=code, domain_id=domain_id)
            return result.data[0] if result.data else {}

        except Exception as e:
            logger.error("Failed to create invite code", error=str(e))
            raise ValueError(f"Failed to create invite code: {e}")

    @staticmethod
    async def validate_invite(code: str) -> dict[str, Any] | None:
        """Validate an invite code.

        Args:
            code: Invite code to validate

        Returns:
            Invite code record if valid, None if invalid/expired/used

        Raises:
            ValueError: If validation fails

        """
        try:
            supabase = get_supabase_client()

            result = (
                supabase.table("invite_codes")
                .select("*")
                .eq("code", code.upper())
                .execute()
            )

            if not result.data:
                logger.warning("Invite code not found", code=code)
                return None

            invite = result.data[0]

            # Check if expired
            expires_at = datetime.fromisoformat(
                invite["expires_at"].replace("Z", "+00:00")
            )
            if datetime.now(UTC) > expires_at:
                logger.warning("Invite code expired", code=code)
                return None

            # Check if already used
            if invite["used_by"] is not None:
                logger.warning("Invite code already used", code=code)
                return None

            logger.info("Invite code validated", code=code)
            return invite

        except Exception as e:
            logger.error("Failed to validate invite code", error=str(e))
            raise ValueError(f"Failed to validate invite code: {e}")

    @staticmethod
    async def use_invite(code: str, user_id: str) -> dict[str, Any]:
        """Mark an invite code as used.

        Args:
            code: Invite code to mark as used
            user_id: User ID that used the code

        Returns:
            Updated invite code record

        Raises:
            ValueError: If update fails

        """
        try:
            supabase = get_supabase_client()

            result = (
                supabase.table("invite_codes")
                .update(
                    {
                        "used_by": user_id,
                        "used_at": datetime.now(UTC).isoformat(),
                    }
                )
                .eq("code", code.upper())
                .execute()
            )

            logger.info("Invite code used", code=code, user_id=user_id)
            return result.data[0] if result.data else {}

        except Exception as e:
            logger.error("Failed to use invite code", error=str(e))
            raise ValueError(f"Failed to use invite code: {e}")

    @staticmethod
    async def list_active_invites(domain_id: str | None = None) -> list[dict[str, Any]]:
        """List active invite codes.

        Args:
            domain_id: Filter by domain (optional)

        Returns:
            List of active invite codes

        """
        try:
            supabase = get_supabase_client()

            query = supabase.table("invite_codes").select("*")

            if domain_id:
                query = query.eq("domain_id", domain_id)

            # Filter for active codes
            query = query.is_("used_by", "null")
            result = query.gt(
                "expires_at",
                datetime.now(UTC).isoformat(),
            ).execute()

            return result.data or []

        except Exception as e:
            logger.error("Failed to list invite codes", error=str(e))
            return []


class UserModel:
    """User database model."""

    @staticmethod
    async def get_user_by_id(user_id: str) -> dict[str, Any] | None:
        """Get user by ID."""
        try:
            supabase = get_supabase_client()

            result = (
                supabase.table("users").select("*").eq("id", user_id).single().execute()
            )

            return result.data if result.data else None

        except Exception as e:
            logger.warning("Failed to get user", user_id=user_id, error=str(e))
            return None

    @staticmethod
    async def create_user(
        user_id: str, email: str, invite_code: str | None = None
    ) -> dict[str, Any]:
        """Create a new user record in database.

        Args:
            user_id: Supabase auth user ID
            email: User email
            invite_code: Invite code used (optional)

        Returns:
            Created user record

        """
        try:
            supabase = get_supabase_client()

            # Get invite details if code provided
            role = "contributor"
            domain_id = None

            if invite_code:
                invite = await InviteCodeModel.validate_invite(invite_code)
                if invite:
                    role = invite.get("role", "contributor")
                    domain_id = invite.get("domain_id")

            result = (
                supabase.table("users")
                .insert(
                    {
                        "id": user_id,
                        "email": email,
                        "role": role,
                        "domain_id": domain_id,
                        "created_at": datetime.now(UTC).isoformat(),
                    }
                )
                .execute()
            )

            logger.info("User created", user_id=user_id, email=email)
            return result.data[0] if result.data else {}

        except Exception as e:
            logger.error("Failed to create user", error=str(e))
            raise ValueError(f"Failed to create user: {e}")
