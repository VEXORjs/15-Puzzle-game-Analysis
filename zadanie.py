import random
import time
import sys
import heapq

class Board:
    MOVE_MAP = {
        'L': lambda z, w, h: z-1 if z % w > 0 else None,
        'R': lambda z, w, h: z+1 if z % w < w-1 else None,
        'U': lambda z, w, h: z-w if z // w > 0 else None,
        'D': lambda z, w, h: z+w if z // w < h-1 else None
    }

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.size = width * height
        self.tiles = list(range(1, self.size)) + [0]
        self.goal = self.tiles.copy()
        self.zero_index = self.size - 1
        self.depth = 0
        self.neighbours_map = [self._compute_neighbours(i) for i in range(self.size)]

    def _compute_neighbours(self, index):
        neighbours = []
        row, col = divmod(index, self.width)
        if col > 0: neighbours.append(index - 1)
        if col < self.width - 1: neighbours.append(index + 1)
        if row > 0: neighbours.append(index - self.width)
        if row < self.height - 1: neighbours.append(index + self.width)
        return neighbours

    def swap(self, i, j):
        if self.tiles[i] == 0:
            self.zero_index = j
        elif self.tiles[j] == 0:
            self.zero_index = i
        self.tiles[i], self.tiles[j] = self.tiles[j], self.tiles[i]

    def load_from_list(self, tiles):
        if len(tiles) != self.size:
            raise ValueError("Wrong number of elements")
        if set(tiles) != set(range(self.size)):
            raise ValueError("Tiles must be 0..N unique")
        self.tiles = tiles.copy()
        self.zero_index = self.tiles.index(0)

    def randomise(self, itr=7, avoid_backtracking=True):
        self.depth = itr
        previous = None
        for _ in range(itr):
            zero = self.zero_index
            neighbours = self.neighbours_map[zero]
            if avoid_backtracking and previous is not None:
                neighbours = [n for n in neighbours if n != previous]
            move = random.choice(neighbours)
            previous = zero
            self.swap(zero, move)

    def is_solvable(self):
        inv_count = 0
        arr = [x for x in self.tiles if x != 0]
        for i in range(len(arr)):
            for j in range(i + 1, len(arr)):
                if arr[i] > arr[j]: inv_count += 1
        if self.width % 2 == 1:
            return inv_count % 2 == 0
        else:
            row_from_bottom = self.height - (self.zero_index // self.width)
            return (inv_count + row_from_bottom) % 2 == 1

    def hamming(self):
        distance = 0
        for i in range(self.size):
            if self.tiles[i] != self.zero_index and self.tiles[i] != self.goal[i]:
                distance += 1
        return distance

    def manhattan(self):
        distance = 0
        for i in range(self.size):
            value = self.tiles[i]
            if value != 0:
                row_now, col_now = value // self.width, value % self.width
                target_index = value - 1
                row_target, col_target = target_index // self.width, target_index % self.width

                distance += abs(row_now - row_target) + abs(col_now - col_target)
        return distance

    def is_complete(self):
        return self.tiles == self.goal

    def print_board(self):
        for i in range(self.size):
            if i % self.width == 0: print()
            print(f"{self.tiles[i]:2}", end=" ")
        print("\n")

    @classmethod
    def from_file(cls, filename):
        with open(filename, "r") as f:
            lines = f.read().splitlines()
        height, width = map(int, lines[0].split())
        tiles = []
        for line in lines[1:]:
            tiles.extend(map(int, line.split()))
        board = cls(width, height)
        board.load_from_list(tiles)
        return board

    @staticmethod
    def save_solution(filename, solution, depth):
        with open(filename, "w") as f:
            if solution is None:
                f.write("-1\n")
            else:
                f.write(f"{len(solution)}\n")
                f.write("".join(solution) + "\n")

    @staticmethod
    def save_stats(filename, depth, visited, processed, max_depth, time_ms):
        with open(filename, "w") as f:
            f.write(f"{depth}\n")
            f.write(f"{visited}\n")
            f.write(f"{processed}\n")
            f.write(f"{max_depth}\n")
            f.write(f"{time_ms}\n")

class A_star:
    def __init__(self, board, heuristic, move_order="LRUD"):
        self.visited_count = 0
        self.processed_count = 0
        self.max_reached_depth = 0
        self.width = board.width
        self.height = board.height
        self.start = board
        self.move_order = move_order
        self.heuristic = heuristic
        self.visited = {}
        self.best_solution = None
        self.best_depth = float('inf')

        if self.heuristic == "manh":
            self.h_func = lambda b: b.manhattan()
        else:
            self.h_func = lambda b: b.hamming()

    def solve(self):
        queue = []
        tie_breaker_og = 0

        start_time = time.time()

        heapq.heappush(queue, (0 + self.h_func(self.start), tie_breaker_og, self.start, 0, None, []))


        while queue:
            f_cost, tie_breaker, board, depth_, prev_zero, moves_seq = heapq.heappop(queue)
            self.max_reached_depth = max(self.max_reached_depth, depth_)
            state = bytes(board.tiles)

            if state in self.visited and self.visited[state] <= depth_:
                continue

            self.visited[state] = depth_
            self.visited_count += 1

            if board.is_complete() == 1:
                self.best_solution = moves_seq
                self.best_depth = depth_
                break

            zero = board.zero_index
            for move in self.move_order:
                n_index = Board.MOVE_MAP[move](zero, board.width, board.height)
                if n_index is None or n_index == prev_zero:
                    continue

                new_board = Board(board.width, board.height)
                new_board.load_from_list(board.tiles)
                new_board.swap(zero, n_index)

                tie_breaker_og += 1
                self.processed_count += 1
                heapq.heappush(queue, (depth_ + 1 + self.h_func(new_board), tie_breaker_og, new_board, depth_ + 1, zero, moves_seq + [move]))


        end_time = time.time()
        stats = {
            "visited": self.visited_count,
            "processed": self.processed_count,
            "max_depth": self.max_reached_depth,
            "time_ms": round((end_time - start_time) * 1000, 3)
        }

        if self.best_solution is None:
            return None, -1, stats
        return self.best_solution, self.best_depth, stats

class DFS:
    def __init__(self, board, move_order="LRUD", max_depth=50):
        self.start = board
        self.best_solution = None
        self.best_depth = float('inf')
        self.visited = {}
        self.move_order = move_order
        self.max_depth = max(max_depth, 20)
        self.visited_count = 0
        self.processed_count = 0
        self.max_reached_depth = 0

    def solve(self):
        if not self.start.is_solvable():
            print("Puzzle is NOT solvable")
            return None, -1, {}

        start_time = time.time()
        lifo = [(self.start, 0, None, [])]

        while lifo:
            board, depth, prev_zero, moves_seq = lifo.pop()
            self.max_reached_depth = max(self.max_reached_depth, depth)

            state = bytes(board.tiles)
            if state in self.visited and self.visited[state] <= depth:
                continue
            self.visited[state] = depth
            self.visited_count += 1

            if depth >= self.max_depth or depth >= self.best_depth:
                continue

            if board.is_complete():
                self.best_solution = moves_seq
                self.best_depth = depth
                continue

            zero = board.zero_index
            for move_char in self.move_order:
                n_index = Board.MOVE_MAP[move_char](zero, board.width, board.height)
                if n_index is None or n_index == prev_zero:
                    continue

                new_board = Board(board.width, board.height)
                new_board.load_from_list(board.tiles)
                new_board.swap(zero, n_index)

                lifo.append((new_board, depth + 1, zero, moves_seq + [move_char]))
                self.processed_count += 1

        end_time = time.time()
        stats = {
            "visited": self.visited_count,
            "processed": self.processed_count,
            "max_depth": self.max_reached_depth,
            "time_ms": round((end_time - start_time) * 1000, 3)
        }

        if self.best_solution is None:
            return None, -1, stats
        return self.best_solution, self.best_depth, stats

from collections import deque

class BFS:
    def __init__(self, board, move_order="LRUD"):
        self.start = board
        self.visited = {}
        self.move_order = move_order
        self.visited_count = 0
        self.processed_count = 0
        self.max_reached_depth = 0
        self.best_solution = None
        self.best_depth = float('inf')

    def solve(self):
        if not self.start.is_solvable():
            print("Puzzle is NOT solvable")
            return None, -1, {}

        start_time = time.time()

        fifo = deque()
        fifo.append((self.start, 0, None, []))

        while fifo:
            board, depth, prev_zero, moves_seq = fifo.popleft()
            self.max_reached_depth = max(self.max_reached_depth, depth)

            state = bytes(board.tiles)
            if state in self.visited and self.visited[state] <= depth:
                continue
            self.visited[state] = depth
            self.visited_count += 1

            if board.is_complete():
                self.best_solution = moves_seq
                self.best_depth = depth
                break

            zero = board.zero_index
            for move_char in self.move_order:
                n_index = Board.MOVE_MAP[move_char](zero, board.width, board.height)
                if n_index is None or n_index == prev_zero:
                    continue

                new_board = Board(board.width, board.height)
                new_board.load_from_list(board.tiles)
                new_board.swap(zero, n_index)

                fifo.append((new_board, depth + 1, zero, moves_seq + [move_char]))
                self.processed_count += 1

        end_time = time.time()
        stats = {
            "visited": self.visited_count,
            "processed": self.processed_count,
            "max_depth": self.max_reached_depth,
            "time_ms": round((end_time - start_time) * 1000, 3)
        }

        if self.best_solution is None:
            return None, -1, stats
        return self.best_solution, self.best_depth, stats



if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: program strategy <move_order/heuristics> <input_file> <solution_file> <stats_file>")
        exit(1)

    strategy = sys.argv[1]
    param = sys.argv[2]
    input_file = sys.argv[3]
    sol_file = sys.argv[4]
    stats_file = sys.argv[5]

    try:
        board = Board.from_file(input_file)
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
        exit(1)

    if strategy == "dfs":
        solver = DFS(board, move_order=param, max_depth=20)
        solution, depth_, stats_ = solver.solve()
    elif strategy == "bfs":
        solver = BFS(board, move_order=param)
        solution, depth_, stats_ = solver.solve()
    elif strategy == "astr":
        solver = A_star(board, heuristic=param)
        solution, depth_, stats_ = solver.solve()
    else:
        print(f"Unknown strategy: {strategy}")
        exit(1)

    Board.save_solution(sol_file, solution, depth_)
    Board.save_stats(
        stats_file,
        depth_,
        stats_['visited'],
        stats_['processed'],
        stats_['max_depth'],
        stats_['time_ms']
    )