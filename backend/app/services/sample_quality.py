from __future__ import annotations


def quality_metadata(sample_size: int, minimum_significant_sample: int) -> dict:
    minimum = max(1, minimum_significant_sample)
    significant = sample_size >= minimum
    return {
        "sample_size": sample_size,
        "minimum_significant_sample": minimum,
        "is_significant": significant,
        "missing_to_significant": 0 if significant else minimum - sample_size,
    }


def adaptive_quality_metadata(
    *,
    sample_size: int,
    distinct_sources: int,
    sentiment_std_proxy: float,
    min_floor: int = 120,
    max_cap: int = 900,
) -> dict:
    # Adaptive threshold:
    # - Higher diversity lowers threshold.
    # - Higher volatility raises threshold.
    diversity_bonus = max(0, distinct_sources - 1) * 35
    volatility_penalty = int(max(0.0, sentiment_std_proxy) * 220)
    adaptive_threshold = max(min_floor, min(max_cap, 500 - diversity_bonus + volatility_penalty))
    is_significant = sample_size >= adaptive_threshold
    return {
        "sample_size": sample_size,
        "adaptive_threshold": adaptive_threshold,
        "is_significant": is_significant,
        "missing_to_significant": 0 if is_significant else adaptive_threshold - sample_size,
        "confidence_band": _confidence_band(sample_size, adaptive_threshold),
    }


def _confidence_band(sample_size: int, threshold: int) -> str:
    ratio = sample_size / max(1, threshold)
    if ratio >= 1.3:
        return "high"
    if ratio >= 1.0:
        return "medium"
    if ratio >= 0.6:
        return "low"
    return "very_low"
