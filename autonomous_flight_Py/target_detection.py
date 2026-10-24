import time
from multiprocessing import shared_memory

import cv2
import numpy as np


def find_target(
    barrier,
    event,
    dron,
    resolution,
    flight_altitude,
    lock,
    fps,
    fonk,
    fonk2,
    fonk3
):
    shm = None

    try:
        frame_w, frame_h, channels = resolution[0], resolution[1], 3
        dtype = np.uint8
        frame_shape = (frame_h, frame_w, channels)

        while True:
            try:
                shm = shared_memory.SharedMemory(
                    name="frame_shm",
                    create=False
                )
                break
            except FileNotFoundError:
                print("Paylasimli bellek bulunamadi")
                time.sleep(1)

        shm_frame = np.ndarray(frame_shape, dtype=dtype, buffer=shm.buf)

        border_limit = resolution[0] // 10

        thresholds = [
            [(90, 0.80), (55, 0.55), (35, 0.45), (25, 0.30), (4, 0.15)],
            [(90, 0.95), (55, 0.75), (35, 0.55), (25, 0.35), (4, 0.20)],
            [(90, 1.0), (55, 0.80), (35, 0.65), (25, 0.45), (4, 0.25)]
        ]

        dropped_count = 0
        flag = 0
        fps_counter = 0

        print("Hedef tespiti hazir")
        barrier.wait()
        print("Hedef tespiti basliyor")

        while dropped_count != 2:
            with lock:
                frame = shm_frame.copy()
            fps_counter += 1
            contours = fonk(frame, flag)

            cv2.imshow("Hedef Tespiti", frame)
            cv2.waitKey(1)

            if not event.is_set():
                flag = _process_search_mode(
                    contours,
                    flag,
                    event,
                    resolution,
                    border_limit
                )
            elif event.is_set():
                dropped_count, flag = _process_tracking_mode(
                    contours,
                    flag,
                    event,
                    resolution,
                    flight_altitude,
                    thresholds,
                    fps_counter,
                    dron,
                    fonk2,
                    fonk3,
                    dropped_count
                )

            time.sleep(1.0 / fps)

        if shm is not None:
            shm.close()

    except Exception as e:
        print(f"Hedef hizalama hatasi: {e}")

    finally:
        if shm is not None:
            shm.close()


def _process_search_mode(contours, flag, event, resolution, border_limit):
    for cnt in contours:
        approx = cv2.approxPolyDP(
            cnt,
            0.05 * cv2.arcLength(cnt, True),
            True
        )
        corners = len(approx)

        moments = cv2.moments(cnt)
        if moments["m00"] == 0:
            continue

        cx = int(moments["m10"] / moments["m00"])
        cy = int(moments["m01"] / moments["m00"])

        if (cx < border_limit or
                cx > (resolution[0] - border_limit) or
                cy < border_limit or
                cy > (resolution[1] - border_limit)):
            continue

        if flag == 0:
            if corners == 6:
                print("Mavi hedef bulundu")
                event.set()
                return 1
            elif corners == 3:
                print("Kirmizi hedef bulundu")
                event.set()
                return 2
        elif flag == 1:
            if corners == 6:
                print("Mavi hedef bulundu\n Hedef arama sona erdi.")
                event.set()
                break
        else:
            if corners == 3:
                print("Kirmizi hedef bulundu\n Hedef arama sona erdi.")
                event.set()
                break

    return flag


def _process_tracking_mode(
    contours,
    flag,
    event,
    resolution,
    flight_altitude,
    thresholds,
    fps_counter,
    dron,
    fonk2,
    fonk3,
    dropped_count
):
    for cnt in contours:
        approx = cv2.approxPolyDP(
            cnt,
            0.05 * cv2.arcLength(cnt, True),
            True
        )
        corners = len(approx)

        moments = cv2.moments(cnt)
        if moments["m00"] == 0:
            continue

        if flag == 1 and corners != 6:
            continue
        elif flag == 2 and corners != 3:
            continue

        cx = int(moments["m10"] / moments["m00"])
        cy = int(moments["m01"] / moments["m00"])

        error_x = cx - (resolution[0] // 2)
        error_y = cy - (resolution[1] // 2)

        if flight_altitude < 25:
            threshold_index = 0
        elif flight_altitude < 35:
            threshold_index = 1
        else:
            threshold_index = 2

        vx = next(
            (speed if error_x > 0 else -speed
             for limit, speed in thresholds[threshold_index]
             if abs(error_x) > limit),
            0.0
        )
        vy = next(
            (speed if error_y > 0 else -speed
             for limit, speed in thresholds[threshold_index]
             if abs(error_y) > limit),
            0.0
        )

        if fps_counter % 5 == 0 and fps_counter > 20:
            print(f"Hedefe olan uzaklik X:{error_x}, Y:{error_y}")

            if abs(error_x) < 150 and abs(error_y) < 150:
                fonk2(dron, -vy, vx)
                print(f"Hareket X:{vx}, Y:{vy}")
                time.sleep(0.35)
            elif abs(error_x) > abs(error_y):
                fonk2(dron, 0, vx)
                print(f"Hareket X: {vx}")
                time.sleep(0.35)
            else:
                fonk2(dron, -vy, 0)
                print(f"Hareket Y: {vy}")
                time.sleep(0.35)

        if abs(error_x) < 10 and abs(error_y) < 10:
            dropped_count += 1
            if flag == 1:
                print("Mavi hedefe yuk birakiliyor")
                time.sleep(2)
                flag = 2
                event.clear()
            else:
                print("Kirmizi hedefe yuk birakiliyor")
                time.sleep(2)
                flag = 1
                event.clear()
            break

    return dropped_count, flag