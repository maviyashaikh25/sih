import os
import sys
sys.path.insert(0, os.path.abspath("."))

from ai_pipeline.video_processor import VideoStreamProcessor

def test_video_inference():
    print("Testing VideoStreamProcessor on data/sample_cctv_feed.mp4...")
    processor = VideoStreamProcessor(camera_id="CAM_CP_01", enable_api_post=False)
    processor.process_video_file(
        video_path="data/sample_cctv_feed.mp4",
        output_path="data/annotated_cctv_feed.mp4",
        max_frames=60,
        display=False
    )
    print("Video inference completed successfully! Annotated output at data/annotated_cctv_feed.mp4")

if __name__ == "__main__":
    test_video_inference()
