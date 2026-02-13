import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Tuple

import cv2
import mss
import numpy as np
import pyautogui


@dataclass
class Region:
    left: int
    top: int
    width: int
    height: int


@dataclass
class Color:
    b: int
    g: int
    r: int


@dataclass
class AgentConfig:
    tolerance: int = 30
    move_key: Tuple[str, str] = ("left", "right")
    min_move_duration: float = 0.01
    max_move_duration: float = 0.06
    loop_delay: float = 0.01
    deadzone: int = 6
    kp: float = 0.001
    adaptive_rate: float = 0.03
    kp_min: float = 0.0002
    kp_max: float = 0.003
    show_preview: bool = True


@dataclass
class Calibration:
    region: Region
    ball_color: Color
    paddle_color: Color
    config: AgentConfig


ROOT_DIR = Path(__file__).resolve().parents[1]
CALIBRATION_PATH = ROOT_DIR / "data" / "screen_agent.json"


def wait_for_enter(prompt: str) -> None:
    input(prompt)


def get_mouse_position() -> Tuple[int, int]:
    pos = pyautogui.position()
    return pos.x, pos.y


def sample_color_at_mouse(samples: int = 7, delay: float = 0.05) -> Color:
    x, y = get_mouse_position()
    colors = []
    for _ in range(samples):
        img = pyautogui.screenshot(region=(x, y, 1, 1))
        r, g, b = img.getpixel((0, 0))
        colors.append((b, g, r))
        time.sleep(delay)
    avg = np.mean(np.array(colors), axis=0)
    return Color(b=int(avg[0]), g=int(avg[1]), r=int(avg[2]))


def select_region() -> Region:
    wait_for_enter("Move mouse to TOP-LEFT of game area, then press Enter...")
    x1, y1 = get_mouse_position()
    wait_for_enter("Move mouse to BOTTOM-RIGHT of game area, then press Enter...")
    x2, y2 = get_mouse_position()

    left = min(x1, x2)
    top = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)

    if width < 10 or height < 10:
        raise ValueError("Selected region too small. Try again with a larger area.")

    return Region(left=left, top=top, width=width, height=height)


def color_mask(frame_bgr: np.ndarray, color: Color, tolerance: int) -> np.ndarray:
    lower = np.array([
        max(color.b - tolerance, 0),
        max(color.g - tolerance, 0),
        max(color.r - tolerance, 0),
    ], dtype=np.uint8)
    upper = np.array([
        min(color.b + tolerance, 255),
        min(color.g + tolerance, 255),
        min(color.r + tolerance, 255),
    ], dtype=np.uint8)
    return cv2.inRange(frame_bgr, lower, upper)


def find_centroid(mask: np.ndarray) -> Optional[Tuple[int, int]]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(contour)
    if area < 10:
        return None
    m = cv2.moments(contour)
    if m["m00"] == 0:
        return None
    cx = int(m["m10"] / m["m00"])
    cy = int(m["m01"] / m["m00"])
    return cx, cy


def press_key(key: str, duration: float) -> None:
    pyautogui.keyDown(key)
    time.sleep(duration)
    pyautogui.keyUp(key)


def calibration_to_dict(calibration: Calibration) -> dict:
    data = asdict(calibration)
    return data


def calibration_from_dict(data: dict) -> Calibration:
    region = Region(**data["region"])
    ball_color = Color(**data["ball_color"])
    paddle_color = Color(**data["paddle_color"])
    config = AgentConfig(**data["config"])
    return Calibration(region=region, ball_color=ball_color, paddle_color=paddle_color, config=config)


def load_calibration() -> Optional[Calibration]:
    if not CALIBRATION_PATH.exists():
        return None
    with CALIBRATION_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return calibration_from_dict(data)


def save_calibration(calibration: Calibration) -> None:
    CALIBRATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CALIBRATION_PATH.open("w", encoding="utf-8") as handle:
        json.dump(calibration_to_dict(calibration), handle, indent=2)


def preview_detection(sct: mss.mss, monitor: dict, calibration: Calibration) -> str:
    frame = np.array(sct.grab(monitor))
    frame_bgr = frame[:, :, :3]
    ball_mask = color_mask(frame_bgr, calibration.ball_color, calibration.config.tolerance)
    paddle_mask = color_mask(frame_bgr, calibration.paddle_color, calibration.config.tolerance)

    ball_mask = cv2.erode(ball_mask, None, iterations=1)
    ball_mask = cv2.dilate(ball_mask, None, iterations=2)
    paddle_mask = cv2.erode(paddle_mask, None, iterations=1)
    paddle_mask = cv2.dilate(paddle_mask, None, iterations=2)

    ball_center = find_centroid(ball_mask)
    paddle_center = find_centroid(paddle_mask)

    if ball_center:
        cv2.circle(frame_bgr, ball_center, 6, (0, 255, 255), -1)
    if paddle_center:
        cv2.circle(frame_bgr, paddle_center, 6, (255, 0, 255), -1)

    cv2.imshow("LittleCat Screen Agent", frame_bgr)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        return "accept"
    if key == ord("r"):
        return "redo"
    if key == ord("x"):
        return "exit"
    return "continue"


