"""The v2 candidate is opt-in and never replaces the production artwork."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops

from ayaka.ui.animation import AnimationFrame, BlinkPhase, MouthShape
from ayaka.ui.blink_assets import BlinkAssetLoader
from ayaka.ui.left_display import (AYAKA_OFFICIAL_ASSET, BlinkOverlayAnimationProvider,
                                   resolve_ayaka_asset)
from ayaka.ui.mouth_assets import MouthAssetLoader
from ayaka.ui.state import JarvisState


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "assets/characters/ayaka/v2_candidate/ayaka_left_official_v2_candidate.png"
OLD_SHA = "cacd63c36d37fb1f6a0c7dce3ab3ef7f6ec14601eec36d9f2b609681547eb030"
NEW_SHA = "24731326b75e87a646ade769f792001b68858cd4e30d8e293add63e5afb2b17a"


class V2CandidateTests(unittest.TestCase):
    def test_candidate_is_separate_and_both_base_hashes_are_fixed(self):
        self.assertEqual(AYAKA_OFFICIAL_ASSET, Path("assets/characters/ayaka/ayaka_left_official.png"))
        self.assertEqual(hashlib.sha256(resolve_ayaka_asset().read_bytes()).hexdigest(), OLD_SHA)
        self.assertEqual(hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(), NEW_SHA)
        with Image.open(CANDIDATE) as image:
            self.assertEqual((image.size, image.mode), ((1672, 941), "RGBA"))

    def test_v2_overlays_load_and_affect_only_eyes_or_mouth(self):
        blink = BlinkAssetLoader(CANDIDATE).load()
        closed_mouth, open_mouth = MouthAssetLoader(CANDIDATE).load()
        self.assertTrue(blink.available, blink.reason)
        for layer in (blink.half, blink.closed, closed_mouth, open_mouth):
            self.assertIsNotNone(layer)
            self.assertEqual((layer.size, layer.mode), ((1672, 941), "RGBA"))
            self.assertEqual(layer.getpixel((0, 0))[3], 0)
        for layer in (blink.half, blink.closed):
            self.assertEqual(layer.getchannel("A").crop((645, 335, 760, 410)).getbbox(), None)
        for layer in (closed_mouth, open_mouth):
            self.assertEqual(layer.getchannel("A").crop((585, 200, 880, 325)).getbbox(), None)

    def test_blink_and_lip_sync_composite_independently(self):
        blink = BlinkAssetLoader(CANDIDATE).load()
        closed_mouth, open_mouth = MouthAssetLoader(CANDIDATE).load()
        with Image.open(CANDIDATE) as source:
            base = source.convert("RGB")

        class Label:
            def configure(self, **kwargs): self.image = kwargs["image"]
            def place_configure(self, **kwargs): self.offset = kwargs["y"]

        label = Label()
        provider = BlinkOverlayAnimationProvider(label, base, blink.half, blink.closed,
                                                 mouth_closed=closed_mouth, mouth_open=open_mouth,
                                                 photo_factory=lambda image: image)
        images = []
        for phase in (BlinkPhase.OPEN, BlinkPhase.HALF, BlinkPhase.CLOSED, BlinkPhase.HALF, BlinkPhase.OPEN):
            provider.apply(AnimationFrame(JarvisState.LISTENING, blink_phase=phase, vertical_offset_px=1))
            images.append(label.image)
        self.assertEqual(label.offset, 1)
        self.assertIsNone(ImageChops.difference(images[0], images[-1]).getbbox())
        for image in images[1:]:
            self.assertIsNone(ImageChops.difference(images[0].crop((645, 335, 760, 410)),
                                                    image.crop((645, 335, 760, 410))).getbbox())
        provider.apply(AnimationFrame(JarvisState.SPEAKING, blink_phase=BlinkPhase.CLOSED,
                                      speaking=True, mouth_shape=MouthShape.OPEN))
        self.assertIsNotNone(ImageChops.difference(images[2].crop((645, 335, 760, 410)),
                                                    label.image.crop((645, 335, 760, 410))).getbbox())
        self.assertIsNone(ImageChops.difference(images[2].crop((585, 200, 880, 325)),
                                                label.image.crop((585, 200, 880, 325))).getbbox())
        provider.reset()
        self.assertEqual(label.offset, 0)

    def test_missing_v2_overlay_uses_existing_safe_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "v2.png"
            Image.new("RGBA", (8, 8), "black").save(base)
            self.assertFalse(BlinkAssetLoader(base).load().available)
            self.assertEqual(MouthAssetLoader(base).load(), (None, None))


if __name__ == "__main__":
    unittest.main()
