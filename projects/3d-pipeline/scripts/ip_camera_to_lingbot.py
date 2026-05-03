"""
IP摄像头 → LingBot-Map 实时3D重建
将手机IP摄像头视频流实时送入LingBot-Map进行流式重建
"""
import argparse
import cv2
import os
import sys
import time
import numpy as np
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="IP Camera to LingBot-Map")
    parser.add_argument("--url", type=str, required=True, help="IP camera URL, e.g. http://192.168.1.100:8080/video")
    parser.add_argument("--output_dir", type=str, default="/python/projects/3d-pipeline/01_phone_capture/frames", help="Output frames directory")
    parser.add_argument("--fps", type=int, default=5, help="Frames per second to capture")
    parser.add_argument("--max_frames", type=int, default=0, help="Max frames to capture (0=unlimited)")
    parser.add_argument("--preview", action="store_true", help="Show preview window")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Connecting to IP camera: {args.url}")
    cap = cv2.VideoCapture(args.url)

    if not cap.isOpened():
        print(f"ERROR: Cannot connect to {args.url}")
        print("Make sure:")
        print("  1. Phone and PC are on the same WiFi")
        print("  2. IP camera app is running on phone")
        print("  3. URL is correct (try /video endpoint)")
        sys.exit(1)

    print(f"Connected! Capturing at {args.fps} FPS...")
    print(f"Frames saved to: {args.output_dir}")
    print("Press 'q' to stop, 's' to save current frame manually")

    frame_interval = 1.0 / args.fps
    frame_count = 0
    last_capture = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Lost connection, retrying...")
                cap.release()
                time.sleep(2)
                cap = cv2.VideoCapture(args.url)
                continue

            now = time.time()
            if now - last_capture >= frame_interval:
                frame_count += 1
                filename = os.path.join(args.output_dir, f"frame_{frame_count:06d}.jpg")
                cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                last_capture = now

                if frame_count % 10 == 0:
                    print(f"  Captured {frame_count} frames...")

                if args.max_frames > 0 and frame_count >= args.max_frames:
                    print(f"Reached max frames ({args.max_frames})")
                    break

            if args.preview:
                cv2.imshow("IP Camera", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    manual_path = os.path.join(args.output_dir, f"manual_{frame_count:06d}.jpg")
                    cv2.imwrite(manual_path, frame)
                    print(f"  Saved manual frame: {manual_path}")

    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        cap.release()
        if args.preview:
            cv2.destroyAllWindows()
        print(f"\nTotal frames captured: {frame_count}")
        print(f"Saved to: {args.output_dir}")
        print(f"\nNow run LingBot-Map:")
        print(f"  cd /python\\projects\\lingbot-map")
        print(f"  python demo.py --model_path checkpoints\\lingbot-map-long.pt --image_folder {args.output_dir} --mask_sky --offload_to_cpu --num_scale_frames 2 --use_sdpa")

if __name__ == "__main__":
    main()
