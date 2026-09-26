"""Render opt-in v2 candidate preview without changing the production asset."""

from pathlib import Path
import argparse

from PIL import Image, ImageDraw

from ayaka.ui.blink_assets import BlinkAssetLoader
from ayaka.ui.mouth_assets import MouthAssetLoader


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "assets/characters/ayaka/v2_candidate/ayaka_left_official_v2_candidate.png"


def render(output: Path) -> None:
    blink = BlinkAssetLoader(CANDIDATE).load()
    mouth_closed, mouth_open = MouthAssetLoader(CANDIDATE).load()
    if not blink.available or mouth_closed is None or mouth_open is None:
        raise ValueError(f"v2 assets unavailable: {blink.reason}")
    with Image.open(CANDIDATE) as source:
        base = source.convert("RGBA")
    tile = (836, 471)
    margin = 24
    preview = Image.new("RGB", (tile[0] * 3, (tile[1] + margin) * 2), "#0a1020")
    for column, (label, eye) in enumerate((("OPEN", None), ("HALF", blink.half),
                                           ("CLOSED", blink.closed))):
        for row, (mouth_label, mouth) in enumerate((("MOUTH_CLOSED", mouth_closed),
                                                    ("MOUTH_OPEN", mouth_open))):
            frame = Image.alpha_composite(base, eye) if eye is not None else base.copy()
            frame = Image.alpha_composite(frame, mouth).convert("RGB")
            frame.thumbnail(tile, Image.Resampling.LANCZOS)
            x, y = column * tile[0], row * (tile[1] + margin)
            preview.paste(frame, (x, y + margin))
            ImageDraw.Draw(preview).text((x + 8, y + 5), f"{label} / {mouth_label}", fill="white")
    output.parent.mkdir(parents=True, exist_ok=True)
    preview.save(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "runtime/ayaka_v2_preview.png")
    render(parser.parse_args().output)
