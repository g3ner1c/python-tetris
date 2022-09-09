"""Collection of presets from various Tetris games."""

from __future__ import annotations

from tetris.engine import EngineFactory
from tetris.impl import gravity, queue, rotation, scorer

__all__ = (
    "Modern",
    "NES",
    "Tetrio",
)

Modern = EngineFactory(
    gravity=gravity.InfinityGravity,
    queue=queue.SevenBag,
    rotation_system=rotation.SRS,
    scorer=scorer.GuidelineScorer,
)

NES = EngineFactory(
    gravity=gravity.NESGravity,
    queue=queue.NES,
    rotation_system=rotation.NRS,
    scorer=scorer.NESScorer,
)

Tetrio = EngineFactory(
    gravity=gravity.InfinityGravity,
    queue=queue.SevenBag,
    rotation_system=rotation.TetrioSRS,
    scorer=scorer.GuidelineScorer,
)
