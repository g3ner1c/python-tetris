"""Collection of presets from various Tetris games."""

from __future__ import annotations

from tetris.engine import EngineFactory
from tetris.impl import gravity, queue, rotation, scorer

Modern = EngineFactory(
    gravity=gravity.InfinityGravity,
    queue=queue.SevenBag,
    rotation_system=rotation.SRS,
    scorer=scorer.GuidelineScorer,
)

Tetrio = EngineFactory(
    gravity=gravity.InfinityGravity,
    queue=queue.SevenBag,
    rotation=rotation.TetrioSRS,
    scorer=scorer.GuidelineScorer,
)

NES = EngineFactory(
    gravity=gravity.NESGravity,
    queue=queue.NES,
    rotation_system=rotation.NRS,
    scorer=scorer.NESScorer,
)
