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
    build_audio_filter,
)
from rendering.story_transition_readability import (
    transition_sample_timestamp,
    transition_text_pass,
    approximately_contains,
)


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

    def test_episode_profiles_are_diverse_and_never_repeat_back_to_back(self):
        profiles = [episode_profile(f"EP{i:02d}")["profile_key"] for i in range(1, 31)]
        self.assertGreaterEqual(len(set(profiles)), 10)
        self.assertTrue(all(left != right for left, right in zip(profiles, profiles[1:])))
        counts = {key: profiles.count(key) for key in set(profiles)}
        self.assertLessEqual(max(counts.values()), 3)

    def test_archive_records_and_courthouse_use_separate_visual_profiles(self):
        self.assertEqual(episode_profile("EP03")["profile_key"], "photo_archive")
        self.assertEqual(episode_profile("EP08")["profile_key"], "records_room")
        self.assertEqual(episode_profile("EP04")["profile_key"], "courthouse")
        self.assertEqual(len({
            episode_profile("EP03")["profile_key"],
            episode_profile("EP08")["profile_key"],
            episode_profile("EP04")["profile_key"],
        }), 3)

    def test_motion_gate_checks_each_scene_and_rejects_static_beats(self):
        self.assertFalse(motion_gate([[0.1, 0.2]] * 6))
        self.assertTrue(motion_gate([[5.0, 8.0]] * 6))
        self.assertFalse(motion_gate([[5.0, 8.0], [1.0, 8.0]] + [[5.0, 8.0]] * 4))

    def test_text_layers_are_separate_and_transition_intervals_do_not_overlap(self):
        graph = build_xfade_filter()
        self.assertEqual(graph.count("xfade=transition=fade"), 5)
        self.assertNotIn("text", graph.lower())
        text_graph = build_text_overlay_filter()
        self.assertEqual(text_graph.count("overlay="), 1)
        self.assertIn("concat=n=6:v=1:a=0", text_graph)
        self.assertNotIn("enable=", text_graph)
        self.assertIn("trim=duration=9.900000,setpts=PTS-STARTPTS[txt0]", text_graph)
        self.assertIn("trim=duration=9.900000,setpts=PTS-STARTPTS[txt1]", text_graph)
        self.assertIn("[vout][text]overlay=", text_graph)
        self.assertNotIn("xfade=", text_graph)

    def test_audio_graph_mixes_narration_with_a_full_duration_ambient_bed(self):
        graph = build_audio_filter()
        self.assertIn("[12:a]apad=pad_dur=60[voice]", graph)
        self.assertIn("[13:a]volume=", graph)
        self.assertIn("amix=inputs=2:duration=longest", graph)
        self.assertIn("normalize=0", graph)
        self.assertIn("[aout]", graph)

    def test_transition_ocr_accepts_a_partially_misread_reveal_title(self):
        self.assertTrue(approximately_contains("THE REVEAL", "REVEAR", threshold=0.75))
        self.assertFalse(approximately_contains("THE REVEAL", "THE REACTION", threshold=0.75))
        self.assertTrue(transition_text_pass("ris e REVEAR", "THE REACTION", "THE REVEAL"))

    def test_transition_text_gate_rejects_double_exposure(self):
        self.assertTrue(transition_text_pass("THE OBJECT", "WIDE ESTABLISHING", "THE OBJECT"))
        self.assertFalse(transition_text_pass("WIDE ESTABLISHING THE OBJECT", "WIDE ESTABLISHING", "THE OBJECT"))
        self.assertFalse(transition_text_pass("WIDE ESTABLISHING", "WIDE ESTABLISHING", "THE OBJECT"))

    def test_transition_text_gate_tolerates_minor_ocr_misreads_but_not_wrong_titles(self):
        self.assertTrue(transition_text_pass("THEOBIECE", "WIDE ESTABLISHING", "THE OBJECT"))
        self.assertTrue(transition_text_pass("THE DECISlON", "THE REVEAL", "THE DECISION"))
        self.assertFalse(transition_text_pass("THE REVEAL", "THE REVEAL", "THE REACTION"))
        self.assertTrue(transition_text_pass("THE 2 EEL\nTHE DECISION", "THE REVEAL", "THE DECISION"))

    def test_transition_ocr_samples_after_background_crossfade_and_title_fade_in(self):
        self.assertAlmostEqual(transition_sample_timestamp(1), 13.5, places=3)
        self.assertAlmostEqual(transition_sample_timestamp(5), 53.1, places=3)

    def test_classification_does_not_claim_ai_video_generation(self):
        self.assertEqual(classify_artifact(), "DETERMINISTIC_MOTION_TEXT_FALLBACK")


if __name__ == "__main__":
    unittest.main()
