"""
cameras.py — 3-Camera IoT Vision System for TED Kiosk

Camera roles (configured in system_config or .env):
  CAMERA_0  = Screen capture camera — faces employee's laptop screen
  CAMERA_1  = Hardware inspection camera — points at physical device
  CAMERA_2  = Badge/employee camera — faces the employee (QR, face)

Uses OpenCV for capture + pyzbar for QR/barcode decoding.
OCR on captured frames uses pattern-matching (PaddleOCR hook ready).
"""
import cv2
import base64
import logging
import numpy as np
from datetime import datetime
from typing import Optional

logger = logging.getLogger("ted.cameras")

# Camera index mapping — override via env vars
CAMERA_SCREEN   = int(__import__('os').environ.get('TED_CAM_SCREEN', 0))
CAMERA_HARDWARE = int(__import__('os').environ.get('TED_CAM_HARDWARE', 1))
CAMERA_BADGE    = int(__import__('os').environ.get('TED_CAM_BADGE', 2))

# Resolution for capture
CAP_WIDTH  = 1280
CAP_HEIGHT = 720


def _open_camera(index: int, width: int = CAP_WIDTH, height: int = CAP_HEIGHT) -> Optional[cv2.VideoCapture]:
    """Open a camera by index. Returns None if not available."""
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW if __import__('platform').system() == 'Windows' else cv2.CAP_ANY)
    if not cap.isOpened():
        logger.warning(f"Camera {index} not available")
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
    return cap


def _frame_to_b64(frame: np.ndarray) -> str:
    """Convert OpenCV frame to base64 PNG string."""
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return base64.b64encode(buf).decode('utf-8')


