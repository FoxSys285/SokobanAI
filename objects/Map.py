class Map:
    def __init__(self, id_map, grid):
        self.id_map = id_map
        self.grid = grid
        
    def obj_static(self):
        return [cell for row in self.grid for cell in row if cell in (0, 1, 3)]
    
    def obj_dynamic(self):
        return [cell for row in self.grid for cell in row if cell in (2, 4, 6)]
    
    def check_win(self):
        """
        Kiểm tra chiến thắng: tất cả hộp phải nằm trên các vị trí mục tiêu
        Trả về True nếu chiến thắng, False nếu chưa
        
        Quy ước:
        - 2: box trên sàn
        - 3: goal trống
        - 6: box on target (hộp nằm trên goal)
        """
        # Đếm số box trên sàn (2) - nếu > 0 thì chưa thắng
        boxes_on_floor = sum(row.count(2) for row in self.grid)
        
        # Đếm số goal trống (3) - nếu > 0 thì chưa thắng
        empty_goals = sum(row.count(3) for row in self.grid)
        
        # Đếm số box trên target (6) - phải > 0
        boxes_on_target = sum(row.count(6) for row in self.grid)
        
        # Thắng: không còn box trên sàn, không còn goal trống, và có ít nhất 1 box trên target
        return boxes_on_floor == 0 and empty_goals == 0 and boxes_on_target > 0
    
    def get_positions(self):
        """
        Lấy vị trí của tất cả các đối tượng quan trọng
        Trả về dict chứa vị trí của player, boxes, và goals
        """
        positions = {
            'player': None,
            'boxes': [],
            'goals': []
        }
        
        for row_idx, row in enumerate(self.grid):
            for col_idx, cell in enumerate(row):
                if cell == 2:  # Player
                    positions['player'] = (row_idx, col_idx)
                elif cell == 4:  # Box
                    positions['boxes'].append((row_idx, col_idx))
                elif cell == 3:  # Goal
                    positions['goals'].append((row_idx, col_idx))
        
        return positions
    
    def get_box_positions(self):
        boxes = [] # Dùng list để dễ dàng thêm phần tử
        for row_idx, row in enumerate(self.grid):
            for col_idx, cell in enumerate(row):
                if cell == 4:  # Box
                    boxes.append((row_idx, col_idx))
        
        # Ép về tuple ở cuối cùng để danh sách hộp không bị thay đổi ngẫu nhiên
        # và có thể dùng làm key (hashable) nếu cần lưu trạng thái
        return tuple(boxes) 

    def get_player_position(self):
        for row_idx, row in enumerate(self.grid):
            for col_idx, cell in enumerate(row):
                if cell == 2:  # Player
                    return (row_idx, col_idx)
        return None
    
    def get_goal_positions(self):
        temp_goals = []
        for row_idx, row in enumerate(self.grid):
            for col_idx, cell in enumerate(row):
                if cell == 3:  # Goal
                    temp_goals.append((row_idx, col_idx))
        # Dùng tuple cho đích vì đích dùng để tính Heuristic (duyệt qua từng đích)
        return tuple(temp_goals)
    
    def get_walls(self):
        walls = set() # Dùng Set thay cho Dict
        for row_idx, row in enumerate(self.grid):
            for col_idx, cell in enumerate(row):
                if cell == 1:  # Wall
                    walls.add((row_idx, col_idx)) 
        return walls