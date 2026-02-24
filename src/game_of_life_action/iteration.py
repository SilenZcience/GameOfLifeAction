from __future__ import annotations

from pathlib import Path


def iteration_image_content(r: int, g: int, b: int) -> str:
    hex_color = f"#{r:02x}{g:02x}{b:02x}"
    return f"""
<svg fill=\"none\" viewBox=\"0 0 345 20\" width=\"345px\" height=\"20px\" xmlns=\"http://www.w3.org/2000/svg\">
  <foreignObject width=\"100%\" height=\"100%\">
    <div xmlns=\"http://www.w3.org/1999/xhtml\">
      <style>
        .wrapper {{ text-align: center; width: 345px; height: 20px; }}
        h1 {{
          background: {hex_color};
          color: #fff;
          font-size: 10px;
          font-weight: 500;
          font-family: \"Josefin Sans\", sans-serif;
          background-size: 200% auto;
          background-clip: text;
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          display: inline-block;
        }}
      </style>
      <div class=\"wrapper\"><h1>Current Iteration: 0</h1></div>
    </div>
  </foreignObject>
</svg>
""".strip()


def update_iteration(image_file: Path, color: tuple[int, int, int, int], increment: bool) -> None:
    if not image_file.exists():
        image_file.write_text(iteration_image_content(*color[:3]), encoding="utf-8")
        return

    try:
        content = image_file.read_text(encoding="utf-8")
    except OSError:
        return

    start = content.find("<h1>")
    end = content.find("</h1>")
    if start == -1 or end == -1 or end <= start + 4:
        return

    header_content = content[start + 4 : end]
    current_iteration = 0
    if increment:
        suffix_digits = ""
        for char in reversed(header_content):
            if not char.isdigit():
                break
            suffix_digits += char
        if suffix_digits:
            current_iteration = int(suffix_digits[::-1]) + 1

    new_header = f"Current Iteration: {current_iteration}"
    updated = content.replace(header_content, new_header, 1)

    try:
        image_file.write_text(updated, encoding="utf-8")
    except OSError:
        return
