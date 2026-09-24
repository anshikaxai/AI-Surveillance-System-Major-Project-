from pathlib import Path
import time

import cv2
from ultralytics import YOLO


# =========================================================
# PROJECT / VIDEO
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

VIDEO_PATH = (
    PROJECT_ROOT
    / "demo_videos"
    / "basement_entry.mp4"
)

MODEL_PATH = "yolov8n.pt"


# =========================================================
# MODEL
# =========================================================

model = YOLO(MODEL_PATH)

# IMPORTANT:
# CPU is intentionally used for stability on macOS.
DEVICE = "cpu"

print(f"[CAM-001] YOLO running on: {DEVICE}")


# =========================================================
# PERFORMANCE SETTINGS
# =========================================================

TARGET_WIDTH = 960

TARGET_STREAM_FPS = 8

YOLO_IMAGE_SIZE = 256

JPEG_QUALITY = 55

CONFIDENCE = 0.35


# COCO classes
CLASS_NAMES = {
    0: "Person",
    1: "Bicycle",
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck",
}

VEHICLE_CLASSES = {
    1,
    2,
    3,
    5,
    7,
}


# =========================================================
# HELPERS
# =========================================================

def resize_frame(frame):

    height, width = frame.shape[:2]

    if width <= TARGET_WIDTH:
        return frame

    scale = TARGET_WIDTH / width

    new_height = int(
        height * scale
    )

    return cv2.resize(
        frame,
        (
            TARGET_WIDTH,
            new_height,
        ),
        interpolation=cv2.INTER_AREA,
    )


# =========================================================
# STREAM
# =========================================================

def generate_demo_frames():

    cap = cv2.VideoCapture(
        str(VIDEO_PATH)
    )

    if not cap.isOpened():

        raise RuntimeError(
            f"Unable to open demo video: "
            f"{VIDEO_PATH}"
        )


    source_fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if (
        source_fps is None
        or source_fps <= 0
    ):
        source_fps = 30


    process_every_n_frames = max(
        1,
        round(
            source_fps
            / TARGET_STREAM_FPS
        ),
    )


    print(
        f"[CAM-001] Source FPS: "
        f"{source_fps:.1f}"
    )

    print(
        f"[CAM-001] Processing every "
        f"{process_every_n_frames} frame(s)"
    )

    print(
        f"[CAM-001] Target stream FPS: "
        f"{TARGET_STREAM_FPS}"
    )

    print(
        f"[CAM-001] Video: "
        f"{VIDEO_PATH}"
    )


    frame_number = 0

    target_frame_duration = (
        1.0
        / TARGET_STREAM_FPS
    )


    while True:

        loop_start = time.perf_counter()

        success, frame = cap.read()


        # -------------------------------------------------
        # LOOP VIDEO
        # -------------------------------------------------

        if not success:

            cap.set(
                cv2.CAP_PROP_POS_FRAMES,
                0,
            )

            frame_number = 0

            continue


        frame_number += 1


        # -------------------------------------------------
        # SKIP SOURCE FRAMES
        # -------------------------------------------------

        if (
            frame_number
            % process_every_n_frames
            != 0
        ):
            continue


        # -------------------------------------------------
        # RESIZE
        # -------------------------------------------------

        frame = resize_frame(
            frame
        )


        # -------------------------------------------------
        # YOLO DETECTION + TRACKING
        # -------------------------------------------------

        results = model.track(
            source=frame,
            persist=True,
            conf=CONFIDENCE,
            classes=[
                0,
                1,
                2,
                3,
                5,
                7,
            ],
            imgsz=YOLO_IMAGE_SIZE,
            device=DEVICE,
            verbose=False,
        )


        result = results[0]


        # Use YOLO's rendered boxes
        annotated_frame = (
            result.plot()
        )


        person_count = 0

        vehicle_count = 0

        vehicle_types = []


        if result.boxes is not None:

            for box in result.boxes:

                class_id = int(
                    box.cls[0]
                )

                if class_id == 0:

                    person_count += 1


                elif (
                    class_id
                    in VEHICLE_CLASSES
                ):

                    vehicle_count += 1

                    name = (
                        CLASS_NAMES.get(
                            class_id,
                            "Vehicle",
                        )
                    )

                    if (
                        name
                        not in vehicle_types
                    ):

                        vehicle_types.append(
                            name
                        )


        vehicle_text = (
            ", ".join(
                vehicle_types
            )
            if vehicle_types
            else "None"
        )


        # -------------------------------------------------
        # STATUS PANEL
        # -------------------------------------------------

        overlay = (
            annotated_frame.copy()
        )


        cv2.rectangle(
            overlay,
            (10, 10),
            (355, 150),
            (0, 0, 0),
            -1,
        )


        cv2.addWeighted(
            overlay,
            0.70,
            annotated_frame,
            0.30,
            0,
            annotated_frame,
        )


        cv2.putText(
            annotated_frame,
            "CAM-001 | BASEMENT ENTRY",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 0),
            2,
        )


        cv2.putText(
            annotated_frame,
            "AI PROCESSING: ACTIVE",
            (20, 62),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (0, 255, 255),
            2,
        )


        cv2.putText(
            annotated_frame,
            f"Persons: {person_count}",
            (20, 88),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (255, 255, 255),
            1,
        )


        cv2.putText(
            annotated_frame,
            f"Vehicles: {vehicle_count}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (255, 255, 255),
            1,
        )


        cv2.putText(
            annotated_frame,
            f"Type: {vehicle_text}",
            (20, 132),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (255, 255, 255),
            1,
        )


        # -------------------------------------------------
        # JPEG
        # -------------------------------------------------

        ok, buffer = cv2.imencode(
            ".jpg",
            annotated_frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                JPEG_QUALITY,
            ],
        )


        if not ok:
            continue


        # -------------------------------------------------
        # FPS PACING
        # -------------------------------------------------

        elapsed = (
            time.perf_counter()
            - loop_start
        )

        remaining = (
            target_frame_duration
            - elapsed
        )

        if remaining > 0:

            time.sleep(
                remaining
            )


        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )


    cap.release()