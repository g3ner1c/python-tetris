# python-tetris

A simple and extensible Tetris engine, aimed for aiding in both game creation and game analysis

```py
>>> import tetris
>>> game = tetris.BaseGame()
>>> game.engine
Engine(queue=<class 'tetris.engine.SevenBag'>, rs=<tetris.engine.SRS object at 0x7f174561aa30>, scorer=<class 'tetris.engine.GuidelineScorer'>)
>>> game.queue.pieces
[<PieceType.S: 4>, <PieceType.O: 7>, <PieceType.J: 3>, <PieceType.I: 1>]
>>> game.piece
Piece(type=<PieceType.Z: 5>, x=18, y=3, r=0)
>>> print(game)


      @ @           
        @ @         
```
