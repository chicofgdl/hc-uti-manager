import os
import jwt
import ldap
import re
import secrets
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ..resources.database import get_app_db_session
from ..models.refresh_token import RefreshToken

load_dotenv()

AD_URL = os.getenv("AD_URL")
AD_BASEDN = os.getenv("AD_BASEDN")
AD_BIND_USER = os.getenv("AD_BIND_USER")
AD_BIND_PASSWORD = os.getenv("AD_BIND_PASSWORD")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS", 24))
REFRESH_TOKEN_EXP_DAYS = int(os.getenv("REFRESH_TOKEN_EXP_DAYS", 30))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

class AuthHandler:
    def authenticate_user(self, username, password):
        print(f"--- Starting AD Authentication for user: {username} ---")
        if not AD_URL or not AD_BASEDN:
            print("!!! ERROR: AD_URL or AD_BASEDN not configured in .env")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AD_URL or AD_BASEDN not configured in .env")

        l = None
        try:
            print(f"1. Initializing LDAP connection to: {AD_URL}")
            l = ldap.initialize(AD_URL)
            l.protocol_version = ldap.VERSION3
            l.set_option(ldap.OPT_REFERRALS, 0)

            user_bind_dn = f"EBSERHNET\\{username}"
            print(f"2. Attempting to bind with user DN: {user_bind_dn}")
            l.simple_bind_s(user_bind_dn, password)
            print("   -> User bind successful!")

            # Now that the user is authenticated, proceed to group search
            groups = []
            search_ldap_conn = None
            print("3. Preparing to search for user groups.")
            try:
                if AD_BIND_USER and AD_BIND_PASSWORD:
                    print("   -> Using dedicated bind user for search.")
                    search_ldap_conn = ldap.initialize(AD_URL)
                    search_ldap_conn.protocol_version = ldap.VERSION3
                    search_ldap_conn.set_option(ldap.OPT_REFERRALS, 0)
                    print(f"   -> Binding with bind user: {AD_BIND_USER}")
                    search_ldap_conn.simple_bind_s(AD_BIND_USER, AD_BIND_PASSWORD)
                    print("      -> Bind user successful!")
                else:
                    print("   -> No dedicated bind user. Using authenticated user's connection for search.")
                    search_ldap_conn = l

                search_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
                search_attribute = ["memberOf"]
                print(f"4. Performing LDAP search with:")
                print(f"   - Base DN: {AD_BASEDN}")
                print(f"   - Filter: {search_filter}")
                
                result_id = search_ldap_conn.search(AD_BASEDN, ldap.SCOPE_SUBTREE, search_filter, search_attribute)
                result_type, result_data = search_ldap_conn.result(result_id, 1)

                if result_data and result_data[0][1]:
                    user_entry = result_data[0][1]
                    if 'memberOf' in user_entry:
                        print("5. Found groups for user:")
                        for group_dn_bytes in user_entry['memberOf']:
                            group_dn = group_dn_bytes.decode('utf-8')
                            cn_match = re.match(r'CN=([^,]+)', group_dn)
                            if cn_match:
                                group_name = cn_match.group(1)
                                groups.append(group_name)
                                print(f"   - Found group: {group_name}")
                    else:
                        print("5. User has no 'memberOf' attribute.")
                else:
                    print("5. LDAP search returned no data for the user.")

                if search_ldap_conn and search_ldap_conn != l:
                    search_ldap_conn.unbind_s()

            except ldap.INVALID_CREDENTIALS:
                print(f"!!! ERROR: Invalid credentials for the BIND USER ({AD_BIND_USER}).")
                print("   -> Please check AD_BIND_USER and AD_BIND_PASSWORD in your .env file.")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid credentials for service account used for group search.")

            print(f"--- AD Authentication successful for user: {username}. Groups: {groups} ---")
            return {"username": username, "groups": groups}

        except ldap.INVALID_CREDENTIALS:
            print(f"!!! ERROR: Invalid credentials for user: {username}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        except ldap.SERVER_DOWN:
            print(f"!!! ERROR: AD server is down or unreachable at {AD_URL}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AD server is down or unreachable")
        except Exception as e:
            print(f"!!! ERROR: An unexpected error occurred during AD authentication: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AD connection or authentication error: {e}")
        finally:
            if l:
                print("6. Unbinding initial LDAP connection.")
                l.unbind_s()

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=JWT_EXP_HOURS)
        to_encode.update({"exp": expire})
        if not JWT_SECRET:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="JWT_SECRET not configured")
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
        return encoded_jwt

    async def create_refresh_token(self, user_id: str, groups: list, db: AsyncSession) -> str:
        refresh_token_string = secrets.token_urlsafe(64)
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXP_DAYS)
        
        new_refresh_token = RefreshToken(
            user_id=user_id,
            token=refresh_token_string,
            groups=groups,
            expires_at=expires_at
        )
        db.add(new_refresh_token)
        await db.commit()
        await db.refresh(new_refresh_token)
        return refresh_token_string

    async def verify_refresh_token(self, refresh_token: str, db: AsyncSession):
        stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
        result = await db.execute(stmt)
        token_obj = result.scalar_one_or_none()

        if not token_obj or token_obj.expires_at < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
        
        return token_obj

    async def invalidate_refresh_token(self, refresh_token: str, db: AsyncSession):
        stmt = delete(RefreshToken).where(RefreshToken.token == refresh_token)
        await db.execute(stmt)
        await db.commit()

    def decode_token(self, token: str = Depends(oauth2_scheme)):
        try:
            if not JWT_SECRET:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="JWT_SECRET not configured")
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

auth_handler = AuthHandler()
