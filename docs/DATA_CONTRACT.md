# Data contract

Each event requires a user, journey and unique event identifier; a UTC-compatible timestamp; channel and campaign; an event type of `impression`, `click` or `conversion`; non-negative cost and revenue; and a consent flag. Revenue is permitted only on conversion events. Non-consented records are removed at the ingestion boundary. Journeys use the first conversion as their cutoff, so later interactions cannot receive credit for an earlier purchase.

