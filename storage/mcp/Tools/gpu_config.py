# GPU配置
# RTX 4060 Ti 8GB

import torch
import os

# 强制使用GPU
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"

# 检查GPU
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
GPU_NAME = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
GPU_MEMORY = torch.cuda.get_device_properties(0).total_memory / 1024**3 if torch.cuda.is_available() else 0

print(f"Using device: {DEVICE}")
print(f"GPU: {GPU_NAME}")
print(f"GPU Memory: {GPU_MEMORY:.2f} GB")

# GPU优化配置
GPU_CONFIG = {
    "device": DEVICE,
    "gpu_name": GPU_NAME,
    "gpu_memory": GPU_MEMORY,
    "batch_size": 4,  # 根据8GB显存调整
    "mixed_precision": True,  # 使用混合精度
    "compile_models": True,  # 编译模型加速
}

def get_device():
    """获取计算设备"""
    return DEVICE

def to_gpu(tensor):
    """将张量移到GPU"""
    if isinstance(tensor, torch.Tensor):
        return tensor.to(DEVICE)
    return tensor

def clear_gpu_cache():
    """清理GPU缓存"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

def check_gpu_memory_available(required_gb=2.0):
    """检查是否有足够的GPU显存"""
    if not torch.cuda.is_available():
        return False, "GPU not available"
    
    allocated = torch.cuda.memory_allocated(0) / 1024**3
    reserved = torch.cuda.memory_reserved(0) / 1024**3
    total = torch.cuda.get_device_properties(0).total_memory / 1024**3
    free = total - reserved
    
    if free >= required_gb:
        return True, f"Free: {free:.2f} GB"
    else:
        return False, f"Insufficient memory. Free: {free:.2f} GB, Required: {required_gb} GB"

async def wait_for_gpu_memory(required_gb=2.0, timeout=60, check_interval=5):
    """等待GPU显存可用"""
    import asyncio
    start_time = asyncio.get_event_loop().time()
    
    while True:
        available, msg = check_gpu_memory_available(required_gb)
        if available:
            return True, msg
        
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > timeout:
            return False, f"Timeout waiting for GPU memory: {msg}"
        
        print(f"⏳ Waiting for GPU memory... {msg}")
        clear_gpu_cache()
        await asyncio.sleep(check_interval)
