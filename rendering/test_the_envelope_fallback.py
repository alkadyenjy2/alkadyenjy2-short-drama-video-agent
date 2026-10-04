import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
from the_envelope_fallback import EPISODES, build_narration_command, wrap_text


class NarrationCommandTests(unittest.TestCase):
    def test_linux_falls_back_to_espeak_when_powershell_is_unavailable(self):
        raw = Path("/tmp/episode.wav")
        with patch("the_envelope_fallback.shutil.which") as which:
            which.side_effect = lambda name: "/usr/bin/espeak-ng" if name == "espeak-ng" else None
            command = build_narration_command("hello world", raw)

        self.assertEqual(command, ["espeak-ng", "-w", str(raw), "hello world"])


class TextLayoutTests(unittest.TestCase):
    def test_long_episode_copy_is_wrapped_to_fit_vertical_card(self):
        for _, hook, body in EPISODES:
            for line in wrap_text(hook, width=28).splitlines():
                self.assertLessEqual(len(line), 28)
            for line in wrap_text(body, width=30).splitlines():
                self.assertLessEqual(len(line), 30)

    def test_wrapping_preserves_all_words(self):
        source = "Lina receives an envelope in her own handwriting"
        wrapped = wrap_text(source, width=18)
        self.assertEqual(" ".join(wrapped.splitlines()), source)


if __name__ == "__main__":
    unittest.main()
