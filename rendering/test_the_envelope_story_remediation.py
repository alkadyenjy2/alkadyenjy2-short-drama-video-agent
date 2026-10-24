"""Story-specific visual remediation regression tests."""
import unittest

from rendering.the_envelope_story_remediation import (
    EPISODES,
    SCENES_PER_EPISODE,
    episode_profile,
    motion_gate,
    classify_artifact,
    build_xfade_filter,
    build_text_overlay_filter,
)
from rendering.story_transition_readability import transition_text_pass


class StoryRemediationTests(unittest.TestCase):
    def test_all_thirty_episodes_have_six_story_scenes(self):
        self.assertEqual(len(EPISODES), 30)
        self.assertTrue(all(len(ep["scenes"]) == SCENES_PER_EPISODE for ep in EPISODES))

    def test_key_episodes_have_distinct_story_locations_and_props(self):
        expected = {
            "EP01": ("front_door", "brass_mailbox"),
            "EP02": ("kitchen", "coffee_mug"),
            "EP15": ("office", "scattered_letters"),
            "EP30": ("attic_archive", "archive_chest"),
        }
        for episode, (place, prop) in expected.items():
            profile = episode_profile(episode)
            self.assertEqual(profile["place_id"], place)
            self.assertIn(prop, profile["objects"])

    def test_other_episodes_derive_visual_profile_from_story_text(self):
        self.assertNotEqual(episode_profile("EP03")["place_id"], episode_profile("EP30")["place_id"])
        self.assertTrue(episode_profile("EP05")["objects"])

    def test_motion_gate_checks_each_scene_and_rejects_static_beats(self):
        self.assertFalse(motion_gate([[0.1, 0.2]] * 6))
        self.assertTrue(motion_gate([[5.0, 8.0]] * 6))
        self.assertFalse(motion_gate([[5.0, 8.0], [1.0, 8.0]] + [[5.0, 8.0]] * 4))

    def test_text_layers_are_separate_and_transition_intervals_do_not_overlap(self):
        graph = build_xfade_filter()
        self.assertEqual(graph.count("xfade=transition=fade"), 5)
        self.assertNotIn("text", graph.lower())
        text_graph = build_text_overlay_filter()
        self.assertEqual(text_graph.count("overlay="), 6)
        self.assertNotIn("enable='between(t,", text_graph)
        self.assertIn("enable='gte(t,0.000000)*lt(t,9.900000)'", text_graph)
        self.assertIn("enable='gte(t,9.900000)*lt(t,19.800000)'", text_graph)
        self.assertNotIn("xfade=", text_graph)

    def test_transition_text_gate_rejects_double_exposure(self):
        self.assertTrue(transition_text_pass("THE OBJECT", "WIDE ESTABLISHING", "THE OBJECT"))
        self.assertFalse(transition_text_pass("WIDE ESTABLISHING THE OBJECT", "WIDE ESTABLISHING", "THE OBJECT"))
        self.assertFalse(transition_text_pass("WIDE ESTABLISHING", "WIDE ESTABLISHING", "THE OBJECT"))

    def test_classification_does_not_claim_ai_video_generation(self):
        self.assertEqual(classify_artifact(), "DETERMINISTIC_MOTION_TEXT_FALLBACK")


if __name__ == "__main__":
    unittest.main()
