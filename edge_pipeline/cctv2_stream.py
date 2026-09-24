from pathlib import Path
import time

import cv2
import numpy as np
from ultralytics import YOLO


# =========================================================
# PROJECT / VIDEO
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

VIDEO_PATH = (
    PROJECT_ROOT
    / "demo_videos"
    / "cctv2_lobby.mp4"
)

MODEL_PATH = "yolov8n.pt"


# =========================================================
# MODEL
# =========================================================

model = YOLO(MODEL_PATH)

# CPU intentionally used for stability.
DEVICE = "cpu"

print(f"[CAM-002] YOLO device: {DEVICE}")


# =========================================================
# PERFORMANCE SETTINGS
# =========================================================

TARGET_WIDTH = 960

TARGET_STREAM_FPS = 8

YOLO_IMAGE_SIZE = 256

JPEG_QUALITY = 55

CONFIDENCE = 0.35


# =========================================================
# HUMAN ANALYTICS SETTINGS
# =========================================================

# DEMO VALUE.
# Production value should normally be much higher.
LOITERING_THRESHOLD = 2.0

# Demo crowd threshold
CROWD_THRESHOLD = 3

# Movement displacement thresholds
STANDING_THRESHOLD = 6

RUNNING_THRESHOLD = 28

# Keep track alive during brief detection loss
TRACK_TTL_SECONDS = 2.0


# =========================================================
# ALERT SETTINGS
# =========================================================

ALERT_COOLDOWNS = {
    "zone_entry": 5,
    "rapid_movement": 5,
    "crowd": 10,
    "restricted_zone_entry": 10,
    "loitering": 10,
}

DEFAULT_ALERT_COOLDOWN = 5


# =========================================================
# STATE
# =========================================================

track_history = {}

track_enter_time = {}

track_last_seen = {}

loitering_alerted = set()

restricted_alerted = set()

zone_entry_alerted = set()

latest_alerts = []

last_alert_time = {}


# =========================================================
# ROI
# =========================================================

ROI_NORMALIZED = [
    (0.08, 0.26),
    (0.92, 0.26),
    (0.96, 0.95),
    (0.04, 0.95),
]


RESTRICTED_NORMALIZED = [
    (0.72, 0.28),
    (0.96, 0.28),
    (0.96, 0.90),
    (0.72, 0.90),
]


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


def normalized_polygon(
    points,
    width,
    height,
):

    return np.array(
        [
            [
                int(x * width),
                int(y * height),
            ]
            for x, y in points
        ],
        dtype=np.int32,
    )


def inside_polygon(
    point,
    polygon,
):

    return (
        cv2.pointPolygonTest(
            polygon,
            point,
            False,
        )
        >= 0
    )


# =========================================================
# ALERTS
# =========================================================

def add_alert(
    event_type,
    message,
    severity="medium",
    track_id=None,
    cooldown=True,
):

    now = time.time()


    alert_key = (
        event_type,
        (
            track_id
            if track_id is not None
            else "global"
        ),
    )


    if cooldown:

        cooldown_seconds = (
            ALERT_COOLDOWNS.get(
                event_type,
                DEFAULT_ALERT_COOLDOWN,
            )
        )


        previous_time = (
            last_alert_time.get(
                alert_key,
                0,
            )
        )


        if (
            now - previous_time
            < cooldown_seconds
        ):
            return False


    last_alert_time[
        alert_key
    ] = now


    alert = {
        "camera_id": "CAM-002",

        "event_type": event_type,

        "severity": severity,

        "message": message,

        "track_id": track_id,

        "timestamp": now,
    }


    latest_alerts.insert(
        0,
        alert,
    )


    # Max 50 alerts
    del latest_alerts[50:]


    print(
        f"[CAM-002 ALERT] "
        f"{event_type}: "
        f"{message}"
    )


    return True


# =========================================================
# BEHAVIOUR
# =========================================================

def calculate_behaviour(
    track_id,
    center,
):

    history = (
        track_history.setdefault(
            track_id,
            [],
        )
    )


    history.append(
        center
    )


    if len(history) > 8:

        history.pop(0)


    if len(history) < 2:

        return "UNKNOWN"


    old_x, old_y = (
        history[0]
    )

    new_x, new_y = (
        history[-1]
    )


    displacement = (
        (
            new_x - old_x
        ) ** 2
        +
        (
            new_y - old_y
        ) ** 2
    ) ** 0.5


    if (
        displacement
        < STANDING_THRESHOLD
    ):

        return "STANDING"


    if (
        displacement
        > RUNNING_THRESHOLD
    ):

        return "RUNNING"


    return "WALKING"


