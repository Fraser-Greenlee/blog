import pyxel

### utils.py
from collections import deque
from itertools import chain, repeat


PROPERTIES = ('you', 'push', 'win', 'hot', 'melt', 'sink')

NOUNS = (
    'baba',
    'flag',
    'wall',
    'rock',
    'grass',
    'skull',
    'key',
    'lava',
    'water',
    'empty'
)

class Entity(str):
    dir = '>'


ENTITIES = tuple(Entity(n.capitalize()) for n in NOUNS)

# Helper functions
isproperty = lambda symbol: symbol in PROPERTIES
isnoun = lambda symbol: symbol in NOUNS
isentity = lambda symbol: symbol in ENTITIES

SYMBOLS = (*PROPERTIES, *NOUNS, *ENTITIES, "is")
issymbol = lambda symbol: symbol in SYMBOLS
isis = lambda symbol: symbol == "is"

TEXT = (*PROPERTIES, *NOUNS, "is")
istext = lambda symbol: symbol in TEXT
isempty = lambda cell: cell == "."


def windowed(seq, n, fillvalue=None, step=1):
    if n < 0:
        raise ValueError('n must be >= 0')
    if n == 0:
        yield tuple()
        return

    window = deque(maxlen=n)
    i = n
    for _ in map(window.append, seq):
        i -= 1
        if not i:
            i = step
            yield tuple(window)

    size = len(window)
    if size == 0:
        return
    elif size < n:
        yield tuple(chain(window, repeat(fillvalue, n - size)))
    elif 0 < i < min(step, n):
        window += (fillvalue,) * i
        yield tuple(window)


def flatten(listOfLists):
    return chain.from_iterable(listOfLists)


def grid_to_string(grid, row_delimiter="\n", col_delimiter=""):
    """Convert grid to multiline string"""
    return row_delimiter.join(col_delimiter.join(row) for row in grid)


def string_to_grid(string, row_delimiter="\n", col_delimiter=""):
    """Convert multiline string to grid"""
    return [
        [cell for cell in row.replace(col_delimiter, "")]
        for row in string.split(row_delimiter)
    ]


def transpose(grid):
    return [list(col) for col in zip(*grid)]


def fliplr(grid):
    return [list(reversed(row)) for row in grid]


def rotate_p90(grid):
    """Rotate grid 90 deg clockwise"""
    return fliplr(transpose(grid))


def rotate_m90(grid):
    """Rotate grid 90 deg counterclockwise"""
    return transpose(fliplr(grid))


def rotate_180(grid):
    """Rotate grid 180 deg"""
    return rotate_p90(rotate_p90(grid))


def empty_NM(N, M, element="."):
    """Make an empty NxM grid"""
    return [[element for _ in range(M)] for _ in range(N)]


def make_behaviour(you=False, push=False, win=False, hot=False, melt=False, sink=False):
    """Helper to make a behaviour"""
    return dict(zip(PROPERTIES, (you, push, win, hot, melt, sink)))


def isvalidgrid(grid):
    """A pile of assertions to check that the grid is valid"""

    # Make sure grid is a list of lists
    assert isinstance(grid, list), "Grid is not a list"
    assert len(grid) > 0, "Grid is an empty list"
    assert isinstance(grid[0], list), "Grid must be a list of lists"

    N, M = len(grid), len(grid[0])

    assert M > 0, "Grid has zero width"

    for row in grid:
        assert len(row) == M, "Grid must be rectangular"
        for cell in row:
            assert cell in (*SYMBOLS, "."), f"'{cell}' is not a valid symbol"


### rules.py
def rulefinder(grid):
    """Find all the rules in the grid"""
    N, M = len(grid), len(grid[0])
    rules = []

    # Check every candidate against the grammar
    # Noun is (Noun OR Property)
    isrule = lambda t: (
        isnoun(t[0]) and isis(t[1]) and (isnoun(t[2]) or isproperty(t[2]))
    )

    # Horizontal rules
    if M >= 3:
        for row in grid:
            for t in windowed(row, 3):
                if isrule(t):
                    rules.append((t[0], t[2]))

    # Vertical rules
    if N >= 3:
        for col in zip(*grid):
            for t in windowed(col, 3):
                if isrule(t):
                    rules.append((t[0], t[2]))

    # Sort according to the first letter
    # rules = sorted(rules,key=lambda x:x[0])
    rules = sorted(rules)
    return rules


def ruleparser(rules):
    """Parse valid rules into behaviours and swaps"""

    behaviours = {noun: (make_behaviour()) for noun in NOUNS}
    swaps = []

    # Parse the rules
    for subject, action in rules:
        # Noun is (Noun OR Property)
        if isproperty(action):  # Noun is a Property
            behaviours[subject][action] = True
        else:  # (Noun is Noun)
            swaps.append((subject, action))

    swaps = sorted(swaps)

    # Add entry for text behaviour
    behaviours["text"] = make_behaviour(push=True)

    return behaviours, swaps


