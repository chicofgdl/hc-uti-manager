from providers.implementations.banco.user_postgres_provider import UserProvider

class UserController:

    def __init__(self, provider: UserProvider):
        self.provider = provider

    async def register(self, username: str, password: str, role: str) -> None:
        if role not in ["enfermeiro_uti", "enfermeiro_cirurgia"]:
            raise ValueError("Role inválido")
        await self.provider.create_user(username, password, role)

    async def authenticate(self, username: str, password: str) -> dict:
        user = await self.provider.authenticate_user(username, password)
        if not user:
            raise ValueError("Credenciais inválidas")
        return user