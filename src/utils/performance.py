import time
from functools import wraps
import torch
import psutil
import gc
from typing import Optional, Callable

class PerformanceMonitor:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        
    def start(self):
        torch.cuda.empty_cache()
        gc.collect()
        self.start_time = time.time()
        
    def end(self):
        self.end_time = time.time()
        
    @property
    def elapsed_time(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
        
    @staticmethod
    def get_gpu_memory_usage():
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / 1024**2  # MB
        return 0
        
    @staticmethod
    def get_cpu_memory_usage():
        return psutil.Process().memory_info().rss / 1024**2  # MB

def measure_performance(func: Optional[Callable] = None, *, name: str = ""):
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            monitor = PerformanceMonitor()
            monitor.start()
            
            initial_gpu_mem = monitor.get_gpu_memory_usage()
            initial_cpu_mem = monitor.get_cpu_memory_usage()
            
            try:
                result = await f(*args, **kwargs)
                return result
            finally:
                monitor.end()
                final_gpu_mem = monitor.get_gpu_memory_usage()
                final_cpu_mem = monitor.get_cpu_memory_usage()
                
                print(f"\nPerformance metrics for {name or f.__name__}:")
                print(f"Time elapsed: {monitor.elapsed_time:.2f} seconds")
                print(f"GPU memory change: {final_gpu_mem - initial_gpu_mem:.2f} MB")
                print(f"CPU memory change: {final_cpu_mem - initial_cpu_mem:.2f} MB")
                
        return wrapper
        
    if func is None:
        return decorator
    return decorator(func)