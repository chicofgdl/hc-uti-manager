import sys
sys.path.insert(0, 'src')
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

resp = client.get('/solicitacoes-reserva')
print('GET status', resp.status_code)
print('GET body', resp.text)

resp2 = client.post('/solicitacoes-reserva', json={'prontuario':77001,'idade':40,'especialidade':'Teste'})
print('POST status', resp2.status_code)
print('POST body', resp2.text)
