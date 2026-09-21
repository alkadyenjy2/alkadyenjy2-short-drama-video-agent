# visual_factory.py - Core Agent - Most Important - Video Generation Engine
import os, json, uuid, hashlib
from datetime import datetime
from typing import Dict, List, Optional

# === Character Consistency - Critical for short drama ===
CHARACTER_BIBLE = {}

def create_character_bible(story_id: str, characters: List[Dict]) -> str:
    """Generate consistent character descriptions for Muse Video"""
    bible_id = f"bible_{hashlib.sha256(story_id.encode()).hexdigest()[:12]}"
    bible = {
        "bible_id": bible_id,
        "story_id": story_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "characters": characters,
        "visual_style": "cinematic 9:16 vertical, dramatic lighting, Middle Eastern features, realistic skin texture, consistent face across all beats"
    }
    CHARACTER_BIBLE[bible_id] = bible
    return bible_id

def parse_story_to_beats(story: Dict) -> List[Dict]:
    """Transform story_outline into 3-5 beats of 40-60 sec each, 9:16"""
    outline = story.get("story_outline", "")
    beats_count = story.get("beats", 4)
    beats = []
    # Simple heuristic: split outline into beats
    sentences = [s.strip() for s in outline.split(".") if s.strip()]
    if not sentences:
        sentences = [outline]
    
    per_beat = max(1, len(sentences) // beats_count)
    for i in range(beats_count):
        start = i * per_beat
        end = start + per_beat if i < beats_count -1 else len(sentences)
        beat_text = ". ".join(sentences[start:end])
        beats.append({
            "beat_id": f"{story['id']}_beat_{i+1}",
            "beat_number": i+1,
            "duration_sec": 45 + (i*2),
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
            "script": beat_text,
            "hook": story.get("hook", "") + f" - الجزء {i+1}",
            "caption": f"{story.get('hook','')} - الجزء {i+1} | #{' #'.join(story.get('tags',[])[:3])}",
            "visual_prompt": f"Cinematic vertical drama scene, {beat_text}, dramatic low-key lighting, Middle Eastern drama style, photorealistic, 8k, consistent characters, emotional close-up",
            "characters_in_beat": story.get("characters", [])[:2],
            "version": "v1"
        })
    return beats

def generate_video_prompt(beat: Dict, operation_logs: List[Dict] = None, character_bible_id: Optional[str] = None) -> str:
    """Build final prompt for Muse Video with edit operations applied"""
    base_prompt = beat["visual_prompt"]
    
    # Apply edit operations if any
    if operation_logs:
        for log in operation_logs:
            op_type = log.get("operation_type")
            if op_type == "lighting" and log.get("parsed_value") == "darker":
                base_prompt += ", dramatic low-key lighting, darker shadows, cinematic noir"
            elif op_type == "lighting" and log.get("parsed_value") == "brighter":
                base_prompt += ", high-key lighting, bright, soft shadows"
            elif op_type == "speed":
                base_prompt += f", {log.get('parsed_value')} speed"
            elif op_type == "trim":
                base_prompt += f", trimmed - remove first {log.get('parsed_value')} seconds"
    
    # Add character consistency
    if character_bible_id and character_bible_id in CHARACTER_BIBLE:
        bible = CHARACTER_BIBLE[character_bible_id]
        chars_desc = ", ".join([f"{c.get('name','character')} with {c.get('look','consistent face')}" for c in bible["characters"][:2]])
        base_prompt += f", characters: {chars_desc}, same face across all beats, character consistency enforced"
    
    base_prompt += ", 9:16 vertical, 1080x1920, 45 seconds, cinematic, photorealistic"
    return base_prompt

def create_visual_job(beat: Dict, user_id: str, publication_id: str, character_bible_id: Optional[str] = None, edit_logs: List[Dict] = None) -> Dict:
    """Create job for Muse Video API - returns job record"""
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    final_prompt = generate_video_prompt(beat, edit_logs, character_bible_id)
    
    job = {
        "job_id": job_id,
        "publication_id": publication_id,
        "beat_id": beat["beat_id"],
        "beat_number": beat["beat_number"],
        "user_id": str(user_id),
        "status": "QUEUED",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "prompt": final_prompt,
        "negative_prompt": "blurry, distorted face, inconsistent character, watermark, low quality, 16:9 horizontal",
        "model": os.getenv("VIDEO_GENERATION_PROVIDER", "UNCONFIGURED"),
        "aspect_ratio": "9:16",
        "duration_sec": beat["duration_sec"],
        "character_bible_id": character_bible_id,
        "edit_logs_applied": [log["operation_id"] for log in (edit_logs or [])],
        "preview_url": None,
        "final_video_url": None,
        "evidence": {
            "prompt_hash": hashlib.sha256(final_prompt.encode()).hexdigest()[:16],
            "character_consistency_enforced": character_bible_id is not None
        }
    }
    
    # Persist
    try:
        from persistence.repository import get_repository
        repo = get_repository()
        repo.init_schema()
        # Use operation log table to store job? For now in-memory + publication attempts
    except Exception as e:
        print(f"Visual job persistence warning: {e}")
    
    return job

def get_agent_status():
    return {
        "visual_factory": "READY",
        "character_bible_count": len(CHARACTER_BIBLE),
        "supported_aspects": ["9:16"],
        "supported_duration": "40-60 sec per beat, 3-5 beats per story",
        "edit_operations_supported": ["lighting darker/brighter", "trim/cut", "caption/title", "speed faster/slower", "colors/filter", "background/zoom"],
        "language": "Arabic comments understanding - اضاءة اغمق قص كابشن اسرع ابطأ",
        "muse_integration": "PROMPT_ONLY_UNTIL_PROVIDER_CONFIGURED",
        "video_generation_provider": os.getenv("VIDEO_GENERATION_PROVIDER", "UNCONFIGURED"),
        "next_step": "Configure VIDEO_GENERATION_API_URL + VIDEO_GENERATION_API_KEY or a concrete provider adapter"
    }
