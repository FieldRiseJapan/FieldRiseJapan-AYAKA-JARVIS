import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ayaka.ui.blink_assets import BlinkAssetLoader


class BlinkAssetLoaderTests(unittest.TestCase):
    def test_missing_required_assets_returns_safe_unavailable_result(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            official = root / "official.png"
            Image.new("RGB", (8, 8), "black").save(official)

            result = BlinkAssetLoader(official).load()

        self.assertFalse(result.available)
        self.assertIn("missing", result.reason)
        self.assertIsNone(result.half)
        self.assertIsNone(result.closed)

    def test_required_assets_must_have_alpha_and_native_dimensions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            official = root / "official.png"
            Image.new("RGB", (8, 8), "black").save(official)
            eyes_dir = root / "animation" / "eyes"
            eyes_dir.mkdir(parents=True)
            Image.new("RGB", (8, 8), "white").save(eyes_dir / "eyes_half.png")
            Image.new("RGBA", (7, 8), (255, 255, 255, 255)).save(eyes_dir / "eyes_closed.png")

            result = BlinkAssetLoader(official).load()

        self.assertFalse(result.available)
        self.assertIn("alpha", result.reason)

    def test_valid_assets_are_loaded_once_and_preserve_transparency(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            official = root / "official.png"
            Image.new("RGB", (8, 8), "black").save(official)
            eyes_dir = root / "animation" / "eyes"
            eyes_dir.mkdir(parents=True)
            for name in ("eyes_half.png", "eyes_closed.png"):
                image = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
                image.putpixel((3, 3), (255, 255, 255, 255))
                image.save(eyes_dir / name)

            loader = BlinkAssetLoader(official)
            first = loader.load()
            second = loader.load()

        self.assertTrue(first.available)
        self.assertIs(first, second)
        self.assertEqual(first.half.mode, "RGBA")
        self.assertEqual(first.closed.mode, "RGBA")
        self.assertEqual(first.half.getpixel((0, 0))[3], 0)


if __name__ == "__main__":
    unittest.main()


class BlinkOverlayProviderTests(unittest.TestCase):
    def test_open_uses_unchanged_base_and_closed_composites_overlay(self):
        from ayaka.ui.left_display import BlinkOverlayAnimationProvider
        from ayaka.ui.animation import AnimationFrame, BlinkPhase
        from ayaka.ui.state import JarvisState

        class FakeLabel:
            def __init__(self):
                self.images = []
                self.placements = []

            def configure(self, **kwargs):
                self.images.append(kwargs["image"])

            def place_configure(self, **kwargs):
                self.placements.append(kwargs)

        base = Image.new("RGB", (2, 2), "black")
        half = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
        closed = Image.new("RGBA", (2, 2), (255, 0, 0, 255))
        label = FakeLabel()
        provider = BlinkOverlayAnimationProvider(label, base, half, closed, photo_factory=lambda image: image)

        provider.apply(AnimationFrame(JarvisState.LISTENING, blink_phase=BlinkPhase.OPEN, vertical_offset_px=1))
        provider.apply(AnimationFrame(JarvisState.LISTENING, blink_phase=BlinkPhase.CLOSED, vertical_offset_px=2))
        provider.reset()

        self.assertEqual(label.images[0].getpixel((0, 0)), (0, 0, 0))
        self.assertEqual(label.images[1].getpixel((0, 0)), (255, 0, 0))
        self.assertEqual(label.placements, [{"y": 1}, {"y": 2}, {"y": 0}])


if __name__ == "__main__":
    unittest.main()
