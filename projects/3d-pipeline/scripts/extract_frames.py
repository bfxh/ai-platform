"""
视频抽帧脚本 - 将视频文件抽取为图片序列
支持 mp4, avi, mov, mkv 等格式
"""
import argparse
import cv2
import os
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Extract frames from video files")
    parser.add_argument("--input", type=str, required=True, help="Input video file or directory")
    parser.add_argument("--output", type=str, default="/python/projects/3d-pipeline/01_phone_capture/frames", help="Output frames directory")
    parser.add_argument("--fps", type=int, default=5, help="Target FPS (0=all frames)")
    parser.add_argument("--quality", type=int, default=95, help="JPEG quality (1-100)")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    input_path = Path(args.input)
    video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.3gp'}

    if input_path.is_file():
        videos = [input_path]
    elif input_path.is_dir():
        videos = [f for f in input_path.iterdir() if f.suffix.lower() in video_exts]
        if not videos:
            image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
            images = [f for f in input_path.iterdir() if f.suffix.lower() in image_exts]
            if images:
                print(f"Found {len(images)} images, copying to output...")
                import shutil
                for i, img in enumerate(sorted(images)):
                    dst = os.path.join(args.output, f"frame_{i+1:06d}{img.suffix}")
                    shutil.copy2(str(img), dst)
                print(f"Done! {len(images)} images copied to: {args.output}")
                return
            print(f"No video or image files found in: {args.input}")
            sys.exit(1)
    else:
        print(f"Path not found: {args.input}")
        sys.exit(1)

    total_frames = 0
    for video_path in videos:
        print(f"Processing: {video_path.name}")
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"  ERROR: Cannot open {video_path}")
            continue

        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = max(1, int(video_fps / args.fps)) if args.fps > 0 else 1

        print(f"  Video FPS: {video_fps}, Total frames: {total_video_frames}")
        print(f"  Extracting every {frame_interval} frame(s)")

        count = 0
        saved = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if count % frame_interval == 0:
                saved += 1
                filename = os.path.join(args.output, f"frame_{total_frames + saved:06d}.jpg")
                cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, args.quality])
            count += 1
            if count % 500 == 0:
                print(f"  Progress: {count}/{total_video_frames} frames, saved {saved}")

        cap.release()
        total_frames += saved
        print(f"  Extracted {saved} frames from {video_path.name}")

    print(f"\nTotal frames extracted: {total_frames}")
    print(f"Saved to: {args.output}")
    print(f"\nNow run LingBot-Map:")
    print(f"  cd /python\\projects\\lingbot-map")
    print(f"  python demo.py --model_path checkpoints\\lingbot-map-long.pt --image_folder {args.output} --mask_sky --offload_to_cpu --num_scale_frames 2 --use_sdpa")

if __name__ == "__main__":
    main()