### main.py
from collections import defaultdict
from copy import deepcopy


BOARD_SIZE = 16
SPRITE_NAMES = {
    (16, 0): 'baba',
    (17, 0): 'flag',
    (18, 0): 'wall',
    (19, 0): 'rock',
    (17, 1): 'grass',
    (20, 3): 'skull',
    (20, 2): 'key',
    (16, 2): 'lava',
    (19, 1): 'water',

    (24, 0): 'is',

    (8, 0): 'you',
    (11, 0): 'push',
    (9, 0): 'win',
    (10, 0): 'hot',
    (12, 0): 'melt',
    (11, 1): 'sink',

    (0, 11): Entity('Baba'),
    (3, 0): Entity('Flag'),
    (4, 0): Entity('Wall'),
    (5, 0): Entity('Rock'),
    (0, 4): Entity('Grass'),
    (4, 4): Entity('Skull'),
    (7, 4): Entity('Key'),
    (5, 4): Entity('Water'),
    (2, 4): Entity('Lava'),
}
SPRITE_NAMES = defaultdict(lambda: '.', SPRITE_NAMES)
SPRITE_POS = {v: k for k, v in SPRITE_NAMES.items()}

STEPS = ("^", "V", "<", ">")

# Rotations and counter rotations which need to be applied to the grid such that the move direction is up
rotate_0 = lambda x: x
# Null rotation
rots = (rotate_0, rotate_180, rotate_p90, rotate_m90)
rots = dict(zip(STEPS, rots))
crots = (rotate_0, rotate_180, rotate_m90, rotate_p90)
crots = dict(zip(STEPS, crots))


class GameEnd(Exception):
    pass


class UnableToMove(Exception):
    pass


class YouWin(GameEnd):
    pass


class YouLose(GameEnd):
    pass


class Board:
    def __init__(self, level):
        tilemap = pyxel.tilemap(0)
        self.grid = []
        map_start = level * BOARD_SIZE
        for y in range(BOARD_SIZE):
            self.grid.append([])
            for x in range(map_start, map_start + BOARD_SIZE):
                sprite_index = tilemap.pget(x, y)
                self.grid[-1].append(SPRITE_NAMES[sprite_index])

    @staticmethod
    def swap(grid, swaps):
        """Apply all the swaps to the grid"""

        stationary = (a for a, b in swaps if a == b)
        swaps = ((a, b) for a, b in swaps if a != b and a not in stationary)

        new_grid = deepcopy(grid)
        for a, b in swaps:
            for j, row in enumerate(grid):
                for k, cell in enumerate(row):
                    if isentity(cell):
                        # If the rule applies to the cell, and no other rule has been applied yet
                        if cell.lower() == a and new_grid[j][k] == cell:
                            if b == 'empty':
                                new_grid[j][k] = '.'
                            else:
                                new_grid[j][k] = Entity(b.capitalize())

        return new_grid

    def attempt_to_move(self, pile, behaviours):
        """Attempt to move a pile of cells in accordance with their behaviour"""

        if len(pile) == 0:  # Empty pile
            raise UnableToMove

        if isempty(pile[0]):  # Trivial pile
            return pile
        elif len(pile) == 1:  # One-element pile
            raise UnableToMove

        def _is(cell, property):
            if istext(cell):
                cell = "text"
            elif cell == '.':
                cell = 'empty'
            return behaviours[cell.lower()][property]
        ispush = lambda cell: _is(cell, "push")
        issink = lambda cell: _is(cell, "sink")
        ishot = lambda cell: _is(cell, "hot")
        ismelt = lambda cell: _is(cell, "melt")

        # Larger pile
        def could_move():
            return (
                isempty(pile[1])
            ) or (
                ispush(pile[1])
            ) or (
                issink(pile[0])
            ) or (
                issink(pile[1])
            ) or (
                ishot(pile[0]) and ismelt(pile[1])
            ) or (
                ismelt(pile[0]) and ishot(pile[1])
            )

        if not could_move():
            raise UnableToMove

        if issink(pile[0]) or issink(pile[1]):
            return ('.', '.', *pile[2:])

        if ishot(pile[1]) and ismelt(pile[0]):
            return ('.', pile[1], *pile[2:])
        if ismelt(pile[1]) and ishot(pile[0]):
            return ('.', pile[0], *pile[2:])

        if isempty(pile[1]):
            return ('.', pile[0], *pile[2:])

        budged = self.attempt_to_move(pile[1:], behaviours)
        return (budged[0], pile[0], *budged[1:])

    def runstep(self, step, behaviours):
        """Advance grid a single step, given the step and the current behaviours"""
        grid = rots[step](self.grid)
        N, M = len(grid), len(grid[0])
        new_grid = empty_NM(N, M)

        isyou = lambda cell: isentity(cell) and behaviours[cell.lower()]["you"]
        iswin = lambda cell: isentity(cell) and behaviours[cell.lower()]["win"]

        for j, row in enumerate(grid):
            for k, cell in enumerate(row):
                if isempty(cell):
                    continue  # Already empty

                if not isyou(cell):
                    new_grid[j][k] = cell
                    continue

                cell.dir = step

                # Attempt to move
                pile = [cell] + [new_grid[l][k] for l in reversed(range(j))]
                try:
                    shifted_pile = self.attempt_to_move(pile, behaviours)
                    for l, elem in enumerate(reversed(shifted_pile)):
                        new_grid[l][k] = elem

                except UnableToMove:
                    if len(pile) > 1 and iswin(pile[1]):
                        raise YouWin(
                            f"You are '{cell}' and you've walked onto a '{pile[0]}'"
                            " which is 'win'. Hooray! :D "
                        )
                    new_grid[j][k] = cell

        new_grid = crots[step](new_grid)
        return new_grid

    def update(self, step=None):
        rules = rulefinder(self.grid)
        behaviours, swaps = ruleparser(rules)

        # Check for you is win condition
        for noun in behaviours:
            if behaviours[noun]["you"] and behaviours[noun]["win"]:
                raise YouWin(f"You are '{noun}' and you are 'win'. Hooray! :D")

            if behaviours[noun]["hot"] and behaviours[noun]["melt"]:
                swaps.append((noun, 'empty'))

        # Do the swap
        self.grid = self.swap(self.grid, swaps)

        entities_present = {j.lower() for j in flatten(self.grid) if isentity(j)}
        if not any(behaviours[e]["you"] for e in entities_present):
            raise YouLose("Nothing is 'you'. Game over.")

        # Timestep the grid
        if step:
            self.grid = self.runstep(step, behaviours)

    def draw(self):
        for _y, row in enumerate(self.grid):
            for _x, tilename in enumerate(row):
                x, y = _x*9, _y*9

                if tilename == '.':
                    continue
                u, v = SPRITE_POS[tilename]

                if tilename in PROPERTIES:
                    corner = pyxel.image(0).pget(u*8,v*8)
                    pyxel.rect(x, y+8, 9, 1, corner)
                    pyxel.rect(x+8, y, 1, 9, corner)

                if tilename == 'Baba':
                    v += '>V^<'.index(tilename.dir)

                pyxel.blt(x, y, 0, u*8, v*8, 8, 8)


