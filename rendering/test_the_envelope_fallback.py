import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from unittest.mock import patch

from the_envelope_fallback import build_narration_command


class NarrationCommandTests(unittest.TestCase):
    def test_linux_falls_back_to_espeak_when_powershell_is_unavailable(self):
        raw = Path("/tmp/episode.wav")
        with patch("the_envelope_fallback.shutil.which") as which:
            which.side_effect = lambda name: "/usr/bin/espeak-ng" if name == "espeak-ng" else None
            command = build_narration_command("hello world", raw)

        self.assertEqual(command, ["espeak-ng", "-w", str(raw), "hello world"])


if __name__ == "__main__":
    unittest.main()
