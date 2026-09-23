from fastapi.testclient import TestClient

from backend.main import app

def test_health_returns_ok():
    client = TestClient(app)
    
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
def test_create_repository_accepts_valid_payload(repository_client):
    client = TestClient(app)
    
    payload = {
        "name": "CodeAtlas",
        "source_url": "http://example.com/codeatlas",
    }
    
    response = repository_client.post("/repositories", json=payload)
    
    assert response.status_code == 201
    
    save_repository = response.json()
    
    assert save_repository["id"] > 0
    assert save_repository["name"] == payload["name"]
    assert save_repository["source_url"] == payload["source_url"]

    
def test_create_repository_rejects_missing_source_url():
    client = TestClient(app)
    
    response = client.post("/repositories", json={"name": "CodeAtlas"})
    
    assert response.status_code == 422
    
def test_list_repositories_returns_empty_list(repository_client):
    response = repository_client.get("/repositories")
    
    assert response.status_code == 200
    assert response.json() == []
    
def test_list_repositories_returns_created_repository(repository_client):
    payload = {
        "name": "CodeAtlas", 
        "source_url": "http://example.com/codeatlas",
    }
    
    create_response = repository_client.post("/repositories", json=payload)
    
    assert create_response.status_code == 201
    
    created_repository = create_response.json()
    list_response = repository_client.get("/repositories")
    
    assert list_response.status_code == 200
    assert list_response.json() == [created_repository]
    
def test_delete_repository_removes_it_from_list(repository_client):
    payload = {
        "name": "CodeAtlas",
        "source_url": "http://example.com/codeatlas",
    }
    
    create_response = repository_client.post("/repositories", json=payload)
    
    assert create_response.status_code == 201
    
    created_repository = create_response.json()
    repository_id = created_repository["id"]
    
    delete_response = repository_client.delete(
        f"/repositories/{repository_id}"
    )
    
    assert delete_response.status_code == 204
    
    list_response = repository_client.get("/repositories")
    
    assert list_response.status_code == 200
    assert list_response.json() == []