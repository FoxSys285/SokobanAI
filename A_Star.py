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
    
    # Chuyển về list để tính toán
    boxes = list(boxes_pos)
    targets = list(goals)
    total_h = 0

    # 1. Tính toán khoảng cách giữa các cặp (Hộp - Đích)
    # Sử dụng phương pháp Greedy bám sát nhất với chi phí tối ưu
    while boxes:
        min_dist = float('inf')
        selected_box_idx = 0
        selected_goal_idx = 0
        
        for i, box in enumerate(boxes):
            for j, goal in enumerate(targets):
                # Manhattan distance
                d = abs(box[0] - goal[0]) + abs(box[1] - goal[1])
                if d < min_dist:
                    min_dist = d
                    selected_box_idx = i
                    selected_goal_idx = j
        
        total_h += min_dist
        boxes.pop(selected_box_idx)
        targets.pop(selected_goal_idx)

    # 2. Chi phí người di chuyển đến "vị trí đẩy" (Push Position)
    # Thay vì tính đến hộp, hãy tính đến ô phía sau hộp
    penalty = 0
    for box in boxes_pos:
        # Nếu hộp chưa ở đích, cộng thêm một chút chi phí để AI ưu tiên tiếp cận
        d_player = abs(player_pos[0] - box[0]) + abs(player_pos[1] - box[1])
        penalty = min(penalty, d_player) if penalty != 0 else d_player
        
    return (total_h * 1.5) + penalty

# Kiểm tra hộp bị kẹt
def is_deadlock(box_pos, board, goals):
    x, y = box_pos
    if box_pos in goals: 
        return False
    
    up = board[y-1][x] == 1
    down = board[y+1][x] == 1
    left = board[y][x-1] == 1
    right = board[y][x+1] == 1
    
    if (up and left) or (up and right) or (down and left) or (down and right):
        return True
        
    # Kiểm tra nếu hộp dính tường trên hoặc dưới
    if up or down:
        if not has_pull_out_or_goal(x, y, board, goals, horizontal=True):
            return True
            
    # Kiểm tra nếu hộp dính tường trái hoặc phải
    if left or right:
        if not has_pull_out_or_goal(x, y, board, goals, horizontal=False):
            return True
                    
    return False

def has_pull_out_or_goal(bx, by, board, goals, horizontal=True):
    """
    Kiểm tra xem dọc theo bức tường mà hộp đang đứng có ô đích 
    hoặc có lỗ hổng nào để đẩy hộp ra khỏi tường không.
    """
    if horizontal:
        # Kiểm tra hai phía Trái và Phải của hộp dọc theo bức tường ngang
        for direction in [-1, 1]:
            curr_x = bx
            while True:
                curr_x += direction
                # Nếu chạm tường: đoạn này bị chặn
                if board[by][curr_x] == 1:
                    break
                # Nếu có ô đích trên đoạn này: Không phải deadlock
                if (curr_x, by) in goals:
                    return True
                # Nếu có khoảng trống để đẩy hộp ra (không có tường song song):
                # Kiểm tra cả phía trên và phía dưới xem có lỗ hổng không
                if board[by-1][curr_x] != 1 and board[by+1][curr_x] != 1:
                    return True
        return False
    else:
        # Kiểm tra hai phía Trên và Dưới của hộp dọc theo bức tường dọc
        for direction in [-1, 1]:
            curr_y = by
            while True:
                curr_y += direction
                if board[curr_y][bx] == 1:
                    break
                if (bx, curr_y) in goals:
                    return True
                if board[curr_y][bx-1] != 1 and board[curr_y][bx+1] != 1:
                    return True
        return False

def solve_sokoban(start_player, start_boxes, goals, board, limit=300000):
    iterations = 0
    goals_set = frozenset(goals)
    
    # Khởi tạo trạng thái đầu
    start_state = State(start_player, start_boxes, 0)
    # Sửa lỗi truyền thiếu tham số ở đây luôn:
    start_state.heuristic = get_heuristic(start_player, start_boxes, goals_set)
    
    open_list = [start_state]
    
    # SỬA TẠI ĐÂY: Sử dụng dictionary để lưu {Trạng_thái: Chi_phí_thấp_nhất}
    # Ta dùng tuple (player_pos, boxes_pos) làm key vì nó bất biến (immutable) và hashable
    closed_list = {} 
    closed_list[(start_state.player_pos, start_state.boxes_pos)] = 0

    rows = len(board)
    cols = len(board[0]) 

    while open_list:
        current = heapq.heappop(open_list)
        iterations += 1

        if iterations > limit: 
            return None
        if current.boxes_pos == goals_set: 
            return get_actions(current)

        x, y = current.player_pos
        for dx, dy, move in [(0, -1, 'U'), (0, 1, 'D'), (-1, 0, 'L'), (1, 0, 'R')]:
            nx, ny = x + dx, y + dy
            
            if 0 <= nx < cols and 0 <= ny < rows and board[ny][nx] != 1:
                new_boxes = set(current.boxes_pos)
                if (nx, ny) in new_boxes:
                    bx, by = nx + dx, ny + dy
                    if 0 <= bx < cols and 0 <= by < rows and board[by][bx] != 1 and (bx, by) not in new_boxes:
                        if is_deadlock((bx, by), board, goals_set): 
                            continue
                        new_boxes.remove((nx, ny))
                        new_boxes.add((bx, by))
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