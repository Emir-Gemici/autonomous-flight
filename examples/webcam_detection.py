import cv2
import numpy as np

# Çözünürlük ayarları
FRAME_W = 1280
FRAME_H = 720
BORDER_LIMIT = FRAME_W // 10

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Çözünürlüğü zorla
    frame = cv2.resize(frame, (FRAME_W, FRAME_H))

    # 1. Gaussian Blur - Gürültü azaltma
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)

    hsv_frame = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([140, 255, 255])

    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([160, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    mask_red1 = cv2.inRange(hsv_frame, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv_frame, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
    mask_blue = cv2.inRange(hsv_frame, lower_blue, upper_blue)
    mask = cv2.bitwise_or(mask_red, mask_blue)

    # 2. Morfolojik işlemler
    kernel = np.ones((5, 5), np.uint8)

    # Opening - Küçük gürültüleri temizle
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    # Closing - Delikleri kapat
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Dilation - Şekilleri büyüt, kopukları birleştir
    mask = cv2.dilate(mask, kernel, iterations=1)

    # Bitwise AND uygulanmış görüntü
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # Kenar sınırlarını çiz (target_detection'daki gibi)
    cv2.rectangle(
        frame, (BORDER_LIMIT, BORDER_LIMIT),
        (FRAME_W - BORDER_LIMIT, FRAME_H - BORDER_LIMIT), (0, 165, 255), 2
    )
    cv2.rectangle(
        result, (BORDER_LIMIT, BORDER_LIMIT),
        (FRAME_W - BORDER_LIMIT, FRAME_H - BORDER_LIMIT), (0, 165, 255), 2
    )

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    filter_contours = [
        cnt for cnt in contours if cv2.contourArea(cnt) > 750
    ]

    for cnt in filter_contours:
        approx = cv2.approxPolyDP(
            cnt, 0.04 * cv2.arcLength(cnt, True), True
        )
        area = cv2.contourArea(cnt)

        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # Sınır kontrolü
            in_border = (
                cx >= BORDER_LIMIT and
                cx <= (FRAME_W - BORDER_LIMIT) and
                cy >= BORDER_LIMIT and
                cy <= (FRAME_H - BORDER_LIMIT)
            )

            color = (0, 255, 0) if in_border else (0, 0, 255)

            # Merkezi çiz
            cv2.circle(frame, (cx, cy), 5, color, -1)
            cv2.circle(result, (cx, cy), 5, color, -1)

            # Bilgileri merkeze yaz
            cv2.putText(
                frame, f"Area: {int(area)}", (cx + 10, cy - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2
            )
            cv2.putText(
                frame, f"({cx}, {cy})", (cx + 10, cy + 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2
            )

            # Sınır dışı uyarısı
            if not in_border:
                cv2.putText(
                    frame, "SINIR DISI!", (cx + 10, cy + 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2
                )

        # Basitleştirilmiş konturu çiz (approx)
        cv2.drawContours(frame, [approx], -1, (0, 255, 0), 2)
        cv2.drawContours(result, [approx], -1, (0, 255, 0), 2)

    cv2.imshow("Bilgisayarin Gordugu", frame)
    cv2.imshow("Basitlestirilmis Goruntu", result)

    # 'q' tuşu ile çıkış
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
