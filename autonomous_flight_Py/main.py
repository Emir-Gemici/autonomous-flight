import os
import signal
import time
from multiprocessing import Barrier, Event, Lock, Manager, Process

import cv2
import numpy as np
from pymavlink import mavutil

from process_monitor import system_monitor
from recording_video import rec
from route_tracking import infinity_flight
from target_detection import find_target
from utils import (
    go_to_position,
    send_velocity,
    set_arm,
    set_mode,
    set_param,
    signal_handler,
    takeoff,
    trigger_relay,
)


def image_process(frame, flag):
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([140, 255, 255])

    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([160, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    if flag == 0:
        mask_red1 = cv2.inRange(hsv_frame, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv_frame, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        mask_blue = cv2.inRange(hsv_frame, lower_blue, upper_blue)
        mask = cv2.bitwise_or(mask_red, mask_blue)
    elif flag == 1:
        mask = cv2.inRange(hsv_frame, lower_blue, upper_blue)
    elif flag == 2:
        mask_red1 = cv2.inRange(hsv_frame, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv_frame, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask_red1, mask_red2)
    else:
        mask = np.zeros(hsv_frame.shape[:2], dtype=np.uint8)

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    filter_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 100]

    return filter_contours


def take_off_process(
    dron,
    takeoff_speed,
    land_speed,
    last_land_speed,
    flight_altitude
):
    set_param(dron, "WPNAV_SPEED_UP", takeoff_speed)
    set_param(dron, "WPNAV_SPEED_DN", land_speed)
    set_param(dron, "LAND_SPEED", last_land_speed)
    print("Parametreler ayarlandi")

    if dron.flightmode != "STABILIZE":
        set_mode(dron, 'STABILIZE')
        time.sleep(2)

    set_mode(dron, 'GUIDED')
    print("Guided moda alindi")
    time.sleep(2.5)

    set_arm(dron)
    print("Dron arm edildi")
    time.sleep(2.5)

    print("Kalkis basliyor...")
    takeoff(dron, flight_altitude)
    time.sleep(flight_altitude + 5)
    print("Kalkis tamamlandi")


def main():
    try:
        flight_altitude = 15
        resolution = [1280, 720]
        fps = 12

        takeoff_speed = 700
        land_speed = 200
        last_land_speed = 75

        print("Dron ile MavLink baglantisi kuruluyor...")

        dron = mavutil.mavlink_connection('udp:127.0.0.1:14550')

        dron.wait_heartbeat()
        print("MavLink baglantasi kuruldu")

        time.sleep(3)

        barrier = Barrier(4)
        target_event = Event()
        manager2 = Manager()
        flag2 = manager2.Value('b', True)
        lock = Lock()

        take_off_process(
            dron,
            takeoff_speed,
            land_speed,
            last_land_speed,
            flight_altitude
        )

        process_recorder = Process(
            target=rec,
            args=(barrier, flag2, resolution, lock, fps)
        )

        process_detector = Process(
            target=find_target,
            args=(
                barrier,
                target_event,
                dron,
                resolution,
                flight_altitude,
                lock,
                fps,
                image_process,
                send_velocity,
                trigger_relay,
            )
        )

        process_navigator = Process(
            target=infinity_flight,
            args=(
                barrier,
                target_event,
                dron,
                flight_altitude,
                go_to_position,
            )
        )

        process_recorder.start()
        process_detector.start()
        process_navigator.start()

        pids_dict = {
            "Recorder": process_recorder.pid,
            "Detector": process_detector.pid,
            "Navigator": process_navigator.pid,
            "Main": os.getpid()
        }

        process_monitor = Process(
            target=system_monitor,
            args=(pids_dict, barrier, flag2,)
        )

        time.sleep(1)
        process_monitor.start()

        signal.signal(
            signal.SIGINT,
            signal_handler(dron, flag2, process_navigator)
        )
        signal.signal(
            signal.SIGTERM,
            signal_handler(dron, flag2, process_navigator)
        )

        process_navigator.join()
        print("Rota tamamlandi")
        print("Inis basliyor...")
        set_mode(dron, 'LAND')
        time.sleep(flight_altitude * 3)
        print("Inis tamamlandi")

        print("Kamera paylasimi sonlandiriliyor...")
        flag2.value = False

        if process_monitor.is_alive():
            process_monitor.join(timeout=2)

        if process_recorder.is_alive():
            process_recorder.join(timeout=2)
        print("Kamera paylasimi sona erdi")

        if process_detector.is_alive():
            print("Hedef bulma processi sonlandiriliyor...")
            process_detector.terminate()
            process_detector.join()
            print("Hedef bulma processi sonlandirildi")

        set_mode(dron, 'STABILIZE')

        print("Otonom ucus sonlandi")

    except Exception as e:
        print(f"Hata: {e}")


if __name__ == '__main__':
    main()
