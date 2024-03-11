# Performance Monitor
![python-version](https://img.shields.io/badge/python->=3.10.12-green.svg)  
![ubuntu-version](https://img.shields.io/badge/ubuntu-=22.04-red)

Suport OS: Linux
## Overview
The Performance Monitor is a Python script designed to monitor and log the performance metrics of a specific process on your system. It tracks CPU, RAM, GPU usage, and VRAM utilization over time. This tool is particularly useful for analyzing the resource consumption of applications, especially in development and testing environments.

## Features
- Monitors CPU and RAM usage.
- Monitors GPU and VRAM usage (requires NVIDIA GPU).
- Logs performance data to an Excel file for easy visualization and analysis.
- Adjustable data recording intervals based on the monitoring duration.
- Calculates and displays average resource usage statistics.

## Dependencies
To run the Performance Monitor, you need to have the following Python libraries installed:
- `time`
- `psutil` for CPU and RAM monitoring.
- `openpyxl` for logging data to an Excel file.
- `pynvml` for NVIDIA GPU monitoring.

Install these dependencies using pip:
```sh=
pip3 install -r requirements.txt
```

## Installation
Clone the repository or download the `PerformanceMonitor.py` script to your local machine.

## Usage
1. Open a terminal or command prompt.
2. Navigate to the directory containing `PerformanceMonitor.py`.
3. Run the script with the command you want to monitor as an argument:
```sh=
python3 PerformanceMonitor.py <command or PID number>
```
Replace `<command or PID number>` with the command you wish to monitor (e.g., `python your_script.py` or `55899`).

## Output
The script will create an Excel file named `Performance.xlsx` in the same directory, containing the performance metrics logged during the monitoring period.
