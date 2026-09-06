# Backend

## Run locally

From this directory:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The health endpoint is available at `http://127.0.0.1:8000/api/v1/health`.

The screening endpoint is available at `POST http://127.0.0.1:8000/api/v1/screening`.

## Run tests

```powershell
python -m pytest -q
```