import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from learning_loop import build_learning_signal, compare_story_variants


def test_learning_never_fabricates_missing_metrics():
    out = build_learning_signal([{
        "metrics": {"views": 100, "likes": 10}
    }])
    assert out["signals"]["views"] == 100
    assert out["signals"]["watch_time_sec"] is None
    assert out["signals"]["revenue"] is None


def test_variant_feedback_is_observed():
    out = compare_story_variants({
        "a": [{"metrics": {"views": 100, "likes": 10}}],
        "b": [{"metrics": {"views": 200, "likes": 10, "followers_gained": 4}}],
    })
    assert len(out) == 2
    assert out[1]["signals"]["followers_gained"] == 4


if __name__ == "__main__":
    test_learning_never_fabricates_missing_metrics()
    test_variant_feedback_is_observed()
    print("LEARNING LOOP AUDIT: 2 PASS")
