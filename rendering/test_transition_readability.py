"""Unit tests for actual transition-frame readability gate."""
import unittest

from rendering.transition_readability import transition_text_pass


class TransitionReadabilityTests(unittest.TestCase):
    def test_clean_incoming_title_passes(self):
        self.assertTrue(transition_text_pass("A MEMORY RETURNS", "THE ENVELOPE", "A MEMORY RETURNS"))

    def test_previous_and_incoming_titles_fail_double_exposure(self):
        self.assertFalse(transition_text_pass("THE ENVELOPE A MEMORY RETURNS", "THE ENVELOPE", "A MEMORY RETURNS"))

    def test_previous_title_only_fails_missing_incoming_scene(self):
        self.assertFalse(transition_text_pass("THE ENVELOPE", "THE ENVELOPE", "A MEMORY RETURNS"))

    def test_title_match_is_case_insensitive(self):
        self.assertTrue(transition_text_pass("the warning", "A MEMORY RETURNS", "THE WARNING"))


if __name__ == "__main__":
    unittest.main()
