from __future__ import annotations

import base64
import io
import json
import os
import shutil
import socket
import struct
import subprocess
import time
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Chrome discovery
# ---------------------------------------------------------------------------

_CHROME_POSIX = [
    "google-chrome",
    "google-chrome-stable",
    "chromium-browser",
    "chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

_CHROME_WIN = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Chromium\Application\chrome.exe",
]

_REGISTRY_KEYS = [
    (r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe", ""),
    (r"SOFTWARE\Google\Chrome\BLBeacon", "path"),
]


def _find_chrome_windows() -> str | None:
    try:
        import winreg
        for key_path, value_name in _REGISTRY_KEYS:
            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(hive, key_path) as key:
                        val, _ = winreg.QueryValueEx(key, value_name)
                        p = Path(val)
                        if p.is_file():
                            return str(p)
                except OSError:
                    continue
    except ImportError:
        pass
    for candidate in _CHROME_WIN:
        if Path(candidate).is_file():
            return candidate
    return None


def _find_chrome() -> str:
    # Windows registry / known paths
    found = _find_chrome_windows()
    if found:
        return found
    # PATH lookup (works on Linux/macOS too)
    for name in _CHROME_POSIX:
        p = Path(name)
        if p.is_file():
            return str(p)
        hit = shutil.which(name)
        if hit:
            return hit
    raise RuntimeError("Chrome/Chromium not found. Install it or add it to PATH.")


# ---------------------------------------------------------------------------
# Minimal WebSocket client (stdlib only, RFC 6455)
# ---------------------------------------------------------------------------

def _ws_connect(host: str, port: int, path: str) -> socket.socket:
    sock = socket.create_connection((host, port), timeout=30)
    key = base64.b64encode(os.urandom(16)).decode()
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"\r\n"
    )
    sock.sendall(request.encode())
    response = b""
    while b"\r\n\r\n" not in response:
        response += sock.recv(4096)
    if b"101" not in response:
        raise RuntimeError(f"WebSocket upgrade failed: {response[:200]}")
    return sock