def calibrate(show_preview: bool = True) -> Calibration:
    print("Calibration mode")
    print("This will control keyboard input. Keep focus on the game window.")
    region = select_region()

    while True:
        wait_for_enter("Hover mouse on BALL and press Enter to sample color...")
        ball_color = sample_color_at_mouse()
        wait_for_enter("Hover mouse on PADDLE and press Enter to sample color...")
        paddle_color = sample_color_at_mouse()

        config = AgentConfig(show_preview=show_preview)
        calibration = Calibration(region=region, ball_color=ball_color, paddle_color=paddle_color, config=config)

        if not show_preview:
            return calibration

        print("Preview: press Q to accept, R to resample colors, X to exit.")
        with mss.mss() as sct:
            monitor = {
                "left": region.left,
                "top": region.top,
                "width": region.width,
                "height": region.height,
            }
            while True:
                result = preview_detection(sct, monitor, calibration)
                if result == "accept":
                    cv2.destroyAllWindows()
                    return calibration
                if result == "redo":
                    cv2.destroyAllWindows()
                    break
                if result == "exit":
                    cv2.destroyAllWindows()
                    raise KeyboardInterrupt


def adaptive_duration(error: int, config: AgentConfig) -> float:
    magnitude = abs(error)
    duration = magnitude * config.kp
    return max(config.min_move_duration, min(config.max_move_duration, duration))


def update_learning(config: AgentConfig, error_history: list[int]) -> None:
    if len(error_history) < 30:
        return
    avg_error = sum(error_history) / len(error_history)
    if avg_error > 40:
        config.kp = min(config.kp * (1.0 + config.adaptive_rate), config.kp_max)
    elif avg_error < 10:
        config.kp = max(config.kp * (1.0 - config.adaptive_rate), config.kp_min)


def play(calibration: Calibration) -> None:
    print("Play mode (Ctrl+C to stop). Keep focus on the game window.")
    config = calibration.config

    error_history: list[int] = []
    last_save = time.time()

    with mss.mss() as sct:
        monitor = {
            "left": calibration.region.left,
            "top": calibration.region.top,
            "width": calibration.region.width,
            "height": calibration.region.height,
        }

        while True:
            frame = np.array(sct.grab(monitor))
            frame_bgr = frame[:, :, :3]

            ball_mask = color_mask(frame_bgr, calibration.ball_color, config.tolerance)
            paddle_mask = color_mask(frame_bgr, calibration.paddle_color, config.tolerance)

            ball_mask = cv2.erode(ball_mask, None, iterations=1)
            ball_mask = cv2.dilate(ball_mask, None, iterations=2)
            paddle_mask = cv2.erode(paddle_mask, None, iterations=1)
            paddle_mask = cv2.dilate(paddle_mask, None, iterations=2)

            ball_center = find_centroid(ball_mask)
            paddle_center = find_centroid(paddle_mask)

            if config.show_preview:
                if ball_center:
                    cv2.circle(frame_bgr, ball_center, 6, (0, 255, 255), -1)
                if paddle_center:
                    cv2.circle(frame_bgr, paddle_center, 6, (255, 0, 255), -1)
                cv2.imshow("LittleCat Screen Agent", frame_bgr)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

            if ball_center and paddle_center:
                ball_x, _ = ball_center
                paddle_x, _ = paddle_center
                error = ball_x - paddle_x
                error_history.append(abs(error))
                if len(error_history) > 120:
                    error_history.pop(0)

                if error < -config.deadzone:
                    press_key(config.move_key[0], adaptive_duration(error, config))
                elif error > config.deadzone:
                    press_key(config.move_key[1], adaptive_duration(error, config))

                update_learning(config, error_history)

            if time.time() - last_save > 30:
                save_calibration(calibration)
                last_save = time.time()

            time.sleep(config.loop_delay)

    if config.show_preview:
        cv2.destroyAllWindows()
    save_calibration(calibration)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LittleCat screen agent")
    parser.add_argument("--calibrate", action="store_true", help="Calibrate game region and colors")
    parser.add_argument("--play", action="store_true", help="Play using saved calibration")
    parser.add_argument("--no-preview", action="store_true", help="Disable preview window")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    show_preview = not args.no_preview

    if args.calibrate:
        calibration = calibrate(show_preview=show_preview)
        save_calibration(calibration)
        print(f"Calibration saved to {CALIBRATION_PATH}")
        return

    calibration = load_calibration()
    if calibration is None:
        calibration = calibrate(show_preview=show_preview)
        save_calibration(calibration)
        print(f"Calibration saved to {CALIBRATION_PATH}")

    if args.play or not args.calibrate:
        calibration.config.show_preview = show_preview
        play(calibration)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
