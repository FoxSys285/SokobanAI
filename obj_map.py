import json

class MapSokoban:
    def __init__(self, id_map, grid):
        self.id_map = id_map
        self.grid = grid
    
    def get_initial_state(self):
        player_pos = None
        boxes = []
        goals = []
        walls = set()

        for r, row in enumerate(self.grid):
            for c, val in enumerate(row):
                if val == 1: 
                    walls.add((c, r))
                if val == 3: 
                    goals.append((c, r))
                if val == 4 or val == 5: 
                    player_pos = (c, r)
                if val == 2: 
                    boxes.append((c, r))
                if val == 6: 
                    boxes.append((c, r))
                    goals.append((c, r))
                    
        return player_pos, frozenset(boxes), tuple(goals), walls
    
class ListMap:
    def __init__(self):
        self.ls = []
    
    def doc_file(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                dulieu = json.load(f)
                self.ls = [
                        MapSokoban(
                            id_map=item["id_map"],
                            grid=item["grid"]
                        ) for item in dulieu
                ]
                print("Đã đọc được file map")
                return self.ls
        except Exception as loi:
            print("Lỗi đọc file map: ",loi)
           
