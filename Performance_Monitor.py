import time
import psutil
import openpyxl
import subprocess
from pynvml import *
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
import numpy as np
import asyncio
import sys
import os
import trio

class PerformanceMonitor():
    def __init__(self, command):
        self.command = command
        self.process = None
        self.psutil_process = None
        self.handle = None
        self.root = tk.Tk()
        self.root.title("")
        self.root.geometry("1500x600")
        self.tree_frame = ttk.Frame(self.root)
        self.tree_frame.pack(expand=True, fill="both")
        self.tree_scrollbar = ttk.Scrollbar(self.tree_frame)
        self.tree = ttk.Treeview(self.tree_frame, yscrollcommand=self.tree_scrollbar.set)
        self.tree_scrollbar.config(command=self.tree.yview)
        self.tree_scrollbar.pack(side="right", fill="y")
        self.tree.pack(expand=True, fill="both")
        self.tree["columns"] = ("Time (s)", "CPU (%)", "RAM (MB)", "GPU (%)", "VRAM (MB)")
        self.tree.heading("#0", text="Index")
        self.tree.heading("Time (s)", text="Time (s)")
        self.tree.heading("CPU (%)", text="CPU (%)")
        self.tree.heading("RAM (MB)", text="RAM (MB)")
        self.tree.heading("GPU (%)", text="GPU (%)")
        self.tree.heading("VRAM (MB)", text="VRAM (MB)")
        self.wb = openpyxl.Workbook()
        self.ws = self.wb.active
        self.ws.append(["Time (s)", "CPU (%)", "RAM (MB)", "GPU (%)", "VRAM (MB)"])
        self.total_cpu = 0
        self.total_ram = 0
        self.total_gpu = 0
        self.total_vram = 0
        self.record_count = 0

    async def start_process(self):
        if len(self.command) > 1 and os.path.isfile(self.command[1]):
            self.process = subprocess.Popen(self.command)
            self.root.title(f"Performance Monitor for {self.command[1]}")
        elif len(self.command) > 0:
            self.process = psutil.Process(int(self.command[0]))
            self.root.title(f"Performance Monitor for PID {self.command[0]}")
        else:
            print("Invalid command format. Please provide a PID or a script to execute.")
            sys.exit(1)
        try:
            self.psutil_process = psutil.Process(self.process.pid)
        except psutil.NoSuchProcess:
            print("Failed to create subprocess.")
            sys.exit(1)
        self.handle = nvmlDeviceGetHandleByIndex(0)

    async def get_record_interval(self, time_sec):
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

    async def monitor(self):
        start_time = time.perf_counter()
        next_record_time = 0
        try:
            while True:
                current_time = time.perf_counter()
                time_sec = current_time - start_time

                # if not self.psutil_process.is_running(): break
                if (not self.psutil_process.is_running() if os.name == 'nt' else self.psutil_process.status() == psutil.STATUS_ZOMBIE): break
                time.sleep(0.1)

                cpu_usage, ram_usage = await self.get_cpu_ram_usage()
                gpu_usage, vram_usage = await self.get_gpu_usage()

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
                    self.ws.append([round(time_sec, 3), round(cpu_usage, 3), round(ram_usage, 3), round(gpu_usage, 3), round(vram_usage, 3)])
                    self.tree.insert("", "end", text=str(self.record_count), values=(round(time_sec, 3), round(cpu_usage, 3), round(ram_usage, 3), round(gpu_usage, 3), round(vram_usage, 3)))
                    next_record_time = time_sec + await self.get_record_interval(time_sec)
                    self.tree.yview_moveto(1)
                    self.root.update()
        finally:
            await self.print_average_metrics()
            self.wb.save("Performance.xlsx")
            print("save the Performance.xlsx")

            # df = pd.read_excel("Performance.xlsx")

            # x_data = df["Time (s)"]
            # y_data_cpu = df["CPU (%)"]
            # y_data_ram = df["RAM (MB)"]
            # y_data_gpu = df["GPU (%)"]
            # y_data_vram = df["VRAM (MB)"]

            # plt.figure(figsize=(15, 8))

            # plt.plot(x_data, y_data_cpu, label='CPU', linewidth=2, color='r', marker='', markersize=6, markevery=20)
            # plt.plot(x_data, y_data_ram, label='RAM', linewidth=2, color='y', marker='', markersize=6, markevery=20)
            # plt.plot(x_data, y_data_gpu, label='GPU', linewidth=2, color='b', marker='', markersize=6, markevery=20)
            # plt.plot(x_data, y_data_vram, label='VRAM', linewidth=2, color='g', marker='', markersize=6, markevery=20)


            # plt.xticks(np.arange(0, max(x_data)+1, 10))
            # plt.yticks(np.arange(0, max(max(y_data_cpu), max(y_data_ram), max(y_data_gpu), max(y_data_vram))+1, 10))
            # plt.xlabel("Time (s)")
            # plt.ylabel('Average')
            # plt.title("Performance Metrics")

            # plt.legend()
            # plt.grid()

            # plt.show()

    async def get_cpu_ram_usage(self):
        try:
            cpu_usage = self.psutil_process.cpu_percent(interval=None)
            ram_usage = self.psutil_process.memory_info().rss / (1024 ** 2)
            return cpu_usage, ram_usage
        except psutil.NoSuchProcess:
            return None, None

    async def get_gpu_usage(self):
        gpu_process_info = nvmlDeviceGetComputeRunningProcesses(self.handle)
        gpu_usage, vram_usage = 0.0, 0.0
        for proc in gpu_process_info:
            if proc.pid == self.process.pid:
                gpu_usage = proc.usedGpuMemory * 100 / nvmlDeviceGetMemoryInfo(self.handle).total
                vram_usage = proc.usedGpuMemory / (1024 ** 2)
                break
        return gpu_usage, vram_usage

    async def print_average_metrics(self):
        if self.record_count > 0:
            avg_cpu = self.total_cpu / self.record_count
            avg_ram = self.total_ram / self.record_count
            avg_gpu = self.total_gpu / self.record_count
            avg_vram = self.total_vram / self.record_count
            print(f"Average CPU: {avg_cpu:.3f}% | Average RAM: {avg_ram:.3f}MB | Average GPU: {avg_gpu:.3f}% | Average VRAM: {avg_vram:.3f}MB")

    @staticmethod
    async def run():
        nvmlInit()

        if len(sys.argv) < 2: print("Usage: Performance.py <command>"); sys.exit(1)
        
        command = sys.argv[1:]
        monitor = PerformanceMonitor(command)
        await monitor.start_process()
        await monitor.monitor()

        nvmlShutdown()

if __name__ == "__main__":
    trio.run(PerformanceMonitor.run)
