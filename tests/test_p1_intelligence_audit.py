import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from trend_intelligence import TrendObservation, score_observation, rank_trends, recommended_episode_count
from rights_engine import assess_adaptation, validate_source_url
from idea_inbox import create_idea_item
from analytics_schema import normalize_metric_event

def main():
    o=TrendObservation("youtube","https://youtube.com/watch?v=1","2026-09-21T20:00:00Z","test",views=100000,likes=10000,comments=500,shares=3000,duration_sec=45,age_hours=10,genre="romance")
    s=score_observation(o); assert s["evidence_status"]=="OBSERVED" and s["trend_score"]>0
    ranked=rank_trends([o]); assert ranked[0]["title"]=="test"
    assert recommended_episode_count(s)==6
    assert validate_source_url("https://example.com/a") and not validate_source_url("javascript:x")
    a=assess_adaptation("copyrighted",similarity_score=.9,copies_dialogue=True); assert a["status"]=="DO_NOT_PUBLISH_UNTIL_REVIEW"
    b=assess_adaptation("user_idea",user_owned=True); assert b["status"]=="ADAPT_WITH_PERMISSION"
    item=create_idea_item("url","https://example.com/story"); assert item["status"]=="RECEIVED"
    event=normalize_metric_event("youtube","vid1","2026-09-21T20:00:00Z",{"views":10,"revenue":1.2,"currency":"USD"}); assert event["metrics"]["views"]==10
    print("P1 AUDIT: 8 PASS")

if __name__ == "__main__": main()

# CI trigger: P1 audit included in workflow.
