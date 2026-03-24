import random

from pandas.core.roperator import rand_

class Node:
    def __init__(self, number):
        self.number = number
        self.neighbours = []

    def __repr__(self):
        return f"({self.number})"

    def add_neighbour(self, new_neighbour):
        if new_neighbour not in self.neighbours:
            self.neighbours.append(new_neighbour)
        if self not in new_neighbour.neighbours:
            new_neighbour.neighbours.append(self)

    def remove_neighbor(self, neighbour):
        if neighbour in self.neighbours:
            self.neighbours.remove(neighbour)
            neighbour.remove_neighbor(self)

    def node_swap(self, other_node):
        if other_node in self.neighbours:
            self.number, other_node.number = other_node.number, self.number

    def get_neighbours(self):
        return self.neighbours

    def get_number(self):
        return self.number

    def set_number(self, new_number):
        self.number = new_number
        return self.number

class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.nodes = []

        self.depth = 0

        size = width * height

        for i in range(size):
            if i == size-1:
                self.nodes.append(Node(0))
            else:
                self.nodes.append(Node(i+1))

        for i in range(size):
            row = i // width
            col = i % width

            if col > 0:
                self.nodes[i].add_neighbour(self.nodes[i - 1])

            if col < width - 1:
                self.nodes[i].add_neighbour(self.nodes[i + 1])

            if row > 0:
                self.nodes[i].add_neighbour(self.nodes[i - width])

            if row < height - 1:
                self.nodes[i].add_neighbour(self.nodes[i + width])

    def copy(self):
        new_board = Board(self.width, self.height)
        for i in range(len(self.nodes)):
            new_board.nodes[i].set_number(self.nodes[i].get_number())
        return new_board

    def is_complete(self):
        expected = list(range(1, self.width * self.height)) + [0]
        current = [node.get_number() for node in self.nodes]
        return current == expected

    def find_zero(self):
        for i in range(len(self.nodes)):
            if self.nodes[i].get_number() == 0:
                return i
        return -1

    def randomise(self, itr=7, repeat_flag=0):
        self.depth = itr

        previous_index = None

        for _ in range(itr):
            zero_index = self.find_zero()
            zero_node = self.nodes[zero_index]

            neighbours = zero_node.get_neighbours()

            neighbour_indices = [self.nodes.index(n) for n in neighbours]

            if repeat_flag and previous_index is not None:
                neighbour_indices = [i for i in neighbour_indices if i != previous_index]

            random_index = random.choice(neighbour_indices)

            previous_index = zero_index

            self.nodes[zero_index].node_swap(self.nodes[random_index])

    def get_nodes(self):
        return self.nodes

    def print_nodes(self):
        size = len(self.nodes)
        mark = ""

        for i in range(size):
            if i % self.width == 0:
                print()

            if self.nodes[i].get_number() <= 9:
                mark = " "
            print(mark, self.nodes[i].get_number(), end=" ")
            mark = ""
        print("\n\n")

    def print_edges(self):
        size = len(self.nodes)

        for i in range(size):
            print(self.nodes[i].get_number(), " : ", self.nodes[i].get_neighbours(), end="\n")

    def get_state(self):
        return tuple(node.get_number() for node in self.nodes)

    def get_depth(self):
        return self.depth


class DFS:
    def __init__(self, board):
        self.start_board = board
        self.visited = {}
        self.iterations = 0
        self.best_solution = None
        self.best_depth = float('inf')

    def solve(self):
        max_depth = self.start_board.get_depth()
        self._dfs(self.start_board, depth_=0, max_depth=max_depth)
        print("Iterations:", self.iterations)
        return self.best_solution, self.best_depth if self.best_solution else None

    def _dfs(self, board, depth_=0, max_depth=7):
        self.iterations += 1

        state = board.get_state()

        if state in self.visited and self.visited[state] <= depth_:
            return
        self.visited[state] = depth_

        if depth_ > max_depth:
            return

        if depth_ >= self.best_depth:
            return

        if board.is_complete():
            print(depth_)
            if depth_ < self.best_depth:
                self.best_solution = board.copy()
                self.best_depth = depth_
            return

        zero_index = board.find_zero()
        zero_node = board.nodes[zero_index]

        for neighbour in zero_node.get_neighbours():
            neighbour_index = board.nodes.index(neighbour)

            board.nodes[zero_index].node_swap(board.nodes[neighbour_index])

            self._dfs(board, depth_ + 1, max_depth)

            board.nodes[zero_index].node_swap(board.nodes[neighbour_index])

b = Board(4,4)
b.print_nodes()

b.randomise(itr=7,repeat_flag=0)

b.print_nodes()

solver = DFS(b)
result, depth = solver.solve()

result.print_nodes()
print(depth)