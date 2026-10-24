import time

import numpy as np

START_POS = (0.0, 0.0)
ELLIPSE_A = 130.0
ELLIPSE_B = 65.0
N_SAMPLES = 800
ROTATE_DEG = 90.0

WAIT_AFTER_DROP = 0.25
WAIT_NORMAL = 0.30
EVENT_CHECK_INTERVAL = 0.25


def infinity_flight(barrier, event, dron, flight_altitude, fonk):
    try:
        t0 = np.pi / 2
        t = np.linspace(t0, t0 - 2 * np.pi, N_SAMPLES, endpoint=True)

        x_full = ELLIPSE_A * np.cos(t)
        y_full = ELLIPSE_B * np.sin(t)

        x_full = x_full - x_full[0] + START_POS[0]
        y_full = y_full - y_full[0] + START_POS[1]

        rotate_rad = np.deg2rad(ROTATE_DEG)
        cos_r, sin_r = np.cos(rotate_rad), np.sin(rotate_rad)
        x_rot = x_full * cos_r - y_full * sin_r
        y_rot = x_full * sin_r + y_full * cos_r

        print("Rota izlemeye hazir")
        barrier.wait()
        print("Rota izleme basliyor")

        drop_count = 0
        last_print_progress = -10

        for i, (x, y) in enumerate(zip(x_rot, y_rot)):
            if event.is_set():
                drop_count += 1
                while event.is_set():
                    time.sleep(EVENT_CHECK_INTERVAL)

            progress = (i + 1) / N_SAMPLES * 100
            if progress - last_print_progress >= 10:
                print(f"Rotanin %{progress:.0f}'si tamamlandi")
                last_print_progress = progress

            fonk(dron, x, y, -flight_altitude)

            if drop_count >= 1:
                time.sleep(WAIT_AFTER_DROP)
            else:
                time.sleep(WAIT_NORMAL)

        time.sleep(10)

    except Exception as e:
        print(f"Rota takibi processi hatasi: {e}")
