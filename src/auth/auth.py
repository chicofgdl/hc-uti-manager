import os
import jwt
import re
import secrets
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ldap3 import Server, Connection, ALL, SUBTREE, ALL_ATTRIBUTES
from ldap3.core.exceptions import LDAPBindError, LDAPSocketOpenError, LDAPException

from resources.database import get_app_db_session
from models.refresh_token import RefreshToken

load_dotenv()

# --- Configurações --- 
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS", 24))
REFRESH_TOKEN_EXP_DAYS = int(os.getenv("REFRESH_TOKEN_EXP_DAYS", 30))
# Por padrão desabilitamos a autenticação para facilitar testes locais.
# Para habilitar, defina AUTH_ENABLED=true no seu arquivo .env ou variáveis de ambiente.
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"

# Torna o scheme opcional se AUTH_ENABLED=false
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=AUTH_ENABLED)  # ← Modifique

# --- Interface e Implementações de Provedor de Autenticação ---

class AuthProviderInterface(ABC):
    """Interface para provedores de autenticação."""
    @abstractmethod
    async def authenticate_user(self, username, password) -> dict:
        pass

class MockAuthProvider(AuthProviderInterface):
    """Provedor de autenticação mock para desenvolvimento offline."""
    
    MOCK_USERS = {
        "admin": {
            "password": "admin",
            "displayName": ["Mock Admin"],
            "groups": ["GLO-SEC-HCPE-SETISD", "Users"],
            "email": "admin@mock.com"
        },
        "uti": {
            "password": "uti",
            "displayName": ["Enfermeiro UTI"],
            "groups": ["enfermeiro_uti"],
            "email": "uti@mock.com"
        },
        "cirurgia": {
            "password": "cirurgia",
            "displayName": ["Enfermeiro Cirurgia"],
            "groups": ["enfermeiro_cirurgia"],
            "email": "cirurgia@mock.com"
        }
    }
    
    async def authenticate_user(self, username, password) -> dict:
        print("--- Using Mock Authentication ---")
        user_data = self.MOCK_USERS.get(username)
        if user_data and user_data["password"] == password:
            print(f"Authentication successful for mock user: {username}")
            return {
                "username": username,
                **user_data
            }
        else:
            print(f"Authentication failed for mock user: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid mock credentials"
            )

class ActiveDirectoryAuthProvider(AuthProviderInterface):
    """Provedor de autenticação real usando LDAP/Active Directory."""
    def __init__(self):
        self.ad_url = os.getenv("AD_URL")
        self.ad_basedn = os.getenv("AD_BASEDN")
        self.ad_bind_user = os.getenv("AD_BIND_USER")
        self.ad_bind_password = os.getenv("AD_BIND_PASSWORD")
        if not self.ad_url or not self.ad_basedn:
            raise RuntimeError("Active Directory is not configured. Check .env file.")

    def _bind(self, user, password) -> Connection:
        server = Server(self.ad_url, get_info=ALL)
        return Connection(
            server,
            user=user,
            password=password,
            auto_bind=True,
            receive_timeout=10,
        )

    def _extract_user_info(self, entry, username) -> dict:
        attrs = entry.entry_attributes_as_dict
        user_info = {"username": username}

        groups_attr = attrs.get("memberOf") or []
        user_info["groups"] = [
            re.match(r"CN=([^,]+)", group).group(1)
            for group in groups_attr
            if re.match(r"CN=([^,]+)", group)
        ]

        for key, value in attrs.items():
            if key == "memberOf":
                continue
            if isinstance(value, list):
                user_info[key] = [str(v) for v in value]
            else:
                user_info[key] = str(value)

        return user_info

    async def authenticate_user(self, username, password) -> dict:
        print(f"--- Starting AD Authentication for user: {username} ---")
        user_conn = None
        search_conn = None
        try:
            user_bind_dn = f"EBSERHNET\\{username}"
            user_conn = self._bind(user_bind_dn, password)

            search_conn = user_conn
            if self.ad_bind_user and self.ad_bind_password:
                search_conn = self._bind(self.ad_bind_user, self.ad_bind_password)

            search_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
            search_conn.search(
                search_base=self.ad_basedn,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=ALL_ATTRIBUTES,
                size_limit=1,
            )

            if not search_conn.entries:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

            entry = search_conn.entries[0]
            user_info = self._extract_user_info(entry, username)

            print(f"--- AD Authentication successful for user: {username}. ---")
            return user_info

        except LDAPBindError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        except LDAPSocketOpenError:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AD server is down or unreachable")
        except LDAPException as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AD error: {e}")
        finally:
            if search_conn and search_conn is not user_conn and search_conn.bound:
                search_conn.unbind()
            if user_conn and user_conn.bound:
                user_conn.unbind()

