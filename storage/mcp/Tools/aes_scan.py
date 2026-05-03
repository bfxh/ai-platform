#!/usr/bin/env python3
"""
AES Key Scanner - 从UE游戏exe中扫描AES-256密钥

原理：UE游戏的AES密钥通常以特定模式存储在exe中
- 0x开头的64字符十六进制字符串
- 或base64编码的32字节数据
- 或直接的32字节二进制数据在特定结构附近
"""
import sys
import re
import struct
from pathlib import Path

def scan_aes_from_exe(exe_path):
    """从exe文件中扫描可能的AES-256密钥"""
    exe_path = Path(exe_path)
    if not exe_path.exists():
        print(f"文件不存在: {exe_path}")
        return []
    
    print(f"扫描: {exe_path}")
    print(f"大小: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    with open(exe_path, 'rb') as f:
        data = f.read()
    
    keys = []
    
    # 方法1: 搜索0x开头的64字符十六进制字符串
    print("\n[方法1] 搜索0x+64字符十六进制...")
    hex_pattern = rb'0x([0-9A-Fa-f]{64})'
    for m in re.finditer(hex_pattern, data):
        key = "0x" + m.group(1).decode('ascii')
        offset = m.start()
        if key not in [k[0] for k in keys]:
            keys.append((key, offset, "hex_0x"))
            print(f"  找到: {key[:20]}...{key[-10:]} @ offset {offset}")
    
    # 方法2: 搜索纯64字符十六进制（不带0x前缀）
    print("\n[方法2] 搜索纯64字符十六进制...")
    # 在ASCII字符串区域搜索
    ascii_hex = rb'(?<![0-9A-Fa-f])([0-9A-Fa-f]{64})(?![0-9A-Fa-f])'
    count = 0
    for m in re.finditer(ascii_hex, data):
        key_bytes = m.group(1)
        # 过滤掉全0或全F的
        if key_bytes == b'0' * 64 or key_bytes == b'F' * 64 or key_bytes == b'f' * 64:
            continue
        # 检查是否在可读字符串区域
        start = max(0, m.start() - 4)
        context = data[start:m.start()]
        key = "0x" + key_bytes.decode('ascii')
        if key not in [k[0] for k in keys]:
            keys.append((key, m.start(), "hex_plain"))
            count += 1
            if count <= 10:
                print(f"  找到: {key[:20]}...{key[-10:]} @ offset {m.start()}")
    if count > 10:
        print(f"  ... 共 {count} 个")
    
    # 方法3: 搜索base64编码的32字节密钥（44字符base64）
    print("\n[方法3] 搜索base64编码密钥...")
    import base64
    b64_pattern = rb'([A-Za-z0-9+/]{43}=)'
    b64_count = 0
    for m in re.finditer(b64_pattern, data):
        try:
            decoded = base64.b64decode(m.group(1))
            if len(decoded) == 32:
                key = "0x" + decoded.hex().upper()
                if key not in [k[0] for k in keys]:
                    keys.append((key, m.start(), "base64"))
                    b64_count += 1
                    if b64_count <= 5:
                        print(f"  找到: {key[:20]}...{key[-10:]} @ offset {m.start()}")
        except:
            pass
    if b64_count > 5:
        print(f"  ... 共 {b64_count} 个")
    
    # 方法4: 搜索UE特定的密钥结构
    print("\n[方法4] 搜索UE密钥结构...")
    # UE中AES密钥通常在FNamedAESKey结构附近
    # 搜索 "EncryptionKey" 字符串附近的数据
    for keyword in [b'EncryptionKey', b'AES', b'PakEncryption', b'CryptoKeys']:
        for m in re.finditer(keyword, data):
            # 在关键词后面100字节内搜索32字节的非零数据
            region = data[m.start():m.start()+200]
            for offset in range(len(keyword), len(region)-32):
                chunk = region[offset:offset+32]
                # 检查是否像密钥（非零，高熵）
                if len(set(chunk)) > 20 and chunk != b'\x00' * 32:
                    key = "0x" + chunk.hex().upper()
                    if key not in [k[0] for k in keys]:
                        keys.append((key, m.start()+offset, f"near_{keyword.decode()}"))
                        print(f"  找到(near {keyword.decode()}): {key[:20]}... @ {m.start()+offset}")
                    break
    
    return keys

def main():
    if len(sys.argv) < 2:
        print("用法: python aes_scan.py <游戏exe路径>")
        print("示例: python aes_scan.py D:\\Games\\MyGame\\MyGame.exe")
        sys.exit(1)
    
    exe_path = sys.argv[1]
    keys = scan_aes_from_exe(exe_path)
    
    print(f"\n{'='*60}")
    print(f"扫描完成，共找到 {len(keys)} 个可能的AES密钥")
    print(f"{'='*60}")
    
    if keys:
        print("\n最可能的密钥（按来源排序）：")
        # 优先显示hex_0x类型的
        sorted_keys = sorted(keys, key=lambda k: {'hex_0x': 0, 'near_EncryptionKey': 1, 'near_PakEncryption': 1, 'base64': 2, 'hex_plain': 3}.get(k[2], 4))
        for i, (key, offset, source) in enumerate(sorted_keys[:10]):
            print(f"\n  [{i+1}] {key}")
            print(f"      来源: {source}, 偏移: {offset}")
        
        # 保存到文件
        output = Path("D:/搞阶跃的/RoboQuest_AES_Keys.txt")
        with open(output, 'w') as f:
            for key, offset, source in sorted_keys:
                f.write(f"{key}  # source={source}, offset={offset}\n")
        print(f"\n所有密钥已保存到: {output}")
    else:
        print("\n未找到AES密钥。可能需要：")
        print("  1. 用Dumper-7注入运行中的游戏进程")
        print("  2. 搜索社区数据库")

if __name__ == '__main__':
    main()
