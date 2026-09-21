{
  "audit_date": "2026-09-20",
  "graph_version": "v21.0",
  "supported_versions": [
    "v21.0",
    "v22.0",
    "v23.0",
    "v24.0"
  ],
  "publisher_inspected": "publisher.py (fake) -> P0 real expected",
  "findings": {
    "fake_success_detected": true,
    "evidence_gate_enforced_in_P0": true,
    "current_fake_block": "PlatformAdapter returns success True with ig_{video_path} no receipt",
    "expected_real_flow": {
      "instagram": "POST /{ig-id}/media -> container_id -> GET /{container_id}?fields=status_code -> FINISHED -> POST /{ig-id}/media_publish -> media_id -> GET /{media_id}?fields=permalink",
      "facebook": "POST graph-video.facebook.com/{version}/{page-id}/videos -> video_id -> GET /{video_id}?fields=permalink_url"
    }
  },
  "error_taxonomy": {
    "authentication_failure": {
      "codes": [
        190,
        102
      ],
      "http": [
        401
      ],
      "retryable": false,
      "action": "HUMAN_ACTION_REQUIRED token refresh"
    },
    "authorization_failure": {
      "codes": [
        200,
        10
      ],
      "http": [
        403
      ],
      "retryable": false,
      "action": "HUMAN_ACTION_REQUIRED permissions"
    },
    "invalid_account_configuration": {
      "reason": "instagram_business_account null or not linked to Page",
      "retryable": false
    },
    "invalid_media": {
      "codes": [
        2207001,
        2207026,
        2207042
      ],
      "retryable": false
    },
    "invalid_url": {
      "reason": "video_url not public HTTPS or HEAD not 200 video/mp4",
      "retryable": false,
      "hosting_required": true
    },
    "container_processing_failure": {
      "status": "ERROR",
      "retryable": false,
      "note": "create new container"
    },
    "rate_limit": {
      "codes": [
        4,
        17,
        80004
      ],
      "http": [
        429
      ],
      "retryable": true,
      "backoff": "exponential 1.5s cap 60s max 3"
    },
    "temporary_provider_failure": {
      "http": [
        500,
        502,
        503,
        504
      ],
      "retryable": true
    }
  },
  "deliverables": [
    "META_GAP_MATRIX.md",
    "META_EVIDENCE_REPORT.json",
    "test_meta_audit.py",
    "Meta-patched ZIP after verification"
  ]
}