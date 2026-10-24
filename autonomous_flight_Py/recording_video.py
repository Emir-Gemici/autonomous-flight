import time
from multiprocessing import shared_memory

import cv2
import numpy as np


def rec(barrier, flag, resolution, lock, fps):
    shm = None

    try:
        try:
            old_shm = shared_memory.SharedMemory(
                name="frame_shm",
                create=False
            )
            old_shm.close()
            old_shm.unlink()
            print("Eski paylasimli bellek silindi")
        except FileNotFoundError:
            pass

        frame_w, frame_h, channels = resolution[0], resolution[1], 3
        dtype = np.uint8

        frame_shape = (frame_h, frame_w, channels)
        frame_bytes = np.prod(frame_shape) * np.dtype(dtype).itemsize

        shm = shared_memory.SharedMemory(
            name="frame_shm",
            create=True,
            size=frame_bytes
        )

        shm_frame = np.ndarray(frame_shape, dtype=dtype, buffer=shm.buf)
        print("Paylasimli bellek olusturuldu")

        gst_pipeline = (
            "udpsrc port=5600 "
            "caps=application/x-rtp,media=video,clock-rate=90000,"
            "encoding-name=H264 ! "
            "rtph264depay ! avdec_h264 ! videoconvert ! "
            "video/x-raw,format=BGR ! "
            "appsink drop=true sync=false"
        )

        camera = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

        if not camera.isOpened():
            print("Kamera acilamadi")
            raise RuntimeError("Kamera acilamadi")

        print("Kamera konfigurasyonlari yapildi\nVideo paylasimina hazir")
        barrier.wait()

        while flag.value:
            ret, frame = camera.read()

            with lock:
                shm_frame[:] = frame[:]

            time.sleep(1.0 / fps)

        camera.release()

        if shm is not None:
            try:
                shm.close()
                shm.unlink()
            except Exception:
                pass

    except Exception as e:
        print(f"Video paylasimi hatasi: {e}")

    finally:
        if shm is not None:
            try:
                shm.close()
                shm.unlink()
            except Exception:
                pass
