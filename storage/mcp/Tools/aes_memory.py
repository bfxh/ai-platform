#!/usr/bin/env python3
"""
UE5 AES Key Memory Scanner
从运行中的UE5游戏进程内存中扫描AES密钥

原理：UE5在加载Pak时会将AES密钥存储在内存中的FCoreDelegates::GetPakEncryptionKeyDelegate
密钥是32字节(256位)，通常在特定的内存结构中

用法：
1. 先启动游戏
2. 运行此脚本: python aes_memory.py RoboQuest
"""
import ctypes
import ctypes.wintypes
import sys
import struct
import re
from pathlib import Path

# Windows API
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04
PAGE_READONLY = 0x02
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.wintypes.DWORD),
        ("Protect", ctypes.wintypes.DWORD),
        ("Type", ctypes.wintypes.DWORD),
    ]

def find_process(name):
    """查找进程PID"""
    import subprocess
    result = subprocess.run(['tasklist', '/fi', f'imagename eq {name}*', '/fo', 'csv', '/nh'],
                          capture_output=True, text=True)
    for line in result.stdout.strip().split('\n'):
        if line.strip():
            parts = line.strip('"').split('","')
            if len(parts) >= 2:
                try:
                    return int(parts[1])
                except:
                    pass
    return None

def scan_memory(pid):
    """扫描进程内存中的AES密钥"""
    handle = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not handle:
        print(f"无法打开进程 {pid}，需要管理员权限")
        return []
    
    keys = []
    address = 0
    mbi = MEMORY_BASIC_INFORMATION()
    regions_scanned = 0
    bytes_scanned = 0
    
    print(f"扫描进程 PID={pid} 的内存...")
    
    while kernel32.VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        # 只扫描已提交的可读内存
        if (mbi.State == MEM_COMMIT and 
            mbi.Protect in (PAGE_READWRITE, PAGE_READONLY, PAGE_EXECUTE_READ, PAGE_EXECUTE_READWRITE) and
            mbi.RegionSize < 100 * 1024 * 1024):  # 跳过超大区域
            
            try:
                buf = ctypes.create_string_buffer(mbi.RegionSize)
                bytes_read = ctypes.c_size_t(0)
                if kernel32.ReadProcessMemory(handle, ctypes.c_void_p(mbi.BaseAddress), buf, mbi.RegionSize, ctypes.byref(bytes_read)):
                    data = buf.raw[:bytes_read.value]
                    bytes_scanned += len(data)
                    
                    # 搜索0x+64字符十六进制
                    for m in re.finditer(rb'0x([0-9A-Fa-f]{64})', data):
                        key = "0x" + m.group(1).decode('ascii')
                        addr = mbi.BaseAddress + m.start()
                        if key not in [k[0] for k in keys]:
                            keys.append((key, addr, "memory_hex"))
                            print(f"  [HEX] {key[:30]}... @ 0x{addr:X}")
                    
                    # 搜索base64编码的32字节
                    import base64
                    for m in re.finditer(rb'([A-Za-z0-9+/]{43}=)', data):
                        try:
                            decoded = base64.b64decode(m.group(1))
                            if len(decoded) == 32 and len(set(decoded)) > 15:
                                key = "0x" + decoded.hex().upper()
                                addr = mbi.BaseAddress + m.start()
                                if key not in [k[0] for k in keys]:
                                    keys.append((key, addr, "memory_b64"))
                                    print(f"  [B64] {key[:30]}... @ 0x{addr:X}")
                        except:
                            pass
                    
                    regions_scanned += 1
            except:
                pass
        
        # 移到下一个区域
        address = mbi.BaseAddress + mbi.RegionSize
        if address <= mbi.BaseAddress:
            break
    
    kernel32.CloseHandle(handle)
    print(f"\n扫描完成: {regions_scanned} 个内存区域, {bytes_scanned/1024/1024:.1f} MB")
    return keys

def main():
    game_name = sys.argv[1] if len(sys.argv) > 1 else "RoboQuest"
    
    print(f"查找进程: {game_name}...")
    pid = find_process(game_name)
    
    if not pid:
        print(f"未找到 {game_name} 进程。请先启动游戏！")
        print(f"\n提示：启动游戏后再运行此脚本")
        sys.exit(1)
    
    print(f"找到进程 PID={pid}")
    
    keys = scan_memory(pid)
    
    print(f"\n{'='*60}")
    print(f"共找到 {len(keys)} 个可能的AES密钥")
    print(f"{'='*60}")
    
    if keys:
        output = Path(f"D:/搞阶跃的/{game_name}_AES_Keys.txt")
        with open(output, 'w') as f:
            for key, addr, source in keys:
                f.write(f"{key}  # addr=0x{addr:X}, source={source}\n")
                print(f"\n  {key}")
                print(f"  地址: 0x{addr:X}, 来源: {source}")
        print(f"\n密钥已保存: {output}")
        print(f"\n在FModel中使用：Directory > AES > 粘贴密钥")
    else:
        print("\n未在内存中找到AES密钥")
        print("可能原因：")
        print("  1. 游戏还没加载到主菜单（等游戏完全启动后再扫描）")
        print("  2. 需要管理员权限运行此脚本")
        print("  3. 密钥使用了非标准存储方式")

if __name__ == '__main__':
    main()
