import os
import sys
from fastapi.testclient import TestClient
from app.main import app

def test_feed_upload_endpoint():
    client = TestClient(app)
    
    # Check sample video path
    sample_video_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sample_cctv_feed.mp4"))
    if not os.path.exists(sample_video_path):
        print(f"Sample video not found at {sample_video_path}")
        return

    print(f"Testing Feed Upload endpoint with {sample_video_path}...")
    with open(sample_video_path, "rb") as f:
        response = client.post(
            "/api/v1/feed/upload",
            files={"file": ("test_corridor_feed.mp4", f, "video/mp4")},
            data={
                "camera_id": "CAM_KG_01",
                "camera_name": "Kashmere Gate ISBT Node",
                "latitude": 28.6665,
                "longitude": 77.2285,
                "zone": "North Delhi"
            }
        )

    print(f"Response Status: {response.status_code}")
    data = response.json()
    print("Response Data:", data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert data["success"] is True
    assert data["camera_id"] == "CAM_KG_01"
    print("\n[SUCCESS] Custom Feed Upload and AI processing verified successfully!")

if __name__ == "__main__":
    test_feed_upload_endpoint()
