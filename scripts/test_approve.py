from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

resp = client.post('/solicitacoes-reserva/1/aprovar', json={'lto_lto_id':'L100'})
print(resp.status_code)
print(resp.text)
