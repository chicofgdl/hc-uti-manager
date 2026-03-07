from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from resources.database import Base

class Notificacao(Base):
    __tablename__ = "notificacoes"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), nullable=False)
    mensagem = Column(Text, nullable=False)
    role_destino = Column(String(50), nullable=False)
    lida = Column(Boolean, default=False, nullable=False)
    criada_em = Column(DateTime, server_default=func.now(), nullable=False)