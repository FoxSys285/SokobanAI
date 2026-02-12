import heapq

# A* + Manhattan

class State:
    def __init__(self, player_pos, boxes_pos, cost, parent=None, action=None):
        self.player_pos = player_pos
        self.boxes_pos = frozenset(boxes_pos)
        self.cost = cost # Số bước g(n)
        self.parent = parent
        self.action = action # Lưu hướng đi (L, R, U, D) để game thực thi
        self.heuristic = 0 # h(n)

    def __lt__(self, other):
        # Trả về f(n) = g(n) + h(n) (MIN)
        return (self.cost + self.heuristic) < (other.cost + other.heuristic)

    def __hash__(self):
        return hash((self.player_pos, self.boxes_pos))

    def __eq__(self, other):
        return self.player_pos == other.player_pos and self.boxes_pos == other.boxes_pos




# Minimum Cost Perfect Matching
def get_heuristic(player_pos, boxes_pos, goals):
    if not boxes_pos:
        return 0
    
    boxes = list(boxes_pos)
    targets = list(goals)
    total_h = 0

    # 1. Tính toán Min-Cost Matching (Greedy Approximation nhưng chính xác hơn)
    # Chúng ta tìm cặp Hộp-Đích có khoảng cách ngắn nhất, kết nối chúng, rồi tiếp tục.
    temp_boxes = boxes[:]
    temp_targets = targets[:]
    
    weight = 2.0
    penalty = 20
    
    while temp_boxes:
        min_dist = float('inf')
        best_box_idx = -1
        best_target_idx = -1
        
        for i, box in enumerate(temp_boxes):
            for j, target in enumerate(temp_targets):
                # Manhattan distance
                d = abs(box[0] - target[0]) + abs(box[1] - target[1])
                if d < min_dist:
                    min_dist = d
                    best_box_idx = i
                    best_target_idx = j
        
        # Phạt nặng nếu hộp chưa vào đích để khuyến khích AI ưu tiên hoàn thành từng hộp
        # Nếu hộp đã ở đích, d sẽ bằng 0.
        total_h += min_dist
        if min_dist > 0:
            total_h += penalty # Trọng số phạt (Penalty weight)
            
        temp_boxes.pop(best_box_idx)
        temp_targets.pop(best_target_idx)

    # 2. Khoảng cách từ người chơi đến cái hộp gần nhất
    # AI cần phải chạy lại gần hộp thì mới đẩy được.
    min_p_dist = min(abs(player_pos[0] - b[0]) + abs(player_pos[1] - b[1]) for b in boxes)
    
    # Heuristic tổng hợp: (Khoảng cách Hộp->Đích * Hệ số ưu tiên) + Khoảng cách Người->Hộp
    return (total_h * weight) + (min_p_dist)

def get_static_deadlocks(board, goals):
    rows = len(board)
    cols = len(board[0])
    deadlocks = set()
    goals_set = set(goals)

    for y in range(rows):
        for x in range(cols):
            if board[y][x] == 1 or (x, y) in goals_set:
                continue
            
            # Kiểm tra biên an toàn
            up    = board[y-1][x] == 1 if y > 0 else True
            down  = board[y+1][x] == 1 if y < rows - 1 else True
            left  = board[y][x-1] == 1 if x > 0 else True
            right = board[y][x+1] == 1 if x < cols - 1 else True
            
            # 1. Corner Deadlock
            if (up and left) or (up and right) or (down and left) or (down and right):
                deadlocks.add((x, y))
                continue

            # 2. Line Deadlock
            if up or down:
                if not has_goal_on_wall_segment(x, y, board, goals_set, horizontal=True):
                    deadlocks.add((x, y))
            elif left or right:
                if not has_goal_on_wall_segment(x, y, board, goals_set, horizontal=False):
                    deadlocks.add((x, y))
                    
    return deadlocks

