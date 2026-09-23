import unittest

from ayaka.config import AnimationConfig
from ayaka.ui.animation import AnimationController, BlinkPhase
from ayaka.ui.state import JarvisState


class AnimationControllerTests(unittest.TestCase):
    def test_speaking_state_exposes_and_clears_clamped_audio_level(self):
        controller = AnimationController(
            AnimationConfig(),
            clock=lambda: 10.0,
            blink_interval=lambda: 4.0,
        )

        initial = controller.update(JarvisState.SPEAKING, now=10.0)
        self.assertTrue(initial.speaking)
        self.assertEqual(initial.mouth_open, 0.0)

        controller.set_speaking_level(1.5)
        active = controller.update(JarvisState.SPEAKING, now=10.1)
        self.assertEqual(active.mouth_open, 1.0)

        listening = controller.update(JarvisState.LISTENING, now=10.2)
        self.assertFalse(listening.speaking)
        self.assertEqual(listening.mouth_open, 0.0)

        speaking_again = controller.update(JarvisState.SPEAKING, now=10.3)
        self.assertEqual(speaking_again.mouth_open, 0.0)

    def test_negative_speaking_level_is_clamped_to_closed(self):
        controller = AnimationController(AnimationConfig(), clock=lambda: 0.0)
        controller.set_speaking_level(-0.5)

        frame = controller.update(JarvisState.SPEAKING, now=0.0)

        self.assertEqual(frame.mouth_open, 0.0)

    def test_breathing_is_disabled_by_default(self):
        controller = AnimationController(AnimationConfig(), clock=lambda: 0.0)

        offsets = [
            controller.update(JarvisState.LISTENING, now=now).vertical_offset_px
            for now in (0.0, 1.0, 2.0, 3.0, 4.0)
        ]

        self.assertEqual(offsets, [0, 0, 0, 0, 0])

    def test_breathing_amplitude_is_clamped_to_two_pixels(self):
        controller = AnimationController(
            AnimationConfig(
                breathing_enabled=True,
                breathing_amplitude_px=99,
                breathing_period_seconds=4.0,
            ),
            clock=lambda: 0.0,
        )

        offsets = [
            controller.update(JarvisState.LISTENING, now=now).vertical_offset_px
            for now in (0.0, 1.0, 2.0, 3.0, 4.0)
        ]

        self.assertEqual(offsets, [0, 2, 0, -2, 0])

    def test_negative_breathing_amplitude_produces_no_motion(self):
        controller = AnimationController(
            AnimationConfig(breathing_enabled=True, breathing_amplitude_px=-3),
            clock=lambda: 0.0,
        )

        self.assertEqual(
            controller.update(JarvisState.LISTENING, now=1.0).vertical_offset_px,
            0,
        )

    def test_blink_timing_progresses_through_natural_phases(self):
        controller = AnimationController(
            AnimationConfig(),
            clock=lambda: 10.0,
            blink_interval=lambda: 4.0,
        )

        observed = [
            controller.update(JarvisState.LISTENING, now=now).blink_phase
            for now in (13.99, 14.0, 14.08, 14.20, 14.28)
        ]

        self.assertEqual(
            observed,
            [
                BlinkPhase.OPEN,
                BlinkPhase.HALF,
                BlinkPhase.CLOSED,
                BlinkPhase.HALF,
                BlinkPhase.OPEN,
            ],
        )


if __name__ == "__main__":
    unittest.main()