def _recv_exactly(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(min(65536, n - len(buf)))
        if not chunk:
            raise RuntimeError("WebSocket connection closed unexpectedly")
        buf += chunk
    return buf


def _ws_recv(sock: socket.socket) -> str:
    """Receive one complete (possibly fragmented) WebSocket message."""
    full_payload = b""
    while True:
        header = _recv_exactly(sock, 2)
        fin = (header[0] & 0x80) != 0
        opcode = header[0] & 0x0F
        masked = (header[1] & 0x80) != 0
        length = header[1] & 0x7F
        if length == 126:
            length = struct.unpack("!H", _recv_exactly(sock, 2))[0]
        elif length == 127:
            length = struct.unpack("!Q", _recv_exactly(sock, 8))[0]
        mask_key = _recv_exactly(sock, 4) if masked else b""
        payload = _recv_exactly(sock, length)
        if masked:
            payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        if opcode == 8:
            raise RuntimeError("WebSocket closed by server")
        if opcode != 0:  # not a continuation frame
            full_payload = payload
        else:
            full_payload += payload
        if fin:
            break
    return full_payload.decode("utf-8")


def _ws_send(sock: socket.socket, message: str) -> None:
    data = message.encode("utf-8")
    mask = os.urandom(4)
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    length = len(data)
    if length <= 125:
        header = struct.pack("BB", 0x81, 0x80 | length) + mask
    elif length <= 65535:
        header = struct.pack("!BBH", 0x81, 0x80 | 126, length) + mask
    else:
        header = struct.pack("!BBQ", 0x81, 0x80 | 127, length) + mask
    sock.sendall(header + masked)


def _cdp_call(sock: socket.socket, cmd_id: list[int], method: str, params: dict | None = None) -> dict:
    """Send one CDP command and return its result, discarding unrelated events."""
    cmd_id[0] += 1
    _ws_send(sock, json.dumps({"id": cmd_id[0], "method": method, "params": params or {}}))
    while True:
        msg = json.loads(_ws_recv(sock))
        if msg.get("id") == cmd_id[0]:
            return msg.get("result", {})


# ---------------------------------------------------------------------------
# JS payloads (identical to the selenium version)
# ---------------------------------------------------------------------------

_ANIMATION_JS = """
const svg = document.querySelector("svg");
if (svg) {
    try {
        svg.pauseAnimations();
        let maxDur = 0;
        document.querySelectorAll("animate, animateTransform, animateMotion")
        .forEach(el => {
            const dur = el.getAttribute("dur");
            if (!dur) return;
            let seconds = 0;
            if (dur.endsWith("ms")) seconds = parseFloat(dur) / 1000;
            else if (dur.endsWith("s")) seconds = parseFloat(dur);
            if (seconds > maxDur) maxDur = seconds;
        });
        svg.setCurrentTime(maxDur > 0 ? maxDur + 0.1 : 9999);
    } catch(e) {}
    document.querySelectorAll("*").forEach(el => {
        const style = window.getComputedStyle(el);
        if (style.animationDuration !== "0s") {
            el.style.animationPlayState = "paused";
            el.style.animationDelay = "0s";
            el.style.animationDuration = "0s";
        }
        if (style.transitionDuration !== "0s") {
            el.style.transition = "none";
        }
    });
}
"""

_METRICS_JS = """
(function() {
    const svg = document.querySelector("svg");
    const rect = svg.getBoundingClientRect();
    return JSON.stringify({
        x: rect.x, y: rect.y,
        width: rect.width, height: rect.height,
        dpr: window.devicePixelRatio
    });
})()
"""

_READY_JS = "document.readyState"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def svg_to_png(source: Path | str, out: Path, scale: int = 1) -> None:
    """Convert an SVG *source* (local file path or HTTP/S URL) to a PNG at *out*.

    Uses a headless Chrome subprocess driven via its DevTools Protocol over a
    minimal stdlib WebSocket client.  No third-party packages required beyond
    Pillow (already a project dependency).
    """
    from PIL import Image

    out.parent.mkdir(parents=True, exist_ok=True)
    url = source.as_uri() if isinstance(source, Path) else source
    chrome = _find_chrome()

    # Find a free port
    with socket.socket() as _s:
        _s.bind(("127.0.0.1", 0))
        port = _s.getsockname()[1]

    proc = subprocess.Popen(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-sandbox",
            "--allow-file-access-from-files",
            f"--force-device-scale-factor={scale}",
            "--window-size=1920,1080",
            f"--remote-debugging-port={port}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        # Wait for Chrome's DevTools HTTP endpoint
        ws_path: str | None = None
        for _ in range(40):
            time.sleep(0.25)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                    targets = json.loads(resp.read())
                for t in targets:
                    if t.get("type") == "page":
                        ws_path = t["webSocketDebuggerUrl"].split(f":{port}", 1)[1]
                        break
                if ws_path:
                    break
            except Exception:
                continue

        if not ws_path:
            raise RuntimeError("Chrome DevTools did not start in time")

        sock = _ws_connect("127.0.0.1", port, ws_path)
        cmd_id: list[int] = [0]

        try:
            # Enable Page events and navigate
            _cdp_call(sock, cmd_id, "Page.enable")
            _cdp_call(sock, cmd_id, "Page.navigate", {"url": url})

            # Wait for document.readyState == "complete"
            for _ in range(50):
                time.sleep(0.2)
                result = _cdp_call(sock, cmd_id, "Runtime.evaluate", {
                    "expression": _READY_JS,
                    "returnByValue": True,
                })
                if result.get("result", {}).get("value") == "complete":
                    break

            # Force animations to their final frame (same JS as selenium version)
            _cdp_call(sock, cmd_id, "Runtime.evaluate", {"expression": _ANIMATION_JS})
            time.sleep(0.1)

            # Get SVG bounding box
            metrics_result = _cdp_call(sock, cmd_id, "Runtime.evaluate", {
                "expression": _METRICS_JS,
                "returnByValue": True,
            })
            metrics = json.loads(metrics_result["result"]["value"])

            # Capture screenshot clipped to SVG bounds (CSS pixels)
            screenshot = _cdp_call(sock, cmd_id, "Page.captureScreenshot", {
                "format": "png",
                "clip": {
                    "x": metrics["x"],
                    "y": metrics["y"],
                    "width": metrics["width"],
                    "height": metrics["height"],
                    "scale": 1,
                },
            })
        finally:
            sock.close()

        img = Image.open(io.BytesIO(base64.b64decode(screenshot["data"])))
        exact_w = int(metrics["width"]) * scale
        exact_h = int(metrics["height"]) * scale
        if img.size != (exact_w, exact_h):
            img = img.resize((exact_w, exact_h), Image.Resampling.LANCZOS)
        img = img.crop((4, 4, img.width - 4, img.height - 4))
        img.save(str(out), format="PNG")

    finally:
        proc.terminate()
