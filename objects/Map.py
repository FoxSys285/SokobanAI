import json

class Map:
    def __init__(self, id_map, grid):
        self.id_map = id_map
        self.grid = grid
        
    def obj_static(self):
        return [cell for row in self.grid for cell in row if cell in (0, 1, 3)]
    
    def obj_dynamic(self):
        return [cell for row in self.grid for cell in row if cell in (2, 4, 6)]