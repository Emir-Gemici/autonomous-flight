import cv2
import time
import os

# GStreamer uyarılarını gizle

# GStreamer pipeline
gst_pipeline = (
    "udpsrc port=5600 "
    "caps=application/x-rtp,media=video,clock-rate=90000,encoding-name=H264 ! "
    "rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw,format=BGR ! "
    "appsink drop=true sync=false"
)

print("🚁 Drone Video Stream")
print(f"OpenCV: {cv2.__version__}")

camera = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

if not camera.isOpened():
    print("❌ Kamera açılamadı!")
    print("Kontrol: GStreamer, Port 5600, Video stream")
    exit(1)

print("✅ Kamera açıldı - Stream dinleniyor...")
print("Çıkmak için 'q' tuşuna basın\n")

frame_count = 0
start_time = time.time()

try:
    while True:
        ret, frame = camera.read()

        if ret:
            frame_count += 1

            # İlk frame
            if frame_count == 1:
                print(f"✅ Stream başladı - Boyut: {frame.shape[1]}x{frame.shape[0]}\n")

            # Her 60 frame'de FPS göster
            if frame_count % 60 == 0:
                fps = frame_count / (time.time() - start_time)
                print(f"Frame: {frame_count} | FPS: {fps:.1f}")

            cv2.imshow("Drone Video", frame)

        # 5 saniye içinde frame gelmezse çık
        if frame_count == 0 and time.time() - start_time > 5:
            print("⚠️  Timeout - Video stream gelmiyor!")
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\n✅ Sonlandırıldı")

finally:
    if frame_count > 0:
        fps = frame_count / (time.time() - start_time)
        print(f"\n📊 Toplam: {frame_count} frame | Ort. FPS: {fps:.1f}")
    camera.release()
    cv2.destroyAllWindows()

    cv2.destroyAllWindows()
