import heapq
from typing import List, Tuple, Set, Optional


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
    """Thuật toán A* để giải trò chơi Sokoban"""
    
    def __init__(self, grid: List[List[int]]):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if grid else 0
        self.walls = self._get_walls()
        self.goals = self._get_goals()
        
        # Hướng di chuyển: lên, xuống, trái, phải
        self.directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
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
                if self.grid[r][c] == GOAL:
                    goals.append((r, c))
        return tuple(sorted(goals))
    
    def _get_initial_state(self) -> State:
        """Lấy trạng thái ban đầu"""
        player_pos = None
        boxes = []
        
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == PLAYER:
                    player_pos = (r, c)
                elif self.grid[r][c] == BOX:
                    boxes.append((r, c))
        
        return State(player_pos, tuple(sorted(boxes)))
    
    def _is_goal_state(self, state: State) -> bool:
        """Kiểm tra xem trạng thái có phải trạng thái thắng không"""
        # Tất cả hộp phải ở giữa các vị trí đích
        return sorted(state.boxes_pos) == sorted(self.goals)
    
    def _is_deadlock(self, state: State) -> bool:
        """
        Kiểm tra xem trạng thái có deadlock không
        Deadlock xảy ra khi hộp bị mắc kẹt ở góc không có đích
        """
        
        # Kiểm tra mỗi hộp
        for box_pos in state.boxes_pos:
            # Nếu hộp đã ở trên đích, không phải deadlock
            if box_pos in self.goals:
                continue
            
            # Kiểm tra Corner Deadlock: hộp ở góc mà không thể đẩy ra
            if self._is_in_corner(box_pos):
                # Góc không có goal lân cận = deadlock chắc chắn
                has_adjacent_goal = any(
                    (box_pos[0] + dr, box_pos[1] + dc) in self.goals 
                    for dr, dc in self.directions
                )
                if not has_adjacent_goal:
                    return True
        
        return False
    
    def _min_matching_cost(self, boxes: Tuple[Tuple[int, int], ...], goals: Tuple[Tuple[int, int], ...]) -> float:
        """
        Tính chi phí ghép cặp tối ưu giữa hộp và mục tiêu
        Sử dụng Hungarian algorithm approximation (greedy matching)
        """
        if not boxes:
            return 0
        
        total_cost = 0
        used_goals = set()
        
        # Sorted boxes để có kết quả nhất quán
        for box in sorted(boxes):
            min_distance = float('inf')
            best_goal = None
            
            for i, goal in enumerate(sorted(goals)):
                if i in used_goals:
                    continue
                
                distance = abs(box[0] - goal[0]) + abs(box[1] - goal[1])
                if distance < min_distance:
                    min_distance = distance
                    best_goal = i
            
            if best_goal is not None:
                used_goals.add(best_goal)
                total_cost += min_distance
        
        return total_cost
    
    def _heuristic(self, state: State) -> float:
        """
        Hàm heuristic nâng cao cho Sokoban:
        - Ghép cặp tối ưu hộp với mục tiêu
        - Tính chi phí tiếp cận từ player
        - Xử phạt các hộp ở vị trí nguy hiểm
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
        
        # 3. Xử phạt nhẹ cho các hộp ở vị trí khó tiếp cận (tránh deadlock)
        penalty = 0
        for box in state.boxes_pos:
            if box not in self.goals:
                # Kiểm tra xem hộp có ở góc không
                if self._is_in_corner(box):
                    penalty += 30  # Phạt góc (giảm từ 50)
                elif self._is_against_wall(box, state.boxes_pos):
                    penalty += 5   # Phạt dán tường (giảm từ 10)
        
        # Công thức: matching_cost + chi phí tiếp cận nhẹ + phạt nhẹ
        return matching_cost + (min_player_to_box * 0.3) + penalty
    
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
    
    def _is_against_wall(self, box_pos: Tuple[int, int], boxes: set) -> bool:
        """Kiểm tra xem hộp có dán tường mà không có đích gần không"""
        r, c = box_pos
        if box_pos in self.goals:
            return False
        
        # Đếm tường xung quanh
        wall_count = 0
        for dr, dc in self.directions:
            if not self._is_valid_position((r + dr, c + dc)):
                wall_count += 1
        
        # Nếu có 2 tường liên tiếp (góc) = rất nguy hiểm
        if wall_count >= 2:
            return True
        
        return False
    
    def _is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Kiểm tra vị trí có hợp lệ không (không phải tường, trong lưới)"""
        r, c = pos
        return (0 <= r < self.rows and 0 <= c < self.cols and 
                pos not in self.walls)
    
    def _get_neighbors(self, state: State) -> List[Tuple[State, str]]:
        """
        Lấy các trạng thái kế tiếp từ trạng thái hiện tại
        Trả về danh sách (state, action) trong đó action là "UP", "DOWN", "LEFT", "RIGHT"
        """
        neighbors = []
        player_r, player_c = state.player_pos
        boxes_pos = set(state.boxes_pos)
        actions = ["UP", "DOWN", "LEFT", "RIGHT"]
        
        for direction_idx, (dr, dc) in enumerate(self.directions):
            new_player_r = player_r + dr
            new_player_c = player_c + dc
            new_pos = (new_player_r, new_player_c)
            
            # Kiểm tra vị trí mới có hợp lệ không
            if not self._is_valid_position(new_pos):
                continue
            
            # Nếu không có hộp tại vị trí mới, người chơi chỉ cần di chuyển
            if new_pos not in boxes_pos:
                new_state = State(new_pos, state.boxes_pos)
                neighbors.append((new_state, actions[direction_idx]))
            else:
                # Có hộp tại vị trí mới, kiểm tra xem có thể đẩy hộp không
                box_r = new_player_r + dr
                box_c = new_player_c + dc
                box_new_pos = (box_r, box_c)
                
                # Kiểm tra vị trí hộp mới có hợp lệ không
                if not self._is_valid_position(box_new_pos):
                    continue
                
                # Có hộp khác tại vị trí mới của hộp
                if box_new_pos in boxes_pos:
                    continue
                
                # Có thể đẩy hộp
                new_boxes = boxes_pos - {new_pos} | {box_new_pos}
                new_state = State(new_pos, tuple(sorted(new_boxes)))
                
                # Kiểm tra deadlock: nếu tạo ra deadlock, không thêm vào neighbors
                if not self._is_deadlock(new_state):
                    neighbors.append((new_state, actions[direction_idx]))
        
        return neighbors
    
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
        
        # Kiểm tra deadlock ban đầu
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
                print(f"AI đang tính lần thứ {step}, đã khám phá {explored_states} trạng thái, open_list size: {len(open_list)}")
            
            f, _, current_state, path = heapq.heappop(open_list)
            
            # Nếu trạng thái hiện tại đã ở trong closed list, bỏ qua
            if current_state in closed_set:
                continue
            
            # Thêm trạng thái hiện tại vào closed list
            closed_set.add(current_state)
            explored_states += 1
            
            # Kiểm tra xem có phải trạng thái winning không
            if self._is_goal_state(current_state):
                print(f"\n✓ Tìm thấy giải pháp sau {explored_states} trạng thái khám phá")
                print(f"Số bước: {len(path)}")
                return path
            
            # Khám phá các trạng thái kế tiếp
            for next_state, action in self._get_neighbors(current_state):
                if next_state in closed_set:
                    continue
                
                # Tính g_score cho trạng thái kế tiếp
                tentative_g = g_score[current_state] + 1
                
                # Nếu tìm thấy đường đi tốt hơn
                if next_state not in g_score or tentative_g < g_score[next_state]:
                    g_score[next_state] = tentative_g
                    h = self._heuristic(next_state)
                    f = tentative_g + h
                    
                    heapq.heappush(open_list, (f, counter, next_state, path + [action]))
                    counter += 1
        # Không tìm thấy giải pháp
        print(f"✗ Không tìm thấy giải pháp. Đã khám phá {explored_states} trạng thái")
        return None


def solve_sokoban(grid: List[List[int]]) -> Optional[List[str]]:
    """Hàm tiện ích để giải trò chơi Sokoban"""
    solver = AStarSolver(grid)
    return solver.solve()