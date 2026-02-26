import heapq
from typing import List, Tuple, Set, Optional, Dict
from collections import deque


# Các hằng số định nghĩa bản đồ
WALL = 1
FLOOR = 0
BOX = 2
GOAL = 3
PLAYER = 4
PLAYER_ON_GOAL = 5 # (Tuỳ chọn nếu nhân vật dẫm lên đích)
BOX_ON_GOAL = 6    # (Tuỳ chọn nếu hộp nằm trên đích)


class State:
    """Lớp đại diện cho một trạng thái trò chơi (vị trí người chơi + vị trí các hộp)"""
    def __init__(self, player_pos: Tuple[int, int], boxes_pos: Tuple[Tuple[int, int], ...]):
        self.player_pos = player_pos
        self.boxes_pos = boxes_pos  # Tuple của các vị trí hộp (để hashable)
    
    def __hash__(self):
        return hash((self.player_pos, self.boxes_pos))
    
    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        return self.player_pos == other.player_pos and self.boxes_pos == other.boxes_pos
    
    def __repr__(self):
        return f"State(player={self.player_pos}, boxes={self.boxes_pos})"


class AStarSolver:
    """Thuật toán A* để giải trò chơi Sokoban

    Deadlock detection has been split into static/deadlock and dynamic checks.
    Static positions are computed once based on the map layout; dynamic checks
    depend on the current state of boxes.
    """
    
    def __init__(self, grid: List[List[int]]):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if grid else 0
        self.walls = self._get_walls()
        self.goals = self._get_goals()
        
        # Hướng di chuyển: lên, xuống, trái, phải (cần dùng cho việc xác định deadlock cạnh)
        self.directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        # Precompute static deadlock positions on the map
        self.static_deadlocks = self._compute_static_deadlocks()

        # Precompute distances from every goal to all reachable floor cells
        # using BFS. This allows the heuristic to use true path distances
        # (ignoring other boxes) instead of simple Manhattan metrics.
        self.goal_distances = self._compute_goal_distances()
    
    def _get_walls(self) -> Set[Tuple[int, int]]:
        """Lấy tất cả vị trí tường"""
        walls = set()
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == WALL:
                    walls.add((r, c))
        return walls
    
    def _get_goals(self) -> Tuple[Tuple[int, int], ...]:
        """Lấy tất cả vị trí đích"""
        goals = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] in (GOAL, PLAYER_ON_GOAL, BOX_ON_GOAL):
                    goals.append((r, c))
        return tuple(sorted(goals))
    
    def _get_initial_state(self) -> State:
        """Lấy trạng thái ban đầu"""
        player_pos = None
        boxes = []
        
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] in (PLAYER, PLAYER_ON_GOAL):
                    player_pos = (r, c)
                elif self.grid[r][c] in (BOX, BOX_ON_GOAL):
                    boxes.append((r, c))
        
        return State(player_pos, tuple(sorted(boxes)))
    
    def _is_goal_state(self, state: State) -> bool:
        """Kiểm tra xem trạng thái có phải trạng thái thắng không"""
        # Tất cả hộp phải ở giữa các vị trí đích
        return sorted(state.boxes_pos) == sorted(self.goals)
    
    def _compute_static_deadlocks(self) -> Set[Tuple[int, int]]:
        """Xác định các vị trí tĩnh gây deadlock độc lập với hộp khác.
        Vị trí tĩnh ở đây là những ô không phải tường, không phải đích và
        nằm trong góc (hoặc mô thức tương tự) mà nếu một hộp được đặt vào đó
        thì trò chơi không thể thắng được.
        """
        deadlocks = set()
        for r in range(self.rows):
            for c in range(self.cols):
                pos = (r, c)
                if pos in self.walls or pos in self.goals:
                    continue
                # vị trí nằm trong góc gây deadlock
                if self._is_in_corner(pos):
                    deadlocks.add(pos)
                # vị trí nằm dọc theo bức tường nhưng không có đích phù hợp trên cùng một dòng/cột
                elif self._is_in_edge(pos):
                    deadlocks.add(pos)
        return deadlocks

    def _has_dynamic_deadlock(self, state: State) -> bool:
        """Kiểm tra deadlock động dựa trên vị trí hộp và các hộp khác.
        Logic cũ được giữ ở đây và chỉ áp dụng cho các trạng thái hộp cụ thể.
        """
        for box_pos in state.boxes_pos:
            if box_pos in self.goals:
                continue
            # corner dynamic check: vẫn giữ logic cũ
            if self._is_in_corner(box_pos):
                has_adjacent_goal = any(
                    (box_pos[0] + dr, box_pos[1] + dc) in self.goals 
                    for dr, dc in self.directions
                )
                if not has_adjacent_goal:
                    return True
            # edge deadlock: hộp nằm cạnh tường và không có đích trong cùng dòng/cột
            if self._is_in_edge(box_pos):
                return True
        # 2x2 block deadlock: any 2x2 square fully occupied by boxes without a goal
        if self._has_2x2_deadlock(state):
            return True
        # adjacent pair stuck against wall (conservative check)
        if self._has_adjacent_pair_deadlock(state):
            return True
        return False

    def _has_2x2_deadlock(self, state: State) -> bool:
        """Detect simple 2x2 box blocks (all four cells contain boxes) with no goal inside.

        This is a common dynamic deadlock pattern: a 2x2 square of boxes that cannot
        be moved if no goal lies within the square.
        """
        boxes = set(state.boxes_pos)
        for r in range(self.rows - 1):
            for c in range(self.cols - 1):
                square = {(r, c), (r+1, c), (r, c+1), (r+1, c+1)}
                if square.issubset(boxes):
                    # if any of the four is a goal, it's not a deadlock
                    if any(pos in self.goals for pos in square):
                        continue
                    return True
        return False

    def _has_adjacent_pair_deadlock(self, state: State) -> bool:
        """Conservative check for adjacent pair deadlocks against walls.

        If two boxes are adjacent horizontally and both have walls on the same
        side (above or below) and neither is on a goal, they're unlikely to be
        moved vertically; similarly for vertical adjacent pairs with walls on
        left or right. This is a conservative heuristic to prune obvious deadlocks.
        """
        boxes = set(state.boxes_pos)
        for (r, c) in state.boxes_pos:
            # horizontal neighbor
            right = (r, c+1)
            if right in boxes and (r, c) not in self.goals and right not in self.goals:
                above_blocked = (not self._is_valid_position((r-1, c))) and (not self._is_valid_position((r-1, c+1)))
                below_blocked = (not self._is_valid_position((r+1, c))) and (not self._is_valid_position((r+1, c+1)))
                if above_blocked or below_blocked:
                    return True
            # vertical neighbor
            down = (r+1, c)
            if down in boxes and (r, c) not in self.goals and down not in self.goals:
                left_blocked = (not self._is_valid_position((r, c-1))) and (not self._is_valid_position((r+1, c-1)))
                right_blocked = (not self._is_valid_position((r, c+1))) and (not self._is_valid_position((r+1, c+1)))
                if left_blocked or right_blocked:
                    return True
        return False

    def _is_deadlock(self, state: State) -> bool:
        """Kiểm tra cả deadlock tĩnh và động.
        Tĩnh: hộp nằm trên một vị trí vốn đã bị xác định deadlock trên bản đồ
        (bao gồm cả góc và cạnh không có đích).
        Động: hộp bị kẹt trong góc/vị trí không ra được do các hộp khác.
        """
        # kiểm tra tĩnh
        for box_pos in state.boxes_pos:
            if box_pos in self.goals:
                continue
            if box_pos in self.static_deadlocks:
                return True
        # kiểm tra động
        return self._has_dynamic_deadlock(state)
    
    def _compute_goal_distances(self) -> Dict[Tuple[int, int], Dict[Tuple[int, int], int]]:
        """
        Precompute BFS distances from each goal position to every reachable cell
        on the map (ignoring boxes). The returned dict maps a goal coordinate to a
        dict that maps any reachable position to its shortest path distance.
        """
        distances: Dict[Tuple[int, int], Dict[Tuple[int, int], int]] = {}
        for goal in self.goals:
            dist_map: Dict[Tuple[int, int], int] = {}
            queue = deque([(goal, 0)])
            visited = {goal}
            while queue:
                pos, d = queue.popleft()
                dist_map[pos] = d
                for dr, dc in self.directions:
                    nxt = (pos[0] + dr, pos[1] + dc)
                    if nxt in visited or not self._is_valid_position(nxt):
                        continue
                    visited.add(nxt)
                    queue.append((nxt, d + 1))
            distances[goal] = dist_map
        return distances

    # ---------------------------------------------------------------------
    # Minimum cost perfect matching utilities
    # ---------------------------------------------------------------------
    def _hungarian(self, cost_matrix: List[List[float]]) -> float:
        """Return the minimum cost of a perfect matching for a square cost_matrix.

        This is an implementation of the Hungarian algorithm (a.k.a. Kuhn–Munkres).
        The input matrix must be square; unreachable assignments are indicated by
        ``float('inf')``. The algorithm returns ``float('inf')`` if no perfect
        matching exists (i.e. some row is entirely ``inf`` or some column is
        entirely ``inf`` after reductions). Only the minimum cost is needed for
        the Sokoban heuristic, so we ignore the actual assignment.
        """
        n = len(cost_matrix)
        if n == 0:
            return 0.0

        # convert to 1-indexed for convenience
        u = [0.0] * (n + 1)
        v = [0.0] * (n + 1)
        p = [0] * (n + 1)
        way = [0] * (n + 1)

        for i in range(1, n + 1):
            p[0] = i
            j0 = 0
            minv = [float('inf')] * (n + 1)
            used = [False] * (n + 1)
            while True:
                used[j0] = True
                i0 = p[j0]
                delta = float('inf')
                j1 = 0
                for j in range(1, n + 1):
                    if not used[j]:
                        cur = cost_matrix[i0 - 1][j - 1] - u[i0] - v[j]
                        if cur < minv[j]:
                            minv[j] = cur
                            way[j] = j0
                        if minv[j] < delta:
                            delta = minv[j]
                            j1 = j
                if delta == float('inf'):
                    # no feasible assignment for row i0
                    return float('inf')
                for j in range(n + 1):
                    if used[j]:
                        u[p[j]] += delta
                        v[j] -= delta
                    else:
                        minv[j] -= delta
                j0 = j1
                if p[j0] == 0:
                    break
            # augmenting path
            while True:
                j1 = way[j0]
                p[j0] = p[j1]
                j0 = j1
                if j0 == 0:
                    break
        # optimal cost is -v[0]
        return -v[0]

    def _min_matching_cost(self, boxes: Tuple[Tuple[int, int], ...], goals: Tuple[Tuple[int, int], ...]) -> float:
        """
        Chi phí ghép cặp chính xác giữa hộp và mục tiêu sử dụng Hungarian
        algorithm. Thay vì đo khoảng cách Manhattan, ta dùng khoảng cách thực
        tế trên lưới (bỏ qua các hộp khác) lấy từ các bản đồ độ dài đường đi
        đã tiền tính.
        """
        n = len(boxes)
        if n == 0:
            return 0

        # Build cost matrix where cost[i][j] = distance from boxes[i] to goals[j]
        cost_matrix = [[float('inf')] * n for _ in range(n)]
        for i, box in enumerate(boxes):
            for j, goal in enumerate(goals):
                # Look up precomputed distance; if unreachable, it stays inf
                cost_matrix[i][j] = self.goal_distances.get(goal, {}).get(box, float('inf'))

        # Solve assignment problem using Hungarian algorithm helper defined below.
        # This is more efficient than the earlier DP bitmask approach and works for
        # larger numbers of boxes. If an entry in cost_matrix is ``inf`` it means
        # the goal is unreachable from that box; the Hungarian implementation will
        # ignore such assignments by leaving the final cost as ``inf`` if no
        # perfect matching exists.
        result = self._hungarian(cost_matrix)
        # if any box unreachable, result may stay inf; return large value to discourage
        return result if result != float('inf') else 1e6
    
    def _heuristic(self, state: State) -> float:
        """
        Hàm heuristic nâng cao cho Sokoban:
        - Sử dụng Hungarian heuristic: ghép cặp chính xác hộp với mục tiêu
          dựa trên khoảng cách đường đi thực tế (không phải Manhattan).
        - Tính chi phí tiếp cận từ player đến hộp gần nhất.
        - Xử phạt các hộp ở vị trí nguy hiểm (góc, cạnh, dán tường) để tránh
          deadlock sớm.
        """
        if not state.boxes_pos:
            return 0
        
        # 1. Chi phí ghép cặp hộp-mục tiêu (trọng số chính)
        matching_cost = self._min_matching_cost(state.boxes_pos, self.goals)
        
        # 2. Chi phí tiếp cận: khoảng cách từ player đến hộp gần nhất
        min_player_to_box = float('inf')
        for box in state.boxes_pos:
            dist = abs(state.player_pos[0] - box[0]) + abs(state.player_pos[1] - box[1])
            min_player_to_box = min(min_player_to_box, dist)
        
        if min_player_to_box == float('inf'):
            min_player_to_box = 0
        
        # 3. Xử phạt nhẹ cho các hộp ở vị trí khó tiếp cận (tránh deadlock tĩnh)
        penalty = 5  # Phạt cơ bản cho mỗi hộp ở vị trí nguy hiểm
        for box in state.boxes_pos:
            if box not in self.goals:
                # Kiểm tra xem hộp có ở góc không
                if self._is_in_corner(box):
                    penalty += 30  # Phạt góc (giảm từ 50)
                # vị trí dọc theo cạnh tường cũng nên bị phạt vì có nguy cơ deadlock
                elif self._is_in_edge(box):
                    penalty += 20  # phạt nặng hơn so với góc nhưng nhẹ hơn deadlock thực sự
                elif self._is_against_wall(box, state.boxes_pos):
                    penalty += 5   # Phạt dán tường (giảm từ 10)
        
        # Công thức: matching_cost + chi phí tiếp cận nhẹ + phạt nhẹ
        return matching_cost + (min_player_to_box * 1.5) + penalty
    
    def _is_in_corner(self, pos: Tuple[int, int]) -> bool:
        """Kiểm tra xem vị trí có ở góc (bị 2 tường bao quanh) không"""
        r, c = pos
        # Kiểm tra 4 góc
        corners = [
            # Góc trên-trái
            (not self._is_valid_position((r-1, c)) and not self._is_valid_position((r, c-1))),
            # Góc trên-phải
            (not self._is_valid_position((r-1, c)) and not self._is_valid_position((r, c+1))),
            # Góc dưới-trái
            (not self._is_valid_position((r+1, c)) and not self._is_valid_position((r, c-1))),
            # Góc dưới-phải
            (not self._is_valid_position((r+1, c)) and not self._is_valid_position((r, c+1)))
        ]
        return any(corners)

    def _is_in_edge(self, pos: Tuple[int, int]) -> bool:
        """Kiểm tra xem vị trí có nằm dọc theo một cạnh tường mà không có đích trên cùng một dòng/cột.

        Đây là deadlock tĩnh: nếu một hộp đẩy vào ô này thì nó chỉ có thể di chuyển dọc theo bức tường
        và nếu không có đích nằm trên đường di chuyển đó thì trò chơi sẽ chết.
        """
        r, c = pos
        # không xét tường hoặc đích
        if pos in self.walls or pos in self.goals:
            return False

        # phát hiện xem có đúng một bức tường liền kề (không phải góc)
        wall_dirs = []
        for dr, dc in self.directions:
            if not self._is_valid_position((r + dr, c + dc)):
                wall_dirs.append((dr, dc))
        # nếu là góc (2 tường) thì _is_in_corner đã bắt
        if len(wall_dirs) != 1:
            return False

        dr, dc = wall_dirs[0]
        # Nếu tường nằm trên/dưới thì hộp chỉ có thể trượt ngang
        # Ta kiểm tra đoạn liên thông (corridor) trên cùng một hàng xem có goal nào
        # nằm trong khoảng đi được (không bị tường chắn). Nếu có, thì không phải deadlock.
        if dr != 0:
            left = c
            while left - 1 >= 0 and self._is_valid_position((r, left - 1)):
                left -= 1
            right = c
            while right + 1 < self.cols and self._is_valid_position((r, right + 1)):
                right += 1
            for goal in self.goals:
                if goal[0] == r and left <= goal[1] <= right:
                    return False
            return True
        else:
            # Tường bên trái/phải -> hộp chỉ có thể trượt dọc theo cột
            top = r
            while top - 1 >= 0 and self._is_valid_position((top - 1, c)):
                top -= 1
            bottom = r
            while bottom + 1 < self.rows and self._is_valid_position((bottom + 1, c)):
                bottom += 1
            for goal in self.goals:
                if goal[1] == c and top <= goal[0] <= bottom:
                    return False
            return True
    
    def _is_against_wall(self, box_pos: Tuple[int, int], boxes: set) -> bool:
        """Trả về True nếu hộp bị kẹt bởi hai bức tường cạnh nhau (góc) hoặc các hộp khác.

        Đây là một kiểm tra đơn giản dùng trong heuristic để phạt các hộp nguy hiểm.
        (Không phải là kiểm tra deadlock tĩnh/dynamic chính thức.)
        """
        r, c = box_pos
        if box_pos in self.goals:
            return False
        
        # Đếm tường xung quanh
        wall_count = 0
        for dr, dc in self.directions:
            if not self._is_valid_position((r + dr, c + dc)):
                wall_count += 1
        
        # góc (hai tường) được xem rất nguy hiểm
        if wall_count >= 2:
            return True
        
        return False
    
    def _is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Kiểm tra vị trí có hợp lệ không (không phải tường, trong lưới)"""
        r, c = pos
        return (0 <= r < self.rows and 0 <= c < self.cols and 
                pos not in self.walls)
    
    def _get_neighbors(self, state: State) -> List[Tuple[State, str, list]]:
        """
        Lấy các trạng thái kế tiếp từ trạng thái hiện tại.
        Sử dụng flood-fill (player reachable) để chỉ sinh các hành động "đẩy" (push)
        nơi người chơi có thể tiếp cận phía sau hộp mà không cần sinh tất cả các
        trạng thái di chuyển của người chơi (giảm bùng nổ trạng thái).

        Trả về danh sách (state, action) trong đó action là "UP", "DOWN", "LEFT", "RIGHT"
        """
        neighbors: List[Tuple[State, str]] = []
        boxes_pos = set(state.boxes_pos)
        actions = ["UP", "DOWN", "LEFT", "RIGHT"]

        # Flood-fill để tìm tất cả ô mà người chơi có thể đi đến mà không đẩy hộp
        reachable = self._player_reachable(state.player_pos, boxes_pos)

        # Với mỗi hộp, kiểm tra 4 hướng: nếu ô phía sau hộp (player must stand)
        # nằm trong reachable và ô đẩy đến hợp lệ và rỗng thì ta có thể sinh push
        for box in state.boxes_pos:
            br, bc = box
            for direction_idx, (dr, dc) in enumerate(self.directions):
                player_needed = (br - dr, bc - dc)  # vị trí người chơi phải đứng để đẩy
                box_target = (br + dr, bc + dc)     # vị trí mới của hộp sau khi đẩy

                # player phải có thể đến vị trí đẩy, và vị trí đẩy phải hợp lệ
                if player_needed not in reachable:
                    continue
                if not self._is_valid_position(box_target):
                    continue
                # không có hộp khác ở ô đích
                if box_target in boxes_pos:
                    continue

                # Compute path for player to reach `player_needed` (sequence of UP/DOWN/LEFT/RIGHT)
                path_to_needed = self._player_path(state.player_pos, player_needed, boxes_pos)
                if path_to_needed is None:
                    continue

                # Tạo trạng thái mới: người chơi sẽ đứng tại vị trí hộp cũ sau khi đẩy
                new_boxes = boxes_pos - {box} | {box_target}
                new_state = State(box, tuple(sorted(new_boxes)))

                # Kiểm tra deadlock cho trạng thái sau khi đẩy
                if self._is_deadlock(new_state):
                    continue

                neighbors.append((new_state, actions[direction_idx], path_to_needed))

        return neighbors

    def _player_reachable(self, player_pos: Tuple[int, int], boxes_pos: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Trả về tập các ô mà người chơi có thể tới bằng flood-fill (không đẩy hộp)."""
        reachable: Set[Tuple[int, int]] = set()
        queue = deque([player_pos])
        reachable.add(player_pos)

        while queue:
            r, c = queue.popleft()
            for dr, dc in self.directions:
                nxt = (r + dr, c + dc)
                if nxt in reachable:
                    continue
                # phải là ô hợp lệ (không phải tường) và không có hộp chiếm chỗ
                if not self._is_valid_position(nxt):
                    continue
                if nxt in boxes_pos:
                    continue
                reachable.add(nxt)
                queue.append(nxt)

        return reachable

    def _player_path(self, player_pos: Tuple[int, int], target: Tuple[int, int], boxes_pos: Set[Tuple[int, int]]) -> Optional[list]:
        """Tính đường đi ngắn nhất (theo số bước) từ `player_pos` tới `target` tránh tường và hộp.
        Trả về danh sách các hành động trong `('UP','DOWN','LEFT','RIGHT')` hoặc None nếu không tới được.
        """
        if player_pos == target:
            return []

        prev: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {player_pos: None}
        queue = deque([player_pos])
        while queue:
            cur = queue.popleft()
            for dr, dc in self.directions:
                nxt = (cur[0] + dr, cur[1] + dc)
                if nxt in prev:
                    continue
                if not self._is_valid_position(nxt):
                    continue
                if nxt in boxes_pos:
                    continue
                prev[nxt] = cur
                if nxt == target:
                    # reconstruct path
                    path = []
                    node = target
                    while prev[node] is not None:
                        p = prev[node]
                        step = (node[0] - p[0], node[1] - p[1])
                        if step == (-1, 0):
                            path.append('UP')
                        elif step == (1, 0):
                            path.append('DOWN')
                        elif step == (0, -1):
                            path.append('LEFT')
                        elif step == (0, 1):
                            path.append('RIGHT')
                        node = p
                    return list(reversed(path))
                queue.append(nxt)
        return None
    
    def solve(self, max_steps: int = None) -> Optional[List[str]]:
        """
        Giải trò chơi Sokoban bằng thuật toán A* nâng cao
        Trả về danh sách các bước (UP, DOWN, LEFT, RIGHT) hoặc None nếu không có giải pháp
        
        Optimizations:
        - Heuristic function nâng cao (ghép cặp tối ưu hộp-mục tiêu)
        - Corner deadlock detection
        - A* search with g_score tracking
        - Dynamic max_steps dựa trên kích thước bản đồ
        """
        # Tính max_steps động dựa trên kích thước bản đồ
        if max_steps is None:
            map_size = self.rows * self.cols
            print(f"Map size: {map_size * 100}")
            max_steps = max(100000, map_size * 100)  # Tối thiểu 10000
        
        initial_state = self._get_initial_state()
        
        # Kiểm tra nếu trạng thái ban đầu đã là trạng thái winning
        if self._is_goal_state(initial_state):
            return []
        
        # Kiểm tra deadlock ban đầu (bao gồm các vị trí tĩnh)
        if self._is_deadlock(initial_state):
            print("Trạng thái ban đầu đã là deadlock!")
            return None
        
        # Open list: heap của (f_score, counter, state, path)
        # Counter để đảm bảo tính nhất quán khi f_score bằng nhau
        open_list = []
        counter = 0
        
        initial_g = 0
        initial_h = self._heuristic(initial_state)
        initial_f = initial_g + initial_h
        
        heapq.heappush(open_list, (initial_f, counter, initial_state, []))
        counter += 1
        
        # Closed list: tập hợp các trạng thái đã khám phá
        closed_set = set()
        
        # g_score: g_score[state] = chi phí tốt nhất để đến trạng thái đó
        g_score = {initial_state: initial_g}
        
        step = 0
        explored_states = 0
        
        while open_list:
            if step > max_steps:
                print(f"Đã vượt quá số bước tối đa ({max_steps}), dừng lại.")
                print(f"Đã tính toán {explored_states} trạng thái")
                return None
            
            step += 1
            
            if step % 1000 == 0:
                print(f"AI computing step {step}, explored {explored_states} states, open_list size: {len(open_list)}")
            
            f, _, current_state, path = heapq.heappop(open_list)
            
            # Nếu trạng thái hiện tại đã ở trong closed list, bỏ qua
            if current_state in closed_set:
                continue
            
            # Thêm trạng thái hiện tại vào closed list
            closed_set.add(current_state)
            explored_states += 1
            
            # Kiểm tra xem có phải trạng thái winning không
            if self._is_goal_state(current_state):
                print(f"\nĐã giải được sau {explored_states} lần khám phá")
                return path
            
            # Khám phá các trạng thái kế tiếp
            for next_state, action, walk_seq in self._get_neighbors(current_state):
                if next_state in closed_set:
                    continue

                # Tính g_score cho trạng thái kế tiếp (mỗi push có chi phí 1)
                tentative_g = g_score[current_state] + 1

                # Nếu tìm thấy đường đi tốt hơn
                if next_state not in g_score or tentative_g < g_score[next_state]:
                    g_score[next_state] = tentative_g
                    h = self._heuristic(next_state)
                    f = tentative_g + h

                    # Mở rộng path bằng các bước đi của người chơi trước khi đẩy,
                    # rồi thêm hành động đẩy hiện tại. `walk_seq` là danh sách các
                    # 'UP'/'DOWN'/'LEFT'/'RIGHT' để đi tới vị trí đẩy.
                    heapq.heappush(open_list, (f, counter, next_state, path + walk_seq + [action]))
                    counter += 1
        # Không tìm thấy giải pháp
        print(f"No solution found. Explored {explored_states} states")
        return None


def solve_sokoban(grid: List[List[int]]) -> Optional[List[str]]:
    """Hàm tiện ích để giải trò chơi Sokoban"""
    solver = AStarSolver(grid)
    return solver.solve()