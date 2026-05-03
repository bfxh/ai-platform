#!/usr/bin/env python3
"""ASAR 文件解包工具 v3 - 正确解析 ASAR 格式"""

import json
import os
import struct
from pathlib import Path


def extract_asar(asar_path, output_dir):
    with open(asar_path, "rb") as f:
        # ASAR header: 4+4+4+4 bytes header, then JSON, then data
        pickle_size = struct.unpack("<I", f.read(4))[0]
        header_size = struct.unpack("<I", f.read(4))[0]
        json_size = struct.unpack("<I", f.read(4))[0]
        string_size = struct.unpack("<I", f.read(4))[0]

        # Read JSON header
        header_json = f.read(string_size).decode("utf-8")
        header = json.loads(header_json)

        # Data starts after header (aligned)
        data_offset = 16 + string_size
        if data_offset % 4 != 0:
            data_offset += 4 - (data_offset % 4)

        file_count = [0]

        def extract_node(node, dest_path):
            if "files" in node:
                os.makedirs(dest_path, exist_ok=True)
                for name, info in node["files"].items():
                    extract_node(info, os.path.join(dest_path, name))
            elif "offset" in node:
                offset = int(node["offset"])
                size = int(node["size"])
                f.seek(data_offset + offset)
                file_data = f.read(size)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "wb") as out:
                    out.write(file_data)
                file_count[0] += 1
                if file_count[0] % 500 == 0:
                    print(f"  ... {file_count[0]} files extracted")

        extract_node(header, output_dir)
        return file_count[0]


if __name__ == "__main__":
    targets = [
        (r"%SOFTWARE_DIR%\AI\QClaw\resources\app.asar", r"\python\extracted\QClaw"),
        (r"%SOFTWARE_DIR%\AI\StepFun\resources\app.asar", r"\python\extracted\StepFun"),
        (r"%SOFTWARE_DIR%\LDD\eIsland\resources\app.asar", r"\python\extracted\eIsland"),
    ]

    for asar_path, output_dir in targets:
        if not os.path.exists(asar_path):
            print(f"[SKIP] Not found: {asar_path}")
            continue

        asar_size = os.path.getsize(asar_path) / (1024 * 1024)
        print(f"\n{'='*60}")
        print(f"Extracting: {asar_path} ({asar_size:.1f} MB)")
        print(f"Output: {output_dir}")
        print(f"{'='*60}")

        try:
            count = extract_asar(asar_path, output_dir)
            print(f"OK: Extracted {count} files")
        except Exception as e:
            print(f"FAIL: {e}")
            import traceback

            traceback.print_exc()
