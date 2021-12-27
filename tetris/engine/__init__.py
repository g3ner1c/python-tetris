import dataclasses

from tetris.engine.abcs import Queue
from tetris.engine.abcs import RotationSystem
from tetris.engine.abcs import Scorer
from tetris.engine.queue import SevenBag
from tetris.engine.rotation import SRS
from tetris.engine.scorer import GuidelineScorer


@dataclasses.dataclass
class Engine:
    queue: type[Queue]
    rs: RotationSystem
    scorer: type[Scorer]


DefaultEngine = Engine(queue=SevenBag, rs=SRS(), scorer=GuidelineScorer)
