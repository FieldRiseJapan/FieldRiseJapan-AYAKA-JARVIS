import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from ayaka.ui.animation import AnimationFrame, BlinkPhase, MouthShape
from ayaka.ui.left_display import BlinkOverlayAnimationProvider, LeftDisplay
from ayaka.ui.mouth_assets import MouthAssetLoader
from ayaka.ui.state import JarvisState


class FakeLabel:
    def __init__(self, *_args, **_kwargs):
        self.image = None

    def configure(self, *, image):
        self.image = image

    def place_configure(self, **_kwargs): pass
    def place(self, **_kwargs): pass
    def lower(self, *_args): pass


class LipSyncTests(unittest.TestCase):
    def test_renderer_keeps_blink_and_mouth_independent_and_resets_closed(self):
        base = Image.new("RGB", (3, 3), "black")
        half = Image.new("RGBA", (3, 3))
        half.putpixel((0, 0), (255, 0, 0, 255))
        eyes_closed = Image.new("RGBA", (3, 3))
        eyes_closed.putpixel((0, 0), (0, 255, 0, 255))
        mouth_closed = Image.new("RGBA", (3, 3))
        mouth_closed.putpixel((1, 1), (0, 0, 255, 255))
        mouth_open = Image.new("RGBA", (3, 3))
        mouth_open.putpixel((1, 1), (255, 255, 0, 255))
        label = FakeLabel()
        provider = BlinkOverlayAnimationProvider(label, base, half, eyes_closed, mouth_closed=mouth_closed, mouth_open=mouth_open, photo_factory=lambda image: image)

        provider.apply(AnimationFrame(JarvisState.SPEAKING, blink_phase=BlinkPhase.HALF, speaking=True, mouth_shape=MouthShape.OPEN))
        self.assertEqual(label.image.getpixel((0, 0)), (255, 0, 0))
        self.assertEqual(label.image.getpixel((1, 1)), (255, 255, 0))
        provider.apply(AnimationFrame(JarvisState.SPEAKING, blink_phase=BlinkPhase.CLOSED, speaking=True, mouth_shape=MouthShape.OPEN))
        self.assertEqual(label.image.getpixel((0, 0)), (0, 255, 0))
        self.assertEqual(label.image.getpixel((1, 1)), (255, 255, 0))
        provider.apply(AnimationFrame(JarvisState.LISTENING, blink_phase=BlinkPhase.CLOSED, mouth_shape=MouthShape.OPEN))
        self.assertEqual(label.image.getpixel((1, 1)), (0, 0, 255))
        provider.reset()
        self.assertEqual(label.image.getpixel((0, 0)), (0, 0, 0))
        self.assertEqual(label.image.getpixel((1, 1)), (0, 0, 255))

    def test_missing_open_falls_back_to_closed_without_disabling_blink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            official = root / "official.png"
            Image.new("RGB", (4, 4), "black").save(official)
            eyes = root / "animation" / "eyes"
            eyes.mkdir(parents=True)
            Image.new("RGBA", (4, 4)).save(eyes / "eyes_half.png")
            Image.new("RGBA", (4, 4)).save(eyes / "eyes_closed.png")
            mouths = root / "animation" / "mouth"
            mouths.mkdir(parents=True)
            closed = Image.new("RGBA", (4, 4))
            closed.putpixel((1, 1), (0, 0, 255, 255))
            closed.save(mouths / "mouth_closed.png")
            self.assertIsNone(MouthAssetLoader(official).load()[1])
            display = LeftDisplay(None, (4, 4), asset_path=official)
            display.fallback_frame = object()

            class FakeTk:
                Label = FakeLabel

            with patch("ayaka.ui.left_display.tk", FakeTk), patch("ayaka.ui.left_display.ImageTk.PhotoImage", side_effect=lambda image: image):
                display._mount_image()
                self.assertIsInstance(display.animation_provider, BlinkOverlayAnimationProvider)
                display.animation_provider.apply(AnimationFrame(JarvisState.SPEAKING, blink_phase=BlinkPhase.HALF, speaking=True, mouth_shape=MouthShape.OPEN))
                self.assertEqual(display.image_label.image.getpixel((1, 1)), (0, 0, 255))

    def test_missing_eye_assets_still_allow_mouth_animation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            official = root / "official.png"
            Image.new("RGB", (4, 4), "black").save(official)
            mouths = root / "animation" / "mouth"
            mouths.mkdir(parents=True)
            for name, color in (("mouth_closed.png", (0, 0, 255, 255)), ("mouth_open.png", (255, 255, 0, 255))):
                overlay = Image.new("RGBA", (4, 4))
                overlay.putpixel((1, 1), color)
                overlay.save(mouths / name)
            display = LeftDisplay(None, (4, 4), asset_path=official)
            display.fallback_frame = object()

            class FakeTk:
                Label = FakeLabel

            with patch("ayaka.ui.left_display.tk", FakeTk), patch("ayaka.ui.left_display.ImageTk.PhotoImage", side_effect=lambda image: image):
                display._mount_image()
                display.animation_provider.apply(AnimationFrame(JarvisState.SPEAKING, speaking=True, mouth_shape=MouthShape.OPEN))
                self.assertEqual(display.image_label.image.getpixel((1, 1)), (255, 255, 0))

    def test_missing_closed_mouth_keeps_eye_blink_available(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            official = root / "official.png"
            Image.new("RGB", (4, 4), "black").save(official)
            eyes = root / "animation" / "eyes"
            eyes.mkdir(parents=True)
            for name in ("eyes_half.png", "eyes_closed.png"):
                layer = Image.new("RGBA", (4, 4))
                layer.putpixel((0, 0), (255, 0, 0, 255))
                layer.save(eyes / name)
            display = LeftDisplay(None, (4, 4), asset_path=official)
            display.fallback_frame = object()

            class FakeTk:
                Label = FakeLabel

            with patch("ayaka.ui.left_display.tk", FakeTk), patch("ayaka.ui.left_display.ImageTk.PhotoImage", side_effect=lambda image: image):
                display._mount_image()
                self.assertIsInstance(display.animation_provider, BlinkOverlayAnimationProvider)
                display.animation_provider.apply(AnimationFrame(JarvisState.LISTENING, blink_phase=BlinkPhase.HALF))
                self.assertEqual(display.image_label.image.getpixel((0, 0)), (255, 0, 0))


if __name__ == "__main__":
    unittest.main()
