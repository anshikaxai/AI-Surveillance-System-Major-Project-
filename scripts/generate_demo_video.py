import sys
sys.path.insert(0, '.')
import cv2
import numpy as np
from pathlib import Path

W, H, FPS, DURATION_S = 1024, 576, 25, 20

def draw_scene(frame, t):
    frame[:] = (20, 25, 35)
    cv2.rectangle(frame, (0, H - 60), (W, H), (35, 50, 70), -1)
    for x in range(0, W, 80):
        cv2.line(frame, (x, H - 30), (x + 40, H - 30), (220, 200, 80), 3)
    cv2.rectangle(frame, (200, 100), (500, 400), (0, 0, 255), 2)
    cv2.putText(frame, "ROI: Main Gate", (205, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    cv2.rectangle(frame, (550, 200), (800, 450), (255, 0, 0), 2)
    cv2.putText(frame, "ROI: Parking Zone", (555, 218), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    car = np.array([[0, 40], [70, 40], [80, 10], [150, 10], [160, 40], [210, 40], [210, 110], [0, 110]], dtype=np.int32)
    car_x = int(520 + np.sin(t * 0.7) * 120)
    car_y = 340
    shifted_car = car + [car_x, car_y]
    cv2.fillPoly(frame, [shifted_car], (30, 80, 150))
    cv2.rectangle(frame, (car_x + 105, car_y + 5), (car_x + 148, car_y + 45), (120, 180, 230), -1)
    plate_box = (car_x + 75, car_y + 75, car_x + 135, car_y + 100)
    cv2.rectangle(frame, (plate_box[0], plate_box[1]), (plate_box[2], plate_box[3]), (240, 240, 240), -1)
    cv2.putText(frame, "AB-123-CD", (plate_box[0] + 4, plate_box[2]//3 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (10, 10, 10), 2)
    for person_i in range(5):
        phase = t * (0.5 + person_i * 0.08)
        base_x = 220 + (person_i * 45 + int(np.sin(phase) * 60 + 50)) % 240
        x = min(base_x, 480)
        ground_y = 380
        speed = 4 + person_i
        walk_phase = np.sin(phase * speed) * 2
        head = (x, ground_y - 90)
        cv2.ellipse(frame, head, (9, 10), 0, 0, 360, (210, 180, 160), -1)
        body_top = (x, ground_y - 78)
        body_bot = (x, ground_y - 15)
        cv2.line(frame, body_top, body_bot, (60, 100 + person_i * 20, 140), 6)
        cv2.line(frame, body_bot, (x + int(walk_phase * 4), ground_y), (30, 60, 100), 4)
        cv2.line(frame, body_bot, (x - int(walk_phase * 4), ground_y), (30, 60, 100), 4)
    loiterer_x = 600 + int(np.sin(t * 0.15) * 15)
    cv2.ellipse(frame, (loiterer_x, 280), (10, 11), 0, 0, 360, (180, 200, 255), -1)
    cv2.line(frame, (loiterer_x, 292), (loiterer_x, 355), (80, 40, 140), 6)
    cv2.line(frame, (loiterer_x, 355), (loiterer_x + 3, 380), (30, 20, 60), 4)
    cv2.line(frame, (loiterer_x, 355), (loiterer_x - 3, 380), (30, 20, 60), 4)
    if 5 < t % 15 < 10:
        for extra in range(6):
            x = 230 + extra * 25
            cv2.ellipse(frame, (x, 360 - 90), (8, 9), 0, 0, 360, (200, 200, 200), -1)
            cv2.line(frame, (x, 360 - 78), (x, 360 - 15), (100, 60, 60), 5)
    stamp = f"t={t:.1f}s  |  1024x576 @ {FPS}fps  |  AI Edge Surveillance Demo"
    cv2.rectangle(frame, (0, 0), (W, 30), (0, 0, 0))
    cv2.putText(frame, stamp, (10, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 255, 100), 1)


def main():
    out_path = Path("data/sample_demo.mp4")
    out_path.parent.mkdir(exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, FPS, (W, H))
    total = FPS * DURATION_S
    for i in range(total):
        t = i / FPS
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        draw_scene(frame, t)
        writer.write(frame)
        if i % (FPS * 5) == 0:
            print(f"  Written {i}/{total} frames ({i/total*100:.0f}%)")
    writer.release()
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"Wrote demo video: {out_path} ({size_mb:.2f} MB, {DURATION_S}s)")


if __name__ == "__main__":
    main()