def has_goal_on_wall_segment(x, y, board, goals, horizontal=True):
    """Kiểm tra dọc theo bức tường xem có ô đích nào không."""
    rows = len(board)
    cols = len(board[0])
    
    if horizontal:
        for direction in [-1, 1]:
            curr_x = x
            while True:
                curr_x += direction
                # Kiểm tra biên trước khi truy cập mảng
                if not (0 <= curr_x < cols): 
                    break 
                if board[y][curr_x] == 1: 
                    break # Chạm tường vuông góc
                if (curr_x, y) in goals: 
                    return True
                # Nếu bỗng nhiên mất tường song song (trên và dưới) thì đây là lối thoát
                has_wall_above = (y > 0 and board[y-1][curr_x] == 1)
                has_wall_below = (y < rows - 1 and board[y+1][curr_x] == 1)
                if not has_wall_above and not has_wall_below:
                    return True
    else:
        for direction in [-1, 1]:
            curr_y = y
            while True:
                curr_y += direction
                # Kiểm tra biên trước khi truy cập mảng
                if not (0 <= curr_y < rows): 
                    break
                if board[curr_y][x] == 1: 
                    break
                if (x, curr_y) in goals: 
                    return True
                # Nếu bỗng nhiên mất tường song song (trái và phải) thì đây là lối thoát
                has_wall_left = (x > 0 and board[curr_y][x-1] == 1)
                has_wall_right = (x < cols - 1 and board[curr_y][x+1] == 1)
                if not has_wall_left and not has_wall_right:
                    return True
    return False

def is_dynamic_deadlock(bx, by, board, boxes, goals):
    # Kiểm tra vùng 2x2 xung quanh hộp vừa đẩy
    for dx, dy in [(-1, -1), (-1, 0), (0, -1), (0, 0)]:
        count = 0
        for i in range(2):
            for j in range(2):
                nx, ny = bx + dx + i, by + dy + j
                # Nếu là tường hoặc là một cái hộp khác
                if board[ny][nx] == 1 or (nx, ny) in boxes:
                    # Nhưng nếu ô này là đích thì không phải deadlock
                    if (nx, ny) in goals:
                        break
                    count += 1
                else:
                    break
            else: 
                continue
            break
        if count == 4: 
            return True
    return False

def is_square_deadlock(bx, by, board, boxes, goals):
    """
    Kiểm tra xem hộp tại vị trí (bx, by) có tạo thành bế tắc 2x2 không.
    bx, by: tọa độ x, y của hộp vừa được đẩy đến.
    """
    # Duyệt qua 4 khả năng mà (bx, by) có thể là một góc của khối 2x2
    # (trên-trái, trên-phải, dưới-trái, dưới-phải)
    for dx, dy in [(-1, -1), (-1, 0), (0, -1), (0, 0)]:
        is_deadlock = True
        
        # Kiểm tra từng ô trong khối 2x2 bắt đầu từ tọa độ (bx+dx, by+dy)
        for i in range(2):
            for j in range(2):
                nx, ny = bx + dx + i, by + dy + j
                
                # Nếu ô nằm ngoài biên hoặc là ô trống (không phải tường/hộp)
                # hoặc nếu ô đó là ĐÍCH -> Không phải bế tắc hình vuông
                if (nx, ny) in goals or (board[ny][nx] != 1 and (nx, ny) not in boxes):
                    is_deadlock = False
                    break
            if not is_deadlock:
                break
        
        if is_deadlock:
            return True
            
    return False

