import json

class MapSokoban:
    def __init__(self, id_map, grid):
        self.id_map = id_map
        self.grid = grid
    
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
           