def _preprocess_for_ocr(frame: np.ndarray) -> np.ndarray:
    """Enhance frame contrast for better OCR accuracy."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    # Bilateral filter to remove noise while keeping edges
    denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
    return denoised


def list_available_cameras(max_check: int = 4) -> list[dict]:
    """Detect all connected cameras and return their info."""
    available = []
    for i in range(max_check):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if __import__('platform').system() == 'Windows' else cv2.CAP_ANY)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # reduce buffer to speed up open check
        if cap.isOpened():
            ret, frame = cap.read()
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            role = "Screen Capture" if i == CAMERA_SCREEN else \
                   "Hardware Inspection" if i == CAMERA_HARDWARE else \
                   "Badge / Employee" if i == CAMERA_BADGE else "Unassigned"
            available.append({
                "index": i,
                "role": role,
                "resolution": f"{w}x{h}",
                "working": ret,
                "preview_b64": _frame_to_b64(frame) if ret else None,
            })
            cap.release()
    return available


# ── Camera 1: Screen Capture ──────────────────────────────────────────────

def capture_screen(frames: int = 3) -> dict:
    """
    Camera 1 — Capture employee's laptop screen to extract error text.
    Takes multiple frames and selects the sharpest one.
    """
    cap = _open_camera(CAMERA_SCREEN)
    if not cap:
        return {"success": False, "error": "Screen camera (Camera 0) not connected",
                "tip": "Set TED_CAM_SCREEN env var to the correct camera index"}

    best_frame = None
    best_sharpness = 0.0

    # Warm up + capture best frame
    for _ in range(5): cap.read()  # discard initial frames
    for _ in range(frames):
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            if sharpness > best_sharpness:
                best_sharpness = sharpness
                best_frame = frame.copy()

    cap.release()
    if best_frame is None:
        return {"success": False, "error": "Failed to capture frame from screen camera"}

    processed = _preprocess_for_ocr(best_frame)

    # Detect error-like regions (bright white text on blue/black background)
    hsv = cv2.cvtColor(best_frame, cv2.COLOR_BGR2HSV)
    # Blue screen detection (BSOD)
    blue_mask = cv2.inRange(hsv, np.array([100, 100, 100]), np.array([130, 255, 255]))
    blue_pixels = np.sum(blue_mask > 0)
    is_bsod = blue_pixels > (best_frame.shape[0] * best_frame.shape[1] * 0.4)

    # Error dialog detection (look for typical Windows error dialog colours)
    white_regions = cv2.inRange(cv2.cvtColor(best_frame, cv2.COLOR_BGR2GRAY),
                                np.array([200]), np.array([255]))

    return {
        "success": True,
        "camera": "Screen Capture (Camera 0)",
        "sharpness": round(best_sharpness, 1),
        "resolution": f"{best_frame.shape[1]}x{best_frame.shape[0]}",
        "bsod_detected": bool(is_bsod),
        "error_dialog_detected": int(np.sum(white_regions > 0)) > 50000,
        "timestamp": datetime.utcnow().isoformat(),
        "image_b64": _frame_to_b64(best_frame),
        "processed_b64": _frame_to_b64(cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)),
        "ocr_ready": True,
    }


# ── Camera 2: Hardware Inspection ────────────────────────────────────────

def scan_hardware_device() -> dict:
    """
    Camera 2 — Scan the physical device placed at the kiosk.
    Reads: QR code / barcode (asset tag), checks physical condition.
    """
    cap = _open_camera(CAMERA_HARDWARE)
    if not cap:
        return {"success": False, "error": "Hardware inspection camera (Camera 1) not connected",
                "tip": "Set TED_CAM_HARDWARE env var to the correct camera index"}

    # Warm up
    for _ in range(5): cap.read()

    asset_tag = None
    serial_number = None
    best_frame = None

    # Try to read QR/barcode for up to 3 seconds (30 frames)
    for _ in range(30):
        ret, frame = cap.read()
        if not ret:
            continue
        best_frame = frame.copy()

        # Barcode/QR detection
        try:
            from pyzbar.pyzbar import decode
            barcodes = decode(frame)
            for bc in barcodes:
                data = bc.data.decode('utf-8', errors='replace')
                if bc.type in ('QRCODE', 'CODE128', 'CODE39'):
                    if not asset_tag:
                        asset_tag = data
                    elif not serial_number:
                        serial_number = data
        except Exception:
            pass

        if asset_tag:
            break  # Got what we need

    cap.release()

    # Physical condition analysis on best frame
    condition = "good"
    damage_notes = []
    if best_frame is not None:
        # Simple damage heuristic: detect large dark irregular regions
        gray = cv2.cvtColor(best_frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        large_dark = [c for c in contours if cv2.contourArea(c) > 5000]
        if len(large_dark) > 5:
            condition = "possibly_damaged"
            damage_notes.append(f"Detected {len(large_dark)} irregular dark regions — may indicate physical damage")

    return {
        "success": True,
        "camera": "Hardware Inspection (Camera 1)",
        "asset_tag": asset_tag,
        "serial_number": serial_number,
        "physical_condition": condition,
        "damage_notes": damage_notes,
        "timestamp": datetime.utcnow().isoformat(),
        "image_b64": _frame_to_b64(best_frame) if best_frame is not None else None,
        "barcode_detected": bool(asset_tag),
    }


# ── Camera 3: Badge / Employee ────────────────────────────────────────────

def scan_badge() -> dict:
    """
    Camera 3 — Scan employee badge (QR code or barcode) for auto-authentication.
    Returns employee_id extracted from badge QR code.
    """
    cap = _open_camera(CAMERA_BADGE)
    if not cap:
        return {"success": False, "error": "Badge camera (Camera 2) not connected",
                "tip": "Set TED_CAM_BADGE env var to the correct camera index"}

    for _ in range(5): cap.read()  # warm up

    employee_id = None
    badge_data = None
    frame_used = None

    for _ in range(60):  # try for ~2 seconds
        ret, frame = cap.read()
        if not ret:
            continue
        frame_used = frame.copy()

        try:
            from pyzbar.pyzbar import decode
            codes = decode(frame)
            for code in codes:
                data = code.data.decode('utf-8', errors='replace').strip()
                # Badge QR format: "EMP:EMP-1029" or just "EMP-1029" or JSON
                if data.startswith("EMP:"):
                    employee_id = data[4:]
                    badge_data = data
                elif data.startswith("EMP-") or data.startswith("EMP_"):
                    employee_id = data
                    badge_data = data
                elif "employee_id" in data.lower():
                    import json as _json
                    try:
                        obj = _json.loads(data)
                        employee_id = obj.get("employee_id") or obj.get("emp_id") or obj.get("id")
                        badge_data = data
                    except Exception:
                        pass
        except Exception:
            pass

        if employee_id:
            break

    cap.release()

    return {
        "success": bool(employee_id),
        "camera": "Badge / Employee (Camera 2)",
        "employee_id": employee_id,
        "badge_raw": badge_data,
        "badge_detected": bool(employee_id),
        "timestamp": datetime.utcnow().isoformat(),
        "image_b64": _frame_to_b64(frame_used) if frame_used is not None else None,
        "message": f"Badge scanned — Employee {employee_id}" if employee_id else "No badge detected — please use manual login",
    }


def capture_all_cameras() -> dict:
    """Capture a single frame from all 3 cameras simultaneously (for status check)."""
    results = {}
    for idx, role in [(CAMERA_SCREEN, "screen"), (CAMERA_HARDWARE, "hardware"), (CAMERA_BADGE, "badge")]:
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            for _ in range(3): cap.read()
            ret, frame = cap.read()
            results[role] = {
                "connected": True, "index": idx,
                "preview_b64": _frame_to_b64(frame) if ret else None,
            }
            cap.release()
        else:
            results[role] = {"connected": False, "index": idx, "preview_b64": None}
    return results