# =========================================================
# CCTV STREAM
# =========================================================

def generate_cctv2_frames():

    cap = cv2.VideoCapture(
        str(VIDEO_PATH)
    )


    if not cap.isOpened():

        raise RuntimeError(
            f"Unable to open CCTV 2 video: "
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


    target_frame_duration = (
        1.0
        / TARGET_STREAM_FPS
    )


    print(
        f"[CAM-002] Source FPS: "
        f"{source_fps:.1f}"
    )

    print(
        f"[CAM-002] Processing every "
        f"{process_every_n_frames} frame(s)"
    )

    print(
        f"[CAM-002] Target stream FPS: "
        f"{TARGET_STREAM_FPS}"
    )

    print(
        f"[CAM-002] Video: "
        f"{VIDEO_PATH}"
    )


    frame_number = 0


    while True:

        loop_start = (
            time.perf_counter()
        )


        success, frame = (
            cap.read()
        )


        # =================================================
        # LOOP VIDEO
        # =================================================

        if not success:

            cap.set(
                cv2.CAP_PROP_POS_FRAMES,
                0,
            )


            frame_number = 0


            track_history.clear()

            track_enter_time.clear()

            track_last_seen.clear()

            loitering_alerted.clear()

            restricted_alerted.clear()

            zone_entry_alerted.clear()


            continue


        frame_number += 1


        # =================================================
        # FRAME SKIPPING
        # =================================================

        if (
            frame_number
            % process_every_n_frames
            != 0
        ):

            continue


        # =================================================
        # RESIZE
        # =================================================

        frame = resize_frame(
            frame
        )


        height, width = (
            frame.shape[:2]
        )


        # =================================================
        # ROI
        # =================================================

        roi = (
            normalized_polygon(
                ROI_NORMALIZED,
                width,
                height,
            )
        )


        restricted_roi = (
            normalized_polygon(
                RESTRICTED_NORMALIZED,
                width,
                height,
            )
        )


        # =================================================
        # YOLO PERSON TRACKING
        # =================================================

        results = model.track(
            source=frame,

            persist=True,

            conf=CONFIDENCE,

            classes=[0],

            imgsz=YOLO_IMAGE_SIZE,

            device=DEVICE,

            verbose=False,
        )


        result = results[0]


        persons_inside_roi = 0


        behaviour_counts = {
            "STANDING": 0,
            "WALKING": 0,
            "RUNNING": 0,
            "UNKNOWN": 0,
        }


        current_track_ids = set()


        # =================================================
        # PERSONS
        # =================================================

        if (
            result.boxes is not None
            and
            result.boxes.id is not None
        ):

            for box in result.boxes:


                track_id = int(
                    box.id[0].item()
                )


                current_track_ids.add(
                    track_id
                )


                track_last_seen[
                    track_id
                ] = time.time()


                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0].tolist(),
                )


                confidence = float(
                    box.conf[0]
                )


                center_x = int(
                    (
                        x1 + x2
                    ) / 2
                )


                center_y = y2


                center = (
                    center_x,
                    center_y,
                )


                # =========================================
                # BEHAVIOUR
                # =========================================

                behaviour = (
                    calculate_behaviour(
                        track_id,
                        center,
                    )
                )


                if (
                    behaviour
                    in behaviour_counts
                ):

                    behaviour_counts[
                        behaviour
                    ] += 1


                # =========================================
                # MONITORED ROI
                # =========================================

                is_inside = (
                    inside_polygon(
                        center,
                        roi,
                    )
                )


                dwell_time = 0.0


                if is_inside:

                    persons_inside_roi += 1


                    # -------------------------------------
                    # ZONE ENTRY
                    # -------------------------------------

                    if (
                        track_id
                        not in zone_entry_alerted
                    ):

                        created = (
                            add_alert(
                                event_type="zone_entry",

                                severity="low",

                                track_id=track_id,

                                message=(
                                    f"Person #{track_id} "
                                    f"entered monitored "
                                    f"lobby zone"
                                ),
                            )
                        )


                        if created:

                            zone_entry_alerted.add(
                                track_id
                            )


                    # -------------------------------------
                    # DWELL TIMER
                    # -------------------------------------

                    if (
                        track_id
                        not in track_enter_time
                    ):

                        track_enter_time[
                            track_id
                        ] = time.time()


                    dwell_time = (
                        time.time()
                        -
                        track_enter_time[
                            track_id
                        ]
                    )


                    # -------------------------------------
                    # LOITERING
                    # -------------------------------------

                    if (
                        dwell_time
                        >= LOITERING_THRESHOLD
                        and
                        track_id
                        not in loitering_alerted
                    ):

                        created = (
                            add_alert(
                                event_type="loitering",

                                severity="medium",

                                track_id=track_id,

                                message=(
                                    f"Person #{track_id} "
                                    f"loitering for "
                                    f"{dwell_time:.1f}s"
                                ),
                            )
                        )


                        if created:

                            loitering_alerted.add(
                                track_id
                            )


                else:

                    track_enter_time.pop(
                        track_id,
                        None,
                    )


                    loitering_alerted.discard(
                        track_id
                    )


                    zone_entry_alerted.discard(
                        track_id
                    )


                # =========================================
                # RESTRICTED ZONE
                # =========================================

                in_restricted = (
                    inside_polygon(
                        center,
                        restricted_roi,
                    )
                )


                if (
                    in_restricted
                    and
                    track_id
                    not in restricted_alerted
                ):

                    created = (
                        add_alert(
                            event_type=
                            "restricted_zone_entry",

                            severity=
                            "high",

                            track_id=
                            track_id,

                            message=(
                                f"Person #{track_id} "
                                f"entered restricted "
                                f"zone"
                            ),
                        )
                    )


                    if created:

                        restricted_alerted.add(
                            track_id
                        )


                if not in_restricted:

                    restricted_alerted.discard(
                        track_id
                    )


                # =========================================
                # RAPID MOVEMENT
                # =========================================

                if (
                    behaviour
                    == "RUNNING"
                ):

                    add_alert(
                        event_type=
                        "rapid_movement",

                        severity=
                        "medium",

                        track_id=
                        track_id,

                        message=(
                            f"Rapid movement "
                            f"detected for "
                            f"person #{track_id}"
                        ),
                    )


                # =========================================
                # BOX COLOR
                # =========================================

                if behaviour == "RUNNING":

                    box_color = (
                        0,
                        0,
                        255,
                    )


                elif behaviour == "STANDING":

                    box_color = (
                        0,
                        255,
                        255,
                    )


                elif behaviour == "UNKNOWN":

                    box_color = (
                        200,
                        200,
                        200,
                    )


                else:

                    box_color = (
                        0,
                        255,
                        0,
                    )


                # =========================================
                # DRAW BOX
                # =========================================

                cv2.rectangle(
                    frame,

                    (
                        x1,
                        y1,
                    ),

                    (
                        x2,
                        y2,
                    ),

                    box_color,

                    2,
                )


                label = (
                    f"ID {track_id}"
                    f" | "
                    f"{behaviour}"
                    f" | "
                    f"{confidence:.2f}"
                )


                cv2.putText(
                    frame,

                    label,

                    (
                        x1,
                        max(
                            y1 - 8,
                            20,
                        ),
                    ),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.46,

                    box_color,

                    1,
                )


                if is_inside:

                    cv2.putText(
                        frame,

                        (
                            f"Dwell "
                            f"{dwell_time:.1f}s"
                        ),

                        (
                            x1,
                            min(
                                y2 + 18,
                                height - 10,
                            ),
                        ),

                        cv2.FONT_HERSHEY_SIMPLEX,

                        0.40,

                        (
                            255,
                            255,
                            255,
                        ),

                        1,
                    )


        # =================================================
        # CROWD
        # =================================================

        if (
            persons_inside_roi
            >= CROWD_THRESHOLD
        ):

            add_alert(
                event_type="crowd",

                severity="high",

                message=(
                    f"Crowd threshold reached: "
                    f"{persons_inside_roi} persons"
                ),
            )


        # =================================================
        # TRACK EXPIRY
        # =================================================

        now = time.time()


        expired_tracks = [
            track_id
            for (
                track_id,
                last_seen,
            )
            in track_last_seen.items()
            if (
                now - last_seen
                >
                TRACK_TTL_SECONDS
            )
        ]


        for track_id in expired_tracks:

            track_history.pop(
                track_id,
                None,
            )

            track_enter_time.pop(
                track_id,
                None,
            )

            track_last_seen.pop(
                track_id,
                None,
            )

            loitering_alerted.discard(
                track_id
            )

            restricted_alerted.discard(
                track_id
            )

            zone_entry_alerted.discard(
                track_id
            )


        # =================================================
        # DRAW ROI
        # =================================================

        cv2.polylines(
            frame,

            [roi],

            True,

            (
                0,
                255,
                255,
            ),

            2,
        )


        cv2.putText(
            frame,

            "MONITORED ZONE",

            (
                int(
                    roi[0][0]
                ),

                max(
                    int(
                        roi[0][1]
                    ) - 8,
                    20,
                ),
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.45,

            (
                0,
                255,
                255,
            ),

            1,
        )


        # =================================================
        # DRAW RESTRICTED ZONE
        # =================================================

        cv2.polylines(
            frame,

            [restricted_roi],

            True,

            (
                0,
                0,
                255,
            ),

            2,
        )


        cv2.putText(
            frame,

            "RESTRICTED ZONE",

            (
                int(
                    restricted_roi[
                        0
                    ][0]
                ),

                max(
                    int(
                        restricted_roi[
                            0
                        ][1]
                    ) - 8,
                    20,
                ),
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.45,

            (
                0,
                0,
                255,
            ),

            1,
        )


        # =================================================
        # STATUS PANEL
        # =================================================

        overlay = frame.copy()


        cv2.rectangle(
            overlay,

            (10, 10),

            (335, 170),

            (
                0,
                0,
                0,
            ),

            -1,
        )


        cv2.addWeighted(
            overlay,

            0.72,

            frame,

            0.28,

            0,

            frame,
        )


        status_lines = [
            "CAM-002 | UNIVERSITY LOBBY",

            "AI HUMAN ANALYTICS: ACTIVE",

            (
                f"ROI Persons: "
                f"{persons_inside_roi}"
            ),

            (
                f"Standing: "
                f"{behaviour_counts['STANDING']}"
            ),

            (
                f"Walking: "
                f"{behaviour_counts['WALKING']}"
            ),

            (
                f"Running: "
                f"{behaviour_counts['RUNNING']}"
            ),
        ]


        y = 30


        for index, text in enumerate(
            status_lines
        ):

            if index == 0:

                color = (
                    0,
                    255,
                    0,
                )


            elif index == 1:

                color = (
                    0,
                    255,
                    255,
                )


            else:

                color = (
                    255,
                    255,
                    255,
                )


            cv2.putText(
                frame,

                text,

                (
                    20,
                    y,
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.46,

                color,

                (
                    2
                    if index < 2
                    else 1
                ),
            )


            y += 24


        # =================================================
        # ALERT BANNER
        # =================================================

        if latest_alerts:

            newest_alert = (
                latest_alerts[0]
            )


            alert_age = (
                time.time()
                -
                newest_alert[
                    "timestamp"
                ]
            )


            if alert_age <= 4:

                severity = (
                    newest_alert.get(
                        "severity",
                        "medium",
                    )
                )


                if severity == "high":

                    alert_color = (
                        0,
                        0,
                        255,
                    )

                elif severity == "medium":

                    alert_color = (
                        0,
                        165,
                        255,
                    )

                else:

                    alert_color = (
                        0,
                        255,
                        255,
                    )


                cv2.rectangle(
                    frame,

                    (
                        10,
                        height - 45,
                    ),

                    (
                        min(
                            width - 10,
                            850,
                        ),

                        height - 10,
                    ),

                    (
                        0,
                        0,
                        0,
                    ),

                    -1,
                )


                alert_text = (
                    f"ALERT | "
                    f"{newest_alert['event_type']} "
                    f"| "
                    f"{newest_alert['message']}"
                )


                cv2.putText(
                    frame,

                    alert_text[:105],

                    (
                        20,
                        height - 22,
                    ),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.45,

                    alert_color,

                    1,
                )


        # =================================================
        # JPEG
        # =================================================

        ok, buffer = cv2.imencode(
            ".jpg",

            frame,

            [
                cv2.IMWRITE_JPEG_QUALITY,
                JPEG_QUALITY,
            ],
        )


        if not ok:
            continue


        # =================================================
        # FPS LIMIT
        # =================================================

        elapsed = (
            time.perf_counter()
            -
            loop_start
        )


        remaining = (
            target_frame_duration
            -
            elapsed
        )


        if remaining > 0:

            time.sleep(
                remaining
            )


        # =================================================
        # STREAM
        # =================================================

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )


    cap.release()


# =========================================================
# ALERT API
# =========================================================

def get_cctv2_alerts():

    return latest_alerts