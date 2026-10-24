"""Regression tests for the THE ENVELOPE visual-upgrade renderer."""
import unittest

from rendering.the_envelope_visual_upgrade import (
    EPISODES,
    SCENES_PER_EPISODE,
    build_xfade_filter,
    classify_artifact,
    motion_gate,
)


class VisualUpgradeTests(unittest.TestCase):
    def test_episode_catalog_has_30_episodes_and_six_scenes_each(self):
        self.assertEqual(len(EPISODES), 30)
        self.assertTrue(all(len(ep["scenes"]) == SCENES_PER_EPISODE for ep in EPISODES))

    def test_artifact_is_not_mislabeled_as_ai_video_generation(self):
        self.assertEqual(classify_artifact(), "DETERMINISTIC_MOTION_TEXT_FALLBACK")

    def test_xfade_offsets_produce_60_seconds(self):
        offsets = [i * (60.0 / 6 + 0.8 * 5 / 6 - 0.8) for i in range(5)]
        self.assertAlmostEqual(offsets[-1] + (60.0 / 6), 60.0, places=5)
        graph = build_xfade_filter()
        self.assertIn("xfade=transition=fade:duration=0.8", graph)
        self.assertIn("offset=49.333333", graph)

    def test_motion_gate_rejects_static_frames(self):
        self.assertFalse(motion_gate([0.0, 0.0]))
        self.assertTrue(motion_gate([12.0, 18.0]))
        self.assertFalse(motion_gate([100.0, 12.0]))


if __name__ == "__main__":
    unittest.main()