class App:
    def __init__(self):
        pyxel.init(BOARD_SIZE*9, BOARD_SIZE*9, display_scale=5, title="BABA IS YOU")
        pyxel.load("game.pyxres")
        self.level = -1
        self.stop_banner = None
        self.next_level()
        pyxel.run(self.update, self.draw)

    def next_level(self):
        self.level += 1
        self.stop_banner = None
        if self.level > 2:
            self.stop_banner = self.show_end

        self.board = Board(self.level)
        if self.stop_banner is None:
            self.board.update()
        self.last_input = None
        self.all_steps = ''

    def undo(self):
        self.stop_banner = None
        self.board = Board(self.level)
        self.all_steps = self.all_steps[:-1]
        for step in self.all_steps:
            self.board.update(step)
            self.board.update()

    @staticmethod
    def show_win():
        pyxel.rect((BOARD_SIZE/2-2)*8, BOARD_SIZE/2*8-4, 4*8-1+16, 5+8, 3)
        pyxel.text((BOARD_SIZE/2-1)*8, BOARD_SIZE/2*8, 'YOU WIN', 10)

    @staticmethod
    def show_lose():
        pyxel.rect((BOARD_SIZE/2-2)*8, BOARD_SIZE/2*8-4, 4*8-1+16, 5+8, 1)
        pyxel.text((BOARD_SIZE/2-1)*8, BOARD_SIZE/2*8, 'YOU LOSE', 7)

    @staticmethod
    def show_end():
        pyxel.rect((BOARD_SIZE/2-2)*8, BOARD_SIZE/2*8-4, 4*8-1+16, 5+8, 3)
        pyxel.text((BOARD_SIZE/2-1)*8, BOARD_SIZE/2*8, 'THE END', 10)

    def update(self):
        inp = None
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT):
            inp = '<'
        elif pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT):
            inp = '>'
        elif pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP):
            inp = '^'
        elif pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN):
            inp = 'V'
        elif pyxel.btn(pyxel.KEY_SPACE) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_A):
            inp = 'X'
        else:
            self.last_input = None

        if inp == self.last_input:
            inp = None

        if inp:
            if (self.stop_banner is None or self.stop_banner in [self.show_lose, self.show_win]) and inp == 'X':
                self.undo()

            elif self.stop_banner is None and inp in '<>^V':
                try:
                    self.board.update(inp)
                    self.board.update()
                except YouWin:
                    self.stop_banner = self.show_win
                except YouLose:
                    self.stop_banner = self.show_lose

                self.all_steps += inp

            elif self.stop_banner == self.show_win:
                self.next_level()

            self.last_input = inp

    def draw(self):
        pyxel.cls(0)
        self.board.draw()
        if self.stop_banner is not None:
            self.stop_banner()


App()
