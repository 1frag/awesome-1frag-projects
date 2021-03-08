# Based on https://www.cs.mcgill.ca/~aassaf9/python/sudoku.txt
from itertools import product, chain, cycle


def solve_sudoku(grid, nr=3, nc=3):
    s = nr * nc
    def f(cnt): return [range(1, s + 1) for _ in range(cnt)]
    def b(r, c): return 1 + ((r - 1) // nr) * nr + ((c - 1) // nc)

    def apply(solution):
        for (r, c, n) in solution:
            grid[r - 1][c - 1] = n
        return grid.copy()

    _, x, y = exact_cover(
        {j: set() for j in chain(*[zip(cycle([k]), product(*f(2))) for k in range(4)])},
        {(r, c, n): [*enumerate(((r, c), (r, n), (c, n), (b(r, c), n)))] for r, c, n in product(*f(3))}
    )
    [list(select(x, y, (i, j, n))) for i, j in product(*f(2)) if (n := grid[i - 1][j - 1])]

    yield from (apply(sol) for sol in solve(x, y, []))


def exact_cover(x, y):
    return [x[j].add(i) for i, row in y.items() for j in row], x, y


def solve(x, y, solution):
    if not x:
        return (yield solution)
    for r in [*min(x.values(), key=len)]:
        solution.append(r)
        cols = [*select(x, y, r)]
        yield from solve(x, y, solution)
        deselect(x, y, r, cols)
        solution.pop()


def select(x, y, r):
    for j in y[r]:
        [x[k].remove(i) for i in x[j] for k in y[i] if k != j]
        yield x.pop(j)


def deselect(x, y, r, cols):
    for j in reversed(y[r]):
        x[j] = cols.pop()
        [x[k].add(i) for i in x[j] for k in y[i] if k != j]
