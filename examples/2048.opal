package opal:   import *;
package random: import choice, random;
package time:   import sleep;
package math:   import ceil;

new int             RESY = 840;
new tuple   BORDER_COLOR = (0, 0, 0),
              TEXT_COLOR = (0, 0, 0),
                BG_COLOR = (255, 255, 255),
              LAST_COLOR = (  0, 255, 0);
new int BORDER_THICKNESS = 2,
          LAST_THICKNESS = 4;
new dict COLORS;
COLORS = {
    2:    (230, 217, 204),
    4:    (227, 216, 195),
    8:    (181, 112, 51),
    16:   (219,  99, 35),
    32:   (209,  71, 40),
    64:   (232,  66, 30),
    128:  (212, 175, 55),
    256:  (237, 199, 66),
    512:  (247, 205, 62),
    1024: (255, 208, 43),
    2048: (255, 198, 0)
};

new Vector RESOLUTION = Vector(RESY - 40, RESY);

new int cellWidth = RESOLUTION.x // 4,
          yOffset = RESOLUTION.y - RESOLUTION.x;

new Vector cellWidthVec = Vector(cellWidth, cellWidth);

new class Grid {
    new method __init__() {
        this.grid = [[0 for _ in range(4)] for _ in range(4)];
        this.old  = this.copy();

        this.last = None;

        this.pressed = {
            K_UP:     False,
            K_DOWN:   False,
            K_RIGHT:  False,
            K_LEFT:   False,
            K_r:      False,
            K_ESCAPE: False,
            K_y:      False,
            K_n:      False
        };
    }

    new method __getAvailable(grid) {
        new list available = [];

        for y = 0; y < 4; y++ {
            for x = 0; x < 4; x++ {
                if grid[y][x] == 0 {
                    available.append(Vector(x, y));
                }
            }
        }

        return available;
    }

    new method addNum() {
        new list available = this.__getAvailable(this.grid);

        if len(available) == 0 {
            return;
        }

        this.last = choice(available);
        this.grid[this.last.y][this.last.x] = 4 if random() < 0.1 else 2;
    }

    new method __arrange(grid, x, array) {
        for y = 0; y < 4; y++ {
            grid[y][x] = array[y];
        }
    }

    new method __slideLeft(array) {
        array = [x for x in array if x != 0];
        return array + [0 for _ in range(4 - len(array))];
    }

    new method __slideUp(x) {
        new list tmp = [this.grid[y][x] for y in range(4) if this.grid[y][x] != 0];
        return tmp + [0 for _ in range(4 - len(tmp))];
    }

    new method __combineLeftUp(array) {
        for i = 0; i < 3; i++ {
            if array[i] == array[i + 1] {
                array[i] += array[i + 1];
                array[i + 1] = 0;
            }
        }
    }

    new method __slideRight(array) {
        array = [x for x in array if x != 0];
        return [0 for _ in range(4 - len(array))] + array;
    }

    new method __slideDown(x) {
        new list tmp = [this.grid[y][x] for y in range(4) if this.grid[y][x]];
        return [0 for _ in range(4 - len(tmp))] + tmp;
    }

    new method __combineRightDown(array) {
        for i = 3; i >= 1; i-- {
            if array[i] == array[i - 1] {
                array[i] += array[i - 1];
                array[i - 1] = 0;
            }
        }
    }

    new method __moveLeft(array) {
        array = this.__slideLeft(array);
        this.__combineLeftUp(array);
        return this.__slideLeft(array);
    }

    new method __moveUp(grid, x) {
        new list tmp = this.__slideUp(x);
        this.__combineLeftUp(tmp);
        this.__arrange(grid, x, this.__slideLeft(tmp));
    }

    new method __moveRight(array) {
        array = this.__slideRight(array);
        this.__combineRightDown(array);
        return this.__slideRight(array);
    }

    new method __moveDown(grid, x) {
        new list tmp = this.__slideDown(x);
        this.__combineRightDown(tmp);
        this.__arrange(grid, x, this.__slideRight(tmp));
    }

    new method copy() {
        new list tmp = [[0 for _ in range(4)] for _ in range(4)];

        for y = 0; y < 4; y++ {
            for x = 0; x < 4; x++ {
                tmp[y][x] = this.grid[y][x];
            }
        }

        return tmp;
    }

    new method compare(other) {
        for y = 0; y < 4; y++ {
            for x = 0; x < 4; x++ {
                if this.grid[y][x] != other[y][x] {
                    return True;
                }
            }
        }
        return False;
    }

    new method move() {
        if this.pressed[K_r] {
            this.last = None;
            this.grid = this.old;
            this.pressed[K_r] = False;
            return True;
        }

        new list tmp = this.copy();
        new list oldT = this.copy();

        if this.pressed[K_LEFT] {
            for y = 0; y < 4; y++ {
                this.grid[y] = this.__moveLeft(this.grid[y]);
            }

            this.pressed[K_LEFT] = False;
        } elif this.pressed[K_UP] {
            for x = 0; x < 4; x++ {
                this.__moveUp(this.grid, x);
            }

            this.pressed[K_UP] = False;
        } elif this.pressed[K_RIGHT] {
            for y = 0; y < 4; y++ {
                this.grid[y] = this.__moveRight(this.grid[y]);
            }

            this.pressed[K_RIGHT] = False;
        } elif this.pressed[K_DOWN] {
            for x = 0; x < 4; x++ {
                this.__moveDown(this.grid, x);
            }

            this.pressed[K_DOWN] = False;
        }

        if this.compare(tmp) {
            this.old = oldT;
            this.addNum();

            return True;
        }

        return False;
    }

    new method hasLost() {
        new list grid = this.copy();

        for i = 0; i < 4; i++ {
            grid[i] = this.__moveLeft(grid[i]);
            grid[i] = this.__moveRight(grid[i]);
            this.__moveUp(grid, i);
            this.__moveDown(grid, i);
        }

        return len(this.__getAvailable(grid)) == 0;
    }

    new method hasWon() {
        for y = 0; y < 4; y++ {
            for x = 0; x < 4; x++ {
                if this.grid[y][x] == 2048 {
                    return True;
                }
            }
        }
        return False;
    }
}

