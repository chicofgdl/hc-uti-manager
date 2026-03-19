import pytest

from src.providers.implementations.banco.solicitacao_postgress_provider import (
    SolicitacaoReservaProvider,
)
from src.providers.implementations.banco.transferencia_postgress import (
    TransferenciaPostgresProvider,
)


class _FakeMappingsResult:
    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row


class _FakeResult:
    def __init__(self, row=None, scalar=None):
        self._row = row
        self._scalar = scalar

    def mappings(self):
        return _FakeMappingsResult(self._row)

    def scalar_one(self):
        if self._scalar is None:
            raise AssertionError("scalar_one() chamado sem valor configurado")
        return self._scalar


class _BeginContext:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def begin(self):
        return _BeginContext()

    async def execute(self, statement, params=None):
        self.calls.append((str(statement), params))
        if not self._results:
            raise AssertionError("execute() chamado mais vezes do que o esperado")
        return self._results.pop(0)


@pytest.mark.asyncio
async def test_reserva_duplicate_active_request_is_blocked():
    session = _FakeSession(
        [
            _FakeResult(),
            _FakeResult(row={"id": 12, "status": "PENDENTE"}),
        ]
    )
    provider = SolicitacaoReservaProvider(session)

    with pytest.raises(ValueError, match="solicitação de reserva ativa"):
        await provider.criar(prontuario=77001, idade=60, especialidade="Cardiologia")

    assert len(session.calls) == 2
    assert "pg_advisory_xact_lock" in session.calls[0][0]
    assert "FROM solicitacoes_reserva" in session.calls[1][0]


@pytest.mark.asyncio
async def test_reserva_create_succeeds_without_active_request():
    session = _FakeSession(
        [
            _FakeResult(),
            _FakeResult(row=None),
            _FakeResult(scalar=33),
        ]
    )
    provider = SolicitacaoReservaProvider(session)

    created_id = await provider.criar(prontuario=77001, idade=60, especialidade="Cardiologia")

    assert created_id == 33
    assert len(session.calls) == 3
    assert "INSERT INTO solicitacoes_reserva" in session.calls[2][0]


@pytest.mark.asyncio
async def test_transfer_duplicate_active_request_is_blocked():
    session = _FakeSession(
        [
            _FakeResult(),
            _FakeResult(row={"id": 18, "status": "ACEITA"}),
        ]
    )
    provider = TransferenciaPostgresProvider(session)

    with pytest.raises(ValueError, match="solicitação de transferência ativa"):
        await provider.criar(
            {
                "prontuario_paciente": 77001,
                "idade_paciente": 60,
                "especialidade_paciente": "Cardiologia",
            }
        )

    assert len(session.calls) == 2
    assert "pg_advisory_xact_lock" in session.calls[0][0]
    assert "FROM solicitacoes_transferencia" in session.calls[1][0]
