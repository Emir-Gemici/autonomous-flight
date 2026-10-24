import csv
import os
import time
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import psutil


def create_log_dir():
    log_dir = Path("Monitor_logs")
    log_dir.mkdir(exist_ok=True)
    return log_dir


def get_latest_file(log_dir="Monitor_logs"):
    log_path = Path(log_dir)
    csv_files = list(log_path.glob("monitor_log_*.csv"))

    if not csv_files:
        return None

    latest_file = max(csv_files, key=lambda p: p.stat().st_mtime)
    return str(latest_file)


def get_temp():
    try:
        with open(
            "/sys/class/thermal/thermal_zone6/temp",
            mode="r",
            encoding="utf-8"
        ) as f:
            return float(f.read()) / 1000.0
    except (FileNotFoundError, PermissionError):
        return 0.0


def system_monitor(process_dict, barrier, flag, interval=2.5):
    log_dir = create_log_dir()
    file_name = log_dir / f"monitor_log_file_{time.strftime('%Y%m%d_%H%M%S')}.csv"

    process_cache = {}

    for name, pid in process_dict.items():
        try:
            proc = psutil.Process(pid)
            proc.cpu_percent(interval=None)
            process_cache[name] = proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            print(f"Uyari: {name} sureci (PID: {pid}) bulunamadi.")

    target_names = list(process_dict.keys())

    with open(file_name, mode='w', newline='', encoding='utf-8') as f:
        try:
            writer = csv.writer(f)

            headers = ["Time_s", "Total_CPU_%", "Total_RAM_MB", "Temperature_C"]
            for name in target_names:
                headers.extend([f"{name}_CPU_%", f"{name}_RAM_MB"])
            writer.writerow(headers)

            print("Sistem izlemeye hazir")
            barrier.wait()
            start_time = time.time()

            while True:
                if not flag.value:
                    break

                current_time = round(time.time() - start_time, 2)

                total_cpu = 0
                total_ram = 0
                row_data = {}

                for name in target_names:
                    try:
                        proc = process_cache.get(name)

                        if proc is not None and proc.is_running():
                            c_cpu = proc.cpu_percent(interval=None)
                            c_ram = proc.memory_info().rss / 1024 / 1024

                            row_data[name] = {"cpu": c_cpu, "ram": c_ram}

                            total_cpu += c_cpu
                            total_ram += c_ram
                        else:
                            row_data[name] = {"cpu": 0, "ram": 0}

                    except (
                        psutil.NoSuchProcess,
                        psutil.AccessDenied,
                        psutil.ZombieProcess,
                        BrokenPipeError,
                        EOFError,
                        ConnectionResetError
                    ):
                        row_data[name] = {"cpu": 0, "ram": 0}
                        print(f"Uyari: {name} sureci bulunamadi.")

                temp = get_temp()

                row = [current_time, total_cpu, total_ram, temp]
                for name in target_names:
                    row.extend([
                        round(row_data[name]["cpu"], 2),
                        round(row_data[name]["ram"], 2)
                    ])

                writer.writerow(row)
                f.flush()

                time.sleep(interval)

        except Exception as e:
            print(f"Izleme hatasi: {e}")

    print("Sistem izleme sonlandiriliyor")


def plot_system_monitor():
    csv_path = get_latest_file()

    if not csv_path:
        print("CSV dosyasi bulunamadi")
        return

    df = pd.read_csv(csv_path)
    time_data = df["Time_s"]

    process_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle(
        'Sistem Performans Monitoru',
        fontsize=14,
        fontweight='bold'
    )

    cpu_columns = [
        col for col in df.columns
        if col.endswith('_CPU_%') and col != 'Total_CPU_%'
    ]
    process_names = [col.replace('_CPU_%', '') for col in cpu_columns]

    ax1 = axes[0]
    ax1.plot(
        time_data,
        df['Total_CPU_%'],
        linewidth=2,
        color='black',
        label='Toplam CPU'
    )

    for i, (name, col) in enumerate(zip(process_names, cpu_columns)):
        color = process_colors[i % len(process_colors)]
        ax1.plot(
            time_data,
            df[col],
            linewidth=1.5,
            color=color,
            label=name,
            linestyle='--'
        )

    ax1.set_ylabel('CPU (%)')
    ax1.set_title('CPU Kullanimi')
    ax1.legend(loc='upper right', fontsize=8)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.set_ylim(bottom=0)

    ax2 = axes[1]
    ax2.plot(
        time_data,
        df['Total_RAM_MB'],
        linewidth=2,
        color='purple',
        label='Toplam RAM'
    )

    ram_columns = [
        col for col in df.columns
        if col.endswith('_RAM_MB') and col != 'Total_RAM_MB'
    ]

    for i, col in enumerate(ram_columns):
        name = col.replace('_RAM_MB', '')
        color = process_colors[i % len(process_colors)]
        ax2.plot(
            time_data,
            df[col],
            linewidth=1.5,
            color=color,
            label=name,
            linestyle=':'
        )

    ax2.set_ylabel('RAM (MB)')
    ax2.set_title('Bellek Kullanimi')
    ax2.legend(loc='upper right', fontsize=8)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.set_ylim(bottom=0)

    ax3 = axes[2]
    temp_data = df['Temperature_C']
    ax3.plot(
        time_data,
        temp_data,
        linewidth=2,
        color='red',
        label='Sicaklik'
    )
    ax3.fill_between(time_data, temp_data, alpha=0.2, color='red')

    ax3.set_xlabel('Zaman (s)')
    ax3.set_ylabel('Sicaklik (C)')
    ax3.set_title('CPU Sicakligi')

    ax3.axhline(
        y=70,
        color='orange',
        linestyle='--',
        linewidth=1.5,
        label='Dikkat (70C)'
    )
    ax3.axhline(
        y=80,
        color='darkred',
        linestyle='--',
        linewidth=1.5,
        label='Kritik (80C)'
    )

    ax3.legend(loc='upper right', fontsize=8)
    ax3.grid(True, linestyle='--', alpha=0.5)
    ax3.set_ylim(bottom=0)

    plt.tight_layout()

    output_path = (
        Path("Monitor_logs") /
        f"system_monitor_plot_{time.strftime('%Y%m%d_%H%M%S')}.png"
    )
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Grafik kaydedildi: {output_path}")

    plt.show()