new class Program : Graphics {
    new method __init__() {
        super().__init__(RESOLUTION, caption = "2048");
        this.grid = Grid();

        this.__scoreFont    = this.getSysFont(size = 48);
        this.__cellFontSize = round(196 / (800 / RESOLUTION.x));
        this.__endFont      = this.getSysFont(size = round(128 / (800 / RESOLUTION.x)));

        this.__won = False;
    }

    new method __renderGrid() {
        this.fill(BG_COLOR);

        new int sum_ = 0;

        for y = 0; y < 4; y++ {
            for x = 0; x < 4; x++ {
                new dynamic tmp = Vector(x, y) * cellWidth;
                tmp.y += yOffset;

                new dynamic cell = this.grid.grid[y][x];

                if cell != 0 {
                    if cell > 2048 {
                        this.fastRectangle(tmp, cellWidthVec, COLORS[2048]);
                    } else {
                        this.fastRectangle(tmp, cellWidthVec, COLORS[cell]);
                    }

                    new dynamic strCell = str(cell);
                    this.simpleText(strCell, tmp + cellWidthVec // 2, TEXT_COLOR, True, True, font = this.getSysFont(size = this.__cellFontSize // ceil(len(strCell) / 2)));
                    sum_ += cell;
                }
            }
        }

        if this.grid.last is not None {
            tmp = this.grid.last.copy() * cellWidth;
            tmp.y += yOffset;

            this.fastRectangle(tmp, cellWidthVec, LAST_COLOR, LAST_THICKNESS);
        }

        this.simpleText(f"Score: {sum_}", Vector(2, 2), TEXT_COLOR, font = this.__scoreFont);
    }

    new method __stop(msg) {
        this.fill(BG_COLOR);
        this.__renderGrid();
        new dynamic tmp = Vector(RESOLUTION.x, RESOLUTION.x);
        this.rectangle(Vector(0, yOffset), tmp, alpha = 180);

        tmp //= 2;
        tmp.y += yOffset;
        this.simpleText(msg, tmp, TEXT_COLOR, True, True, font = this.__endFont);
        this.rawUpdate();
    }

    new method __reset() {
        this.grid = Grid();
        this.grid.addNum();
        this.grid.addNum();
        this.__renderGrid();
    }

    new method drawLoop() {
        if this.grid.move() {
            this.__renderGrid();
        }

        if this.grid.pressed[K_ESCAPE] {
            this.__stop("Reset? (Press Y/N)");

            while (not this.grid.pressed[K_y]) and (not this.grid.pressed[K_n]) {
                this.updateEvents();
            }

            if this.grid.pressed[K_y] {
                this.grid.pressed[K_y] = False;

                this.__reset();
                return;
            } elif this.grid.pressed[K_n] {
                this.grid.pressed[K_n] = False;
                this.__renderGrid();

                return;
            }
        }

        if this.grid.hasWon() and not this.__won {
            this.__stop("You won!");
            this.__won = True;
            sleep(2);

            return;
        }

        if this.grid.hasLost() {
            this.__stop("Game over!");
            sleep(3);

            this.__reset();
        }
    }

    new method __keyDown(event) {
        if event.key in this.grid.pressed {
            this.grid.pressed[event.key] = True;
        }
    }

    new method __keyUp(event) {
        if event.key in this.grid.pressed {
            this.grid.pressed[event.key] = False;
        }
    }

    new method run() {
        this.event(KEYDOWN)(this.__keyDown);
        this.event(KEYUP)(this.__keyUp);

        this.grid.addNum();
        this.grid.addNum();

        this.__renderGrid();
        super().run(drawBackground = False);
    }
}

main {
    Program().run();
}
