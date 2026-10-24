"""Regression tests for the THE ENVELOPE visual-upgrade renderer."""
import unittest

from rendering.the_envelope_visual_upgrade import (
    EPISODES,
    SCENES_PER_EPISODE,
    build_xfade_filter,
    build_text_overlay_filter,
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
        offsets = [i * (60.0 / 6 + 0.8 * 5 / 6 - 0.8) for i in range(1, 6)]
        self.assertAlmostEqual(offsets[-1] + (60.0 / 6 + 0.8 * 5 / 6), 60.0, places=5)
        graph = build_xfade_filter()
        self.assertIn("xfade=transition=fade:duration=0.8", graph)
        self.assertIn("offset=49.333333", graph)

    def test_text_is_not_part_of_background_crossfades(self):
        graph = build_xfade_filter()
        self.assertEqual(graph.count("xfade=transition=fade"), 5)
        self.assertNotIn("text", graph.lower())
        text_graph = build_text_overlay_filter()
        self.assertEqual(text_graph.count("overlay="), 6)
        self.assertEqual(text_graph.count("fade=t=in"), 6)
        self.assertEqual(text_graph.count("fade=t=out"), 6)
        self.assertIn("[vfinal]", text_graph)
        self.assertIn("[6:v]format=rgba", text_graph)
        self.assertIn("[11:v]format=rgba", text_graph)
        self.assertNotIn("xfade=", text_graph)

    def test_text_intervals_are_half_open_to_prevent_double_exposure(self):
        text_graph = build_text_overlay_filter()
        # Adjacent between() intervals include their shared boundary in both
        # overlays. Use [start, end) intervals so only one scene's text can be
        # visible on a transition frame.
        self.assertNotIn("enable='between(t,", text_graph)
        self.assertIn("enable='gte(t,0.000000)*lt(t,9.866667)'", text_graph)
        self.assertIn("enable='gte(t,9.866667)*lt(t,19.733333)'", text_graph)

    def test_motion_gate_rejects_static_frames(self):
        self.assertFalse(motion_gate([0.0, 0.0]))
        self.assertTrue(motion_gate([12.0, 18.0]))
        self.assertFalse(motion_gate([100.0, 12.0]))


if __name__ == "__main__":
    unittest.main()