class LocalAuthProvider(AuthProviderInterface):
    """Provedor de autenticação usando tabela local de usuários."""
    
    def __init__(self, session):
        self.session = session
    
    async def authenticate_user(self, username, password) -> dict:
        from providers.implementations.banco.user_postgres_provider import UserProvider
        provider = UserProvider(self.session)
        user = await provider.authenticate_user(username, password)
        if user:
            return user
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid local credentials")

# --- AuthHandler Principal ---

class AuthHandler:
    def __init__(self):
        # Lógica de troca: decide qual provedor usar na inicialização
        self.providers = []
        if os.getenv("AD_URL"):
            print("INFO: Using Active Directory authentication.")
            self.providers.append(ActiveDirectoryAuthProvider())
        else:
            print("WARNING: AD environment variables not found. Using Mock authentication.")
            self.providers.append(MockAuthProvider())
        
        # Always add local provider as fallback
        # But need session, so perhaps in authenticate_user
        self.local_provider = None

    async def authenticate_user(self, username, password, session=None):
        last_http_error: HTTPException | None = None
        # Try providers in order
        for provider in self.providers:
            try:
                return await provider.authenticate_user(username, password)
            except HTTPException as exc:
                last_http_error = exc
                continue
            except Exception:
                logging.exception("Unexpected error in auth provider %s", type(provider).__name__)
                continue
        
        # Try local users
        if session:
            local_provider = LocalAuthProvider(session)
            try:
                return await local_provider.authenticate_user(username, password)
            except HTTPException as exc:
                last_http_error = exc
            except Exception:
                # Avoid leaking DB/internal failures as 500 on login.
                logging.exception("Unexpected error in local auth provider")
        
        if last_http_error and last_http_error.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            raise last_http_error
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        to_encode.pop("password", None)
        if 'username' in to_encode:
            to_encode['sub'] = to_encode['username']
        expire = datetime.utcnow() + (expires_delta or timedelta(hours=JWT_EXP_HOURS))
        to_encode.update({"exp": expire})
        if not JWT_SECRET:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="JWT_SECRET not configured")
        return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")

    async def create_refresh_token(self, user_id: str, groups: list, db: AsyncSession) -> str:
        refresh_token_string = secrets.token_urlsafe(64)
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXP_DAYS)
        new_refresh_token = RefreshToken(user_id=user_id, token=refresh_token_string, groups=groups, expires_at=expires_at)
        db.add(new_refresh_token)
        await db.commit()
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
        if not AUTH_ENABLED:
            print("⚠️  WARNING: Authentication is DISABLED - using mock user")
            return {
                "username": "dev_user",
                "groups": ["GLO-SEC-HCPE-SETISD", "Users"],
                "email": "dev@localhost"
            }
        
        # Se AUTH_ENABLED=true mas token não foi fornecido
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        # Código original
        try:
            if not JWT_SECRET:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="JWT_SECRET not configured")
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    def require_role(self, required_role: str):
        def role_checker(token_data: dict = Depends(self.decode_token)):
            groups = token_data.get("groups", [])
            if required_role not in groups:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required role: {required_role}"
                )
            return token_data
        return role_checker

    def require_any_role(self, required_roles: list[str]):
        def role_checker(token_data: dict = Depends(self.decode_token)):
            groups = token_data.get("groups", [])
            if not any(role in groups for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required one of roles: {required_roles}"
                )
            return token_data
        return role_checker

# Instância única que será usada em toda a aplicação
auth_handler = AuthHandler()
