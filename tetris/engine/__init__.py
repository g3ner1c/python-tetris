import dataclasses

from tetris.engine.abcs import Gravity
from tetris.engine.abcs import Queue
from tetris.engine.abcs import RotationSystem
from tetris.engine.abcs import Scorer
from tetris.engine.gravity import InfinityGravity
from tetris.engine.queue import SevenBag
from tetris.engine.rotation import SRS
from tetris.engine.scorer import GuidelineScorer


@dataclasses.dataclass
class Engine:
    gravity: type[Gravity]
    queue: type[Queue]
    rs: type[RotationSystem]
    scorer: type[Scorer]

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"{', '.join(f'{k}={v.__name__}' for k, v in vars(self).items())}"
            ")"
        )


DefaultEngine = Engine(
    gravity=InfinityGravity,
    queue=SevenBag,
    rs=SRS,
    scorer=GuidelineScorer,
)
