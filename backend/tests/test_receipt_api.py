from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_rejects_invalid_receipt_upload_content_type(authenticated_client):
    response = authenticated_client.post("/api/receipts/extract", files={"file": ("receipt.txt", b"not an image", "text/plain")})
    assert response.status_code == 415
    assert response.json()["detail"] == "Upload a JPEG, PNG, or WebP image."

def test_rejects_invalid_image_bytes(authenticated_client):
    response = authenticated_client.post("/api/receipts/extract", files={"file": ("receipt.png", b"not an image", "image/png")})
    assert response.status_code == 422
    assert response.json()["detail"] == "The uploaded file is not a valid image."
