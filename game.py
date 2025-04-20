import random

class MinesweeperGame:
    def __init__(self, width, height, mines):
        if not (0 < width <= 30 and 0 < height <= 30): # 添加尺寸限制
             raise ValueError("棋盘尺寸必须在 1 到 30 之间。")
        if not (0 < mines < width * height):
            raise ValueError("无效的雷数。")

        self.width = width
        self.height = height
        self.mines_count = mines
        self.board = [[' ' for _ in range(width)] for _ in range(height)]
        self.mine_locations = set()
        self.revealed = [[False for _ in range(width)] for _ in range(height)]
        self.flagged = [[False for _ in range(width)] for _ in range(height)]
        self.first_click = True
        self.game_over = False
        self.won = False
        self.lost_mine_location = None # 记录哪个雷被踩中了

    def _is_valid(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def _get_neighbors(self, x, y):
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if self._is_valid(nx, ny):
                    neighbors.append((nx, ny))
        return neighbors

    def _place_mines(self, start_x, start_y):
        possible_locations = []
        for r in range(self.height):
            for c in range(self.width):
                # 排除首次点击的位置及其直接相邻的位置
                if abs(r - start_y) > 1 or abs(c - start_x) > 1:
                     possible_locations.append((c, r))

        if len(possible_locations) < self.mines_count:
             # 如果棋盘太小无法满足排除规则，则使用备用方案
             possible_locations = [(c, r) for r in range(self.height) for c in range(self.width) if (c, r) != (start_x, start_y)]
             if len(possible_locations) < self.mines_count:
                 raise ValueError("无法在给定约束条件下放置地雷。") # 尺寸检查后应该不会发生

        self.mine_locations = set(random.sample(possible_locations, self.mines_count))

        for r in range(self.height):
            for c in range(self.width):
                if (c, r) in self.mine_locations:
                    self.board[r][c] = '*'
                    continue
                count = 0
                for nx, ny in self._get_neighbors(c, r):
                    if (nx, ny) in self.mine_locations:
                        count += 1
                if count > 0:
                    self.board[r][c] = str(count)

    def reveal_cell(self, x, y):
        if not self._is_valid(x, y) or self.revealed[y][x] or self.flagged[y][x] or self.game_over:
            return False # 表示无变化或无效移动

        if self.first_click:
            self._place_mines(x, y)
            self.first_click = False

        self.revealed[y][x] = True

        if self.board[y][x] == '*':
            self.game_over = True
            self.won = False
            self.lost_mine_location = (x, y)
            # 揭开所有地雷
            for mx, my in self.mine_locations:
                if not self.flagged[my][mx]:
                    self.revealed[my][mx] = True
            return True # 表示有变化

        if self.board[y][x] == ' ':
            # 对空单元格进行填充
            queue = [(x, y)]
            visited = set([(x, y)])
            while queue:
                curr_x, curr_y = queue.pop(0)
                for nx, ny in self._get_neighbors(curr_x, curr_y):
                    if (nx, ny) not in visited and not self.revealed[ny][nx] and not self.flagged[ny][nx]:
                        self.revealed[ny][nx] = True
                        visited.add((nx, ny))
                        if self.board[ny][nx] == ' ':
                            queue.append((nx, ny))

        self._check_win()
        return True # 表示有变化

    def flag_cell(self, x, y):
        if not self._is_valid(x, y) or self.revealed[y][x] or self.game_over:
            return False # 表示无变化或无效移动

        self.flagged[y][x] = not self.flagged[y][x]
        self._check_win() # 插旗/取消插旗后检查胜利条件
        return True # 表示有变化

    def _check_win(self):
        if self.game_over:
            return
        revealed_count = 0
        correctly_flagged_mines = 0
        for r in range(self.height):
            for c in range(self.width):
                if self.revealed[r][c] and (c, r) not in self.mine_locations:
                    revealed_count += 1
                if self.flagged[r][c] and (c, r) in self.mine_locations:
                     correctly_flagged_mines += 1

        # 胜利条件 1: 所有非雷单元格都已揭开
        if revealed_count == self.width * self.height - self.mines_count:
            self.game_over = True
            self.won = True
            # 自动标记剩余的地雷
            for mx, my in self.mine_locations:
                if not self.flagged[my][mx]:
                    self.flagged[my][mx] = True

        # 胜利条件 2: 所有地雷都被正确标记 (可选，但常见)
        # 注意: 如果严格执行，这可能与主要的胜利条件冲突。
        # 坚持标准的“所有非雷单元格都已揭开”条件。
        # if correctly_flagged_mines == self.mines_count and \
        #    sum(row.count(True) for row in self.flagged) == self.mines_count:
        #     self.game_over = True
        #     self.won = True


    def get_state(self):
        """返回渲染所需的必要状态。"""
        return {
            "width": self.width,
            "height": self.height,
            "board": self.board,
            "revealed": self.revealed,
            "flagged": self.flagged,
            "game_over": self.game_over,
            "won": self.won,
            "mine_locations": self.mine_locations, # 失败时需要揭开地雷
            "lost_mine_location": self.lost_mine_location
        }
