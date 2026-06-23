from app.api.v1.endpoints import dev as dev_endpoint


def test_deve_iniciar_job_qa_padrao(client_dev):
    response = client_dev.post("/api/v1/dev/qa/executar?mode=padrao")

    assert response.status_code == 200
    payload = response.json()
    assert "job_id" in payload
    assert payload["status"] in {"queued", "running"}


def test_deve_retornar_404_para_job_inexistente(client_dev):
    response = client_dev.get("/api/v1/dev/qa/jobs/job-inexistente")

    assert response.status_code == 404


def test_deve_rejeitar_modo_invalido(client_dev):
    response = client_dev.post("/api/v1/dev/qa/executar?mode=invalido")

    assert response.status_code == 400


def test_deve_consultar_status_job_existente(client_dev, monkeypatch):
    fake_job = {
        "job_id": "qa-job-123",
        "mode": "padrao",
        "command": "python -m pytest tests -m not integration",
        "cwd": "C:/Projetos/viagens_labs",
        "status": "running",
        "success": None,
        "exit_code": None,
        "duration_seconds": None,
        "output": "[QA] executando...",
        "created_at": 0,
        "started_at": 0,
        "finished_at": None,
        "pid": 1234,
    }

    monkeypatch.setattr(dev_endpoint, "QA_JOBS", {"qa-job-123": fake_job})

    response = client_dev.get("/api/v1/dev/qa/jobs/qa-job-123")

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == "qa-job-123"
    assert payload["status"] == "running"
    assert "executando" in payload["output"]


def test_deve_listar_catalogo_de_suites_qa(client_dev):
    response = client_dev.get("/api/v1/dev/qa/suites")

    assert response.status_code == 200
    payload = response.json()
    assert "suites" in payload
    assert len(payload["suites"]) >= 3
    assert {s["mode"] for s in payload["suites"]} >= {"padrao", "integration", "completa"}


def test_deve_cancelar_job_em_fila(client_dev, monkeypatch):
    fake_job = {
        "job_id": "qa-job-fila",
        "mode": "padrao",
        "command": "python -m pytest tests -m not integration",
        "cwd": "C:/Projetos/viagens_labs",
        "status": "queued",
        "success": None,
        "exit_code": None,
        "duration_seconds": None,
        "output": "[QA] Job enfileirado...\n",
        "created_at": 0,
        "started_at": None,
        "finished_at": None,
        "pid": None,
        "canceled": False,
    }

    monkeypatch.setattr(dev_endpoint, "QA_JOBS", {"qa-job-fila": fake_job})
    monkeypatch.setattr(dev_endpoint, "QA_PROCESSES", {})

    response = client_dev.post("/api/v1/dev/qa/jobs/qa-job-fila/cancelar")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "canceled"
    assert dev_endpoint.QA_JOBS["qa-job-fila"]["status"] == "canceled"


def test_deve_cancelar_job_em_execucao(client_dev, monkeypatch):
    class _FakeProc:
        def __init__(self):
            self.terminated = False

        def terminate(self):
            self.terminated = True

        def wait(self, timeout=None):
            return 0

        def kill(self):
            self.terminated = True

    fake_proc = _FakeProc()
    fake_job = {
        "job_id": "qa-job-running",
        "mode": "padrao",
        "command": "python -m pytest tests -m not integration",
        "cwd": "C:/Projetos/viagens_labs",
        "status": "running",
        "success": None,
        "exit_code": None,
        "duration_seconds": None,
        "output": "[QA] executando...\n",
        "created_at": 0,
        "started_at": 0,
        "finished_at": None,
        "pid": 1234,
        "canceled": False,
    }

    monkeypatch.setattr(dev_endpoint, "QA_JOBS", {"qa-job-running": fake_job})
    monkeypatch.setattr(dev_endpoint, "QA_PROCESSES", {"qa-job-running": fake_proc})

    response = client_dev.post("/api/v1/dev/qa/jobs/qa-job-running/cancelar")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "canceling"
    assert fake_proc.terminated is True
    assert dev_endpoint.QA_JOBS["qa-job-running"]["status"] == "canceling"
