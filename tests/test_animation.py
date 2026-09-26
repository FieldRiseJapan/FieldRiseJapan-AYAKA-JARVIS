import unittest

from ayaka.config import AnimationConfig
from ayaka.ui.animation import AnimationController, BlinkPhase, MouthShape
from ayaka.ui.state import JarvisState


class AnimationControllerTests(unittest.TestCase):
    def test_time_driven_mouth_and_non_speaking_reset(self):
        controller = AnimationController(clock=lambda: 0.0, blink_interval=lambda: 4.0)
        self.assertEqual(controller.update(JarvisState.SPEAKING, now=0.0).mouth_shape, MouthShape.CLOSED)
        self.assertEqual(controller.update(JarvisState.SPEAKING, now=0.18).mouth_shape, MouthShape.OPEN)
        self.assertEqual(controller.update(JarvisState.SPEAKING, now=0.36).mouth_shape, MouthShape.CLOSED)
        for state in (JarvisState.STANDBY, JarvisState.LISTENING, JarvisState.THINKING, JarvisState.EXECUTING):
            self.assertEqual(controller.update(state, now=0.38).mouth_shape, MouthShape.CLOSED)
        self.assertEqual(controller.update(JarvisState.SPEAKING, now=0.4).mouth_shape, MouthShape.CLOSED)
        controller.reset()
        self.assertEqual(controller.update(JarvisState.SPEAKING, now=0.5).mouth_shape, MouthShape.CLOSED)

    def test_blink_phase_advances_independently_of_mouth(self):
        controller = AnimationController(clock=lambda: 0.0, blink_interval=lambda: 0.2)
        before = controller.update(JarvisState.SPEAKING, now=0.0)
        during = controller.update(JarvisState.SPEAKING, now=0.2)
        self.assertEqual((before.blink_phase, before.mouth_shape), (BlinkPhase.OPEN, MouthShape.CLOSED))
        self.assertEqual((during.blink_phase, during.mouth_shape), (BlinkPhase.HALF, MouthShape.OPEN))

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

    def test_default_micro_motion_has_six_second_period_and_one_pixel_limit(self):
        controller = AnimationController(AnimationConfig(), clock=lambda: 0.0)

        offsets = [
            controller.update(JarvisState.LISTENING, now=now).vertical_offset_px
            for now in (0.0, 1.5, 3.0, 4.5, 6.0)
        ]

        self.assertEqual(offsets, [0, 1, 0, -1, 0])
        self.assertTrue(all(abs(controller.update(JarvisState.STANDBY, now=n / 10).vertical_offset_px) <= 1 for n in range(61)))

    def test_micro_motion_continues_through_every_operational_state(self):
        controller = AnimationController(AnimationConfig(), clock=lambda: 0.0)
        states = (JarvisState.STANDBY, JarvisState.LISTENING, JarvisState.THINKING,
                  JarvisState.EXECUTING, JarvisState.SPEAKING)
        self.assertEqual([controller.update(state, now=1.5).vertical_offset_px for state in states], [1] * 5)
        self.assertEqual(controller.update(JarvisState.LISTENING, now=4.5).vertical_offset_px, -1)

    def test_micro_motion_does_not_change_blink_or_mouth_timing(self):
        moving = AnimationController(AnimationConfig(), clock=lambda: 0.0, blink_interval=lambda: 1.5)
        still = AnimationController(AnimationConfig(breathing_enabled=False), clock=lambda: 0.0, blink_interval=lambda: 1.5)
        for now in (0.0, 1.5, 1.6, 1.75, 1.9, 2.1):
            with self.subTest(now=now):
                moving_frame = moving.update(JarvisState.SPEAKING, now=now)
                still_frame = still.update(JarvisState.SPEAKING, now=now)
                self.assertEqual(moving_frame.blink_phase, still_frame.blink_phase)
                self.assertEqual(moving_frame.mouth_shape, still_frame.mouth_shape)
                self.assertEqual(still_frame.vertical_offset_px, 0)

    def test_micro_motion_reset_and_disabled_or_invalid_settings(self):
        current = [0.0]
        controller = AnimationController(AnimationConfig(), clock=lambda: current[0])
        self.assertEqual(controller.update(JarvisState.LISTENING, now=1.5).vertical_offset_px, 1)
        current[0] = 1.5
        controller.reset()
        self.assertEqual(controller.update(JarvisState.LISTENING, now=1.5).vertical_offset_px, 0)
        for config in (AnimationConfig(breathing_enabled=False),
                       AnimationConfig(breathing_amplitude_px=0),
                       AnimationConfig(breathing_period_seconds=0),
                       AnimationConfig(breathing_period_seconds=-1)):
            with self.subTest(config=config):
                self.assertEqual(AnimationController(config, clock=lambda: 0.0).update(JarvisState.SPEAKING, now=1.5).vertical_offset_px, 0)

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
