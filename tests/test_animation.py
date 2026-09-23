import unittest

from ayaka.config import AnimationConfig
from ayaka.ui.animation import AnimationController, BlinkPhase, MouthShape
from ayaka.ui.state import JarvisState


class AnimationControllerTests(unittest.TestCase):
    def test_discrete_mouth_shapes_and_non_speaking_reset(self):
        controller = AnimationController(clock=lambda: 0.0, blink_interval=lambda: 4.0)
        observed = []
        for level in (0.0, 0.1, 0.4, 0.9):
            controller.set_speaking_level(level)
            observed.append(controller.update(JarvisState.SPEAKING, now=0.0).mouth_shape)
        self.assertEqual(observed, [MouthShape.CLOSED, MouthShape.SMALL, MouthShape.MEDIUM, MouthShape.OPEN])
        self.assertEqual(controller.update(JarvisState.EXECUTING, now=0.0).mouth_shape, MouthShape.CLOSED)
        controller.set_speaking_level(1.0)
        self.assertEqual(controller.update(JarvisState.SPEAKING, now=0.0).mouth_shape, MouthShape.OPEN)
        controller.reset()
        self.assertEqual(controller.update(JarvisState.SPEAKING, now=0.0).mouth_shape, MouthShape.CLOSED)

    def test_independent_flags_and_invalid_audio_close_safely(self):
        config = AnimationConfig(blink_enabled=False, lipsync_enabled=False, breathing_enabled=True)
        controller = AnimationController(config, clock=lambda: 0.0, blink_interval=lambda: 0.1)
        controller.set_speaking_level(float('nan'))
        self.assertEqual(controller.update(JarvisState.SPEAKING, now=1.0).mouth_shape, MouthShape.CLOSED)
        controller.set_speaking_level(1.0)
        frame = controller.update(JarvisState.SPEAKING, now=1.0)
        self.assertEqual(frame.blink_phase, BlinkPhase.OPEN)
        self.assertEqual(frame.mouth_shape, MouthShape.CLOSED)
        self.assertNotEqual(frame.vertical_offset_px, 0)
        disabled = AnimationController(AnimationConfig(enabled=False, breathing_enabled=True), clock=lambda: 0.0)
        self.assertEqual(disabled.update(JarvisState.SPEAKING, now=1.0).vertical_offset_px, 0)

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
