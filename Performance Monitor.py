import time
import psutil
import openpyxl
import subprocess
from pynvml import *

class PerformanceMonitor:
    def __init__(self, command):
        self.command = command
        self.process = None
        self.psutil_process = None
        self.handle = None
        self.wb = openpyxl.Workbook()
        self.ws = self.wb.active
        self.ws.append(["Time (s)", "CPU (%)", "RAM (MB)", "GPU (%)", "VRAM (MB)"])
        self.total_cpu = 0
        self.total_ram = 0
        self.total_gpu = 0
        self.total_vram = 0
        self.record_count = 0

    def start_process(self):
        self.process = subprocess.Popen(self.command)
        try:
            self.psutil_process = psutil.Process(self.process.pid)
        except psutil.NoSuchProcess:
            print("Failed to create subprocess.")
            sys.exit(1)
        self.handle = nvmlDeviceGetHandleByIndex(0)

    def get_record_interval(self, time_sec):
        if time_sec < 10:
            return 0.1
        elif time_sec < 60:
            return 1
        elif time_sec < 3600:
            return 60
        elif time_sec < 36000:
            return 300
        else:
            return 600

    def monitor(self):
        start_time = time.perf_counter()
        next_record_time = 0
        try:
            while True:
                current_time = time.perf_counter()
                time_sec = current_time - start_time

                if not self.psutil_process.is_running():
                    break
                time.sleep(0.1)

                cpu_usage, ram_usage = self.get_cpu_ram_usage()
                gpu_usage, vram_usage = self.get_gpu_usage()

                cpu_usage = 0 if cpu_usage is None else cpu_usage
                ram_usage = 0 if ram_usage is None else ram_usage
                gpu_usage = 0 if gpu_usage is None else gpu_usage
                vram_usage = 0 if vram_usage is None else vram_usage

                self.total_cpu += cpu_usage
                self.total_ram += ram_usage
                self.total_gpu += gpu_usage
                self.total_vram += vram_usage
                self.record_count += 1

                if time_sec >= next_record_time:
                    self.ws.append([round(time_sec, 1), cpu_usage, ram_usage, gpu_usage, vram_usage])
                    next_record_time = time_sec + self.get_record_interval(time_sec)
        finally:
            self.print_average_metrics()
            self.wb.save("Performance.xlsx")

    def get_cpu_ram_usage(self):
        try:
            cpu_usage = self.psutil_process.cpu_percent(interval=None)
            ram_usage = self.psutil_process.memory_info().rss / (1024 ** 2)
            return cpu_usage, ram_usage
        except psutil.NoSuchProcess:
            return None, None

    def get_gpu_usage(self):
        gpu_process_info = nvmlDeviceGetComputeRunningProcesses(self.handle)
        gpu_usage, vram_usage = 0.0, 0.0
        for proc in gpu_process_info:
            if proc.pid == self.process.pid:
                gpu_usage = proc.usedGpuMemory * 100 / nvmlDeviceGetMemoryInfo(self.handle).total
                vram_usage = proc.usedGpuMemory / (1024 ** 2)
                break
        return gpu_usage, vram_usage

    def print_average_metrics(self):
        if self.record_count > 0:
            avg_cpu = self.total_cpu / self.record_count
            avg_ram = self.total_ram / self.record_count
            avg_gpu = self.total_gpu / self.record_count
            avg_vram = self.total_vram / self.record_count
            print(f"Average CPU: {avg_cpu:.3f}% | Average RAM: {avg_ram:.3f}MB | "
                  f"Average GPU: {avg_gpu:.3f}% | Average VRAM: {avg_vram:.3f}MB")

if __name__ == "__main__":
    nvmlInit()

    if len(sys.argv) < 2:
        print("Usage: Performance.py <command>")
        sys.exit(1)

    command = sys.argv[1:]
    monitor = PerformanceMonitor(command)
    monitor.start_process()
    monitor.monitor()

    nvmlShutdown()
