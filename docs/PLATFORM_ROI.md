# Platform ROI Analysis - Drama AI

## 1. TikTok - 70% effort
- Audience: Already looking for short drama, 9:16 native
- Monetization: Creativity Program $0.50-$1/1k views, LIVE gifts, series paywall
- Growth: Fastest 0→100k in 30 days with 2 vids/day
- Requirements: App registration + video.publish scope + app review for PUBLIC
- Evidence: INIT_URL + STATUS_URL polling

## 2. YouTube Shorts - 20% effort
- Audience: Trust + long shelf life (years not 24h)
- Monetization: 45% revenue share Shorts, AdSense, Memberships
- Growth: Slower but sustainable, B2B clients trust YT more
- Requirements: GCP + YouTube Data API + OAuth verification (forced PRIVATE if unverified after July 28 2020)
- Evidence: resumable upload → videoId

## 3. Instagram Reels + Facebook Reels - 10% effort
- Audience: B2B - small production companies, agencies who will pay subscriptions
- Monetization: Reels Play Bonus (limited), brand deals, subscription funnel to bot
- Growth: Medium, good for branding
- Requirements: Meta app + instagram_content_publish + Business account + Page token + public video_url
- Evidence: POST /{ig-id}/media → poll → POST /media_publish → media_id + permalink

Funnel: TikTok/Shorts/Reels → CTA "عايز نفس القصة بشخصياتك؟ /start" → Telegram Bot → Free/Creator $19/Agency $99
