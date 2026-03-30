from fastapi.testclient import TestClient

from dso2.src.api.main import app


client = TestClient(app)


def test_health() -> None:
	response = client.get("/bo2/health")
	assert response.status_code == 200
	payload = response.json()
	assert payload["status"] == "ok"
	assert payload["product_count"] > 0
	assert payload["rag_chunk_count"] > 0


def test_retrieve() -> None:
	response = client.post(
		"/bo2/rag/retrieve",
		json={"question": "dry cough product", "top_k": 3},
	)
	assert response.status_code == 200
	payload = response.json()
	assert len(payload["contexts"]) > 0


def test_ask() -> None:
	response = client.post(
		"/bo2/rag/ask",
		json={
			"question": "Which product can help with dry cough?",
			"avatar_id": "ava_med",
			"audience": "physicians",
			"top_k": 3,
		},
	)
	assert response.status_code == 200
	payload = response.json()
	assert payload["avatar"]["avatar_id"] == "ava_med"
	assert "answer" in payload
	assert len(payload["contexts"]) > 0