def is_tunnel_deadlock(bx, by, board, goals):
    """
    Kiểm tra xem hộp có bị đẩy vào hành lang mà không có lối thoát hoặc không có đích không.
    """
    # Nếu ngay tại vị trí này là đích, không phải deadlock
    if (bx, by) in goals:
        return False

    rows = len(board)
    cols = len(board[0])

    # Kiểm tra hành lang theo chiều ngang (Trái - Phải)
    # Điều kiện: Trên và Dưới là tường
    if (by > 0 and board[by-1][bx] == 1) and (by < rows - 1 and board[by+1][bx] == 1):
        # Kiểm tra hai phía của hành lang xem có ô đích nào không
        for direction in [-1, 1]:
            curr_x = bx + direction
            while 0 <= curr_x < cols and board[by][curr_x] != 1:
                if (curr_x, by) in goals:
                    return False # Có đích trong hành lang hoặc ở lối ra
                # Nếu bỗng nhiên mất tường song song thì đây là lối thoát (hết hành lang)
                if not (board[by-1][curr_x] == 1 and board[by+1][curr_x] == 1):
                    return False
                curr_x += direction
        return True # Hành lang kín, không có đích -> Deadlock

    # Kiểm tra hành lang theo chiều dọc (Trên - Dưới)
    # Điều kiện: Trái và Phải là tường
    if (bx > 0 and board[by][bx-1] == 1) and (bx < cols - 1 and board[by][bx+1] == 1):
        for direction in [-1, 1]:
            curr_y = by + direction
            while 0 <= curr_y < rows and board[curr_y][bx] != 1:
                if (bx, curr_y) in goals:
                    return False
                if not (board[curr_y][bx-1] == 1 and board[curr_y][bx+1] == 1):
                    return False
                curr_y += direction
        return True

    return False

def solve_sokoban(start_player, start_boxes, goals, board, limit=300000):
    iterations = 0
    goals_set = frozenset(goals)
    
    start_boxes = frozenset(start_boxes)
    goals_set = frozenset(goals)
    
    # TÍNH TOÁN DEADLOCK TĨNH TRƯỚC KHI CHẠY A*
    static_deadlocks = get_static_deadlocks(board, goals_set)
    
    # Khởi tạo trạng thái đầu
    start_state = State(start_player, start_boxes, 0)
    start_state.heuristic = get_heuristic(start_player, start_boxes, goals_set)
    
    open_list = [start_state]
    closed_list = {} 
    closed_list[(start_state.player_pos, start_state.boxes_pos)] = 0
    visited_states = {hash((start_player, start_boxes)): 0}

    rows = len(board)
    cols = len(board[0]) 

    while open_list:
        current = heapq.heappop(open_list)
        iterations += 1

        if iterations > limit: 
            return None
        if current.boxes_pos == goals_set: 
            return get_actions(current)

        if len(visited_states) > limit:
            return None

        x, y = current.player_pos
        for dx, dy, move in [(0, -1, 'U'), (0, 1, 'D'), (-1, 0, 'L'), (1, 0, 'R')]:
            nx, ny = x + dx, y + dy
            
            if 0 <= nx < cols and 0 <= ny < rows and board[ny][nx] != 1:
                new_boxes = set(current.boxes_pos)
                if (nx, ny) in new_boxes:
                    bx, by = nx + dx, ny + dy
                    if 0 <= bx < cols and 0 <= by < rows and board[by][bx] != 1 and (bx, by) not in new_boxes:
                        if (bx, by)  in static_deadlocks:
                            continue
                        
                        temp_boxes = set(new_boxes)
                        temp_boxes.remove((nx, ny))
                        temp_boxes.add((bx, by))
                        
                        if is_dynamic_deadlock(bx, by, board, temp_boxes, goals_set):
                            continue
                        if is_square_deadlock(bx, by, board, temp_boxes, goals_set):
                            continue
                        if is_tunnel_deadlock(bx, by, board, goals_set):
                            continue
                        
                        new_boxes = frozenset(temp_boxes)
                    else: 
                        continue
                
                new_state = State((nx, ny), new_boxes, current.cost + 1, current, move)
                
                # TẠO KEY DUY NHẤT CHO TRẠNG THÁI
                state_key = (new_state.player_pos, new_state.boxes_pos)
                
                # KIỂM TRA: Nếu trạng thái chưa có hoặc tìm được đường ngắn hơn (cost nhỏ hơn)
                if state_key not in closed_list or new_state.cost < closed_list[state_key]:
                    new_state.heuristic = get_heuristic(new_state.player_pos, new_state.boxes_pos, goals_set)
                    closed_list[state_key] = new_state.cost # Lưu cost vào
                    heapq.heappush(open_list, new_state)
                    
    return None

def get_actions(State):
    actions = []
    while State.action:
        actions.append(State.action)
        State = State.parent
    return actions[::-1]