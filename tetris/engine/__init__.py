import dataclasses

from tetris.engine.abcs import Gravity
from tetris.engine.abcs import Queue
from tetris.engine.abcs import RotationSystem
from tetris.engine.abcs import Scorer
from tetris.engine.gravity import MarathonGravity
from tetris.engine.queue import SevenBag
from tetris.engine.rotation import SRS
from tetris.engine.scorer import GuidelineScorer


@dataclasses.dataclass
class Engine:
    gravity: type[Gravity]
    queue: type[Queue]
    rs: type[RotationSystem]
    scorer: type[Scorer]


DefaultEngine = Engine(
    gravity=MarathonGravity, queue=SevenBag, rs=SRS, scorer=GuidelineScorer
)
