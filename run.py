import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import json

WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 640

root = tk.Tk()
root.title("Sokoban - AI")

SCREEN_WIDTH = int((root.winfo_screenwidth() / 2) - (WINDOW_WIDTH / 2))
SCREEN_HEIGHT = int((root.winfo_screenheight() / 2) - (WINDOW_HEIGHT / 2)) - 20

root.resizable(False, False)
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{SCREEN_WIDTH}+{SCREEN_HEIGHT}")

#================== CÁC HÀM HỖ TRỢ ==================#
def update_frame():
    
    # Lặp lại sau 16ms (tương đương ~60 FPS: 1000ms / 60 = 16.6)
    root.after(16, update_frame)

# Xử lí ảnh
def load_image(path, witdh, height):
    try:
        image = Image.open(path)
        image = image.resize((witdh, height), Image.LANCZOS)
    except Exception as error:
        print(f"Lỗi tải ảnh: {path} - {error}")
        return None
    return ImageTk.PhotoImage(image)

def on_start_click(event):
    menu.place_forget()  # Ẩn menu
    menu_start.place(x=0, y=0)  # Hiển bảng chọn màn

def on_credits_click(event):
    print("Credits button clicked")

def on_exit_click(event):
    root.destroy()

def on_start_enter(event):
    menu.itemconfig("start_button", fill="yellow")
    menu.itemconfig("start_text", fill="white")
    menu.itemconfig("start_button", outline="yellow")

def on_start_leave(event):
    menu.itemconfig("start_button", fill="")
    menu.itemconfig("start_text", fill="lightblue")
    menu.itemconfig("start_button", outline="lightblue")
    
def on_credits_enter(event):
    menu.itemconfig("credits_button", fill="yellow")
    menu.itemconfig("credits_text", fill="white")
    menu.itemconfig("credits_button", outline="yellow")

def on_credits_leave(event):
    menu.itemconfig("credits_button", fill="")
    menu.itemconfig("credits_text", fill="lightblue")
    menu.itemconfig("credits_button", outline="lightblue")

def on_exit_enter(event):
    menu.itemconfig("exit_button", fill="yellow")
    menu.itemconfig("exit_text", fill="white")
    menu.itemconfig("exit_button", outline="yellow")

def on_exit_leave(event):
    menu.itemconfig("exit_button", fill="")
    menu.itemconfig("exit_text", fill="lightblue")
    menu.itemconfig("exit_button", outline="lightblue")
#================== KẾT THÚC CÁC HÀM HỖ TRỢ ==================#

#================== FRAME MENU ==================#
# Tải hình nền
background_image = load_image("assets/bg.png", WINDOW_WIDTH, WINDOW_HEIGHT)
if background_image:
    menu = tk.Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, highlightthickness=0)
    menu.create_image(0, 0, anchor=tk.NW, image=background_image)
    menu.place(x=0, y=0)
    
    menu_start = tk.Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, highlightthickness=0)
    menu_start.create_image(0, 0, anchor=tk.NW, image=background_image)
else:
    print("Không thể tải hình nền. Sử dụng màu nền mặc định.")
    root.configure(bg="lightgray")
    menu = tk.Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, highlightthickness=0)
    menu.place(x=0, y=0)
    
menu.create_text(WINDOW_WIDTH // 2, 80, text="SOKOBAN", fill="yellow", font=("Arial", 60, "bold"))
menu.create_text(WINDOW_WIDTH // 2 + 3, 80 + 3, text="SOKOBAN", fill="#808080", font=("Arial", 60, "bold"))

menu.create_text(WINDOW_WIDTH // 2, 150, text="ADVENTURE", fill="white", font=("Arial", 30, "bold"))
# Vẽ các nút
menu.create_rectangle(80, 240, 400, 320, fill="", outline="lightblue", width=3, tags="start_button")
menu.create_rectangle(80, 360, 400, 440, fill="", outline="lightblue", width=3, tags="credits_button")
menu.create_rectangle(80, 480, 400, 560, fill="", outline="lightblue", width=3, tags="exit_button")

# Vẽ chữ trên nút
menu.create_text(240, 280, text="START", fill="lightblue", font=("Arial", 24, "bold"), tags="start_text")
menu.create_text(240, 400, text="CREDITS", fill="lightblue", font=("Arial", 24, "bold"), tags="credits_text")
menu.create_text(240, 520, text="EXIT", fill="lightblue", font=("Arial", 24, "bold"), tags="exit_text")

menu.tag_bind("start_text", "<Button-1>", on_start_click)
menu.tag_bind("credits_text", "<Button-1>", on_credits_click)
menu.tag_bind("exit_text", "<Button-1>", on_exit_click)

menu.tag_bind("start_button", "<Button-1>", on_start_click)
menu.tag_bind("credits_button", "<Button-1>", on_credits_click)
menu.tag_bind("exit_button", "<Button-1>", on_exit_click)

menu.tag_bind("start_button", "<Enter>", on_start_enter)
menu.tag_bind("start_button", "<Leave>", on_start_leave)
menu.tag_bind("start_text", "<Enter>", on_start_enter)
menu.tag_bind("start_text", "<Leave>", on_start_leave)

menu.tag_bind("credits_button", "<Enter>", on_credits_enter)
menu.tag_bind("credits_button", "<Leave>", on_credits_leave)
menu.tag_bind("credits_text", "<Enter>", on_credits_enter)
menu.tag_bind("credits_text", "<Leave>", on_credits_leave)

menu.tag_bind("exit_button", "<Enter>", on_exit_enter)
menu.tag_bind("exit_button", "<Leave>", on_exit_leave)
menu.tag_bind("exit_text", "<Enter>", on_exit_enter)
menu.tag_bind("exit_text", "<Leave>", on_exit_leave)
#================== KẾT THÚC FRAME MENU ==================#

#================== FRAME CHỌN MÀN ==================#
# Nút quay lại menu chính
menu_start.create_text(60, 40, text="Back", fill="lightblue", font=("Arial", 26), tags="back_button")
def on_back_click(event):
    menu_start.place_forget()  # Ẩn bảng chọn màn
    menu.place(x=0, y=0)  # Hiển thị lại menu chính
    
menu_start.tag_bind("back_button", "<Button-1>", on_back_click)
menu_start.tag_bind("back_button", "<Enter>", lambda e: menu_start.itemconfig("back_button", fill="yellow"))
menu_start.tag_bind("back_button", "<Leave>", lambda e: menu_start.itemconfig("back_button", fill="lightblue"))

# Load màn chơi từ file JSON
def load_maps(path="maps/sokoban_map.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            maps = json.load(f)
    except Exception as e:
        print(f"Lỗi tải maps: {e}")
        return []
    return maps

# Vẽ các màn chơi lên canvas
def render_preview(grid, max_size=360):
    rows = len(grid)
    cols = max(len(r) for r in grid)
    # choose cell size to fit into max_size
    cell = max(6, min(40, max_size // max(rows, cols)))
    width = cols * cell
    height = rows * cell
    img = Image.new("RGB", (width, height), (220, 220, 220))
    draw = ImageDraw.Draw(img)

    colors = {
        0: (245, 245, 245), # floor
        1: (100, 100, 100), # wall
        2: (160, 110, 60), # box
        3: (255, 200, 0), # target
        4: (30, 120, 200), # player
        6: (150, 0, 150) # box on target
    }

    for r, row in enumerate(grid):
        for c, cellval in enumerate(row):
            x0 = c * cell
            y0 = r * cell
            x1 = x0 + cell
            y1 = y0 + cell
            color = colors.get(cellval, colors[0])
            draw.rectangle([x0, y0, x1, y1], fill=color)
            # small border for tiles
            draw.rectangle([x0, y0, x1 - 1, y1 - 1], outline=(180, 180, 180))

    img.thumbnail((max_size, max_size), Image.LANCZOS)
    return ImageTk.PhotoImage(img)

maps_list = load_maps()
current_index = 0

preview_x = WINDOW_WIDTH // 2
preview_y = 260

preview_label_id = None
preview_image_obj = None

# Hiển thị màn chơi đã chọn
def show_level(index):
    global current_index, preview_image_obj, preview_label_id
    if not maps_list:
        return
    index = index % len(maps_list)
    current_index = index
    m = maps_list[index]
    grid = m.get("grid", [])
    img = render_preview(grid, max_size=360)
    preview_image_obj = img
    menu_start.delete("preview")
    menu_start.create_image(preview_x, preview_y, image=img, tags=("preview",), anchor=tk.CENTER)
    menu_start.create_rectangle(preview_x - 120, preview_y + 190, preview_x + 120, preview_y + 240, fill="#222", outline="", tags=("preview",))
    menu_start.create_text(preview_x, preview_y + 215, text=f"Level {m.get('id_map', index+1)}", fill="white", font=("Arial", 18, "bold"), tags=("preview",))
    
def next_level():
    show_level(current_index + 1)

def prev_level():
    show_level(current_index - 1)

# Các nút điều hướng
left_btn = tk.Button(menu_start, text="◀", font=("Arial", 24), bg="darkblue", fg="white", command=prev_level)
left_btn.place(x=preview_x - 260, y=preview_y - 30, width=60, height=60)
right_btn = tk.Button(menu_start, text="▶", font=("Arial", 24), bg="darkblue", fg="white", command=next_level)
right_btn.place(x=preview_x + 200, y=preview_y - 30, width=60, height=60)

if maps_list:
    show_level(0)
else:
    menu.create_text(WINDOW_WIDTH // 2, 300, text="No maps found", fill="white", font=("Arial", 16))

def play_game():
    menu_start.place_forget()  # Ẩn bảng chọn màn
    # Initialize game state for the selected level and draw it
    init_game_state(current_index)
    render_game_map(current_index)
    game.place(x=0, y=0)  # Hiển thị frame game

play_btn = tk.Button(menu_start, text = "Play", font=("Arial", 20, "bold"), bg="#FFC800", fg="white", command=play_game)
play_btn.place(x=WINDOW_WIDTH // 2 - 100, y=preview_y + 270, width=200, height=50)
#================== KẾT THÚC FRAME CHỌN MÀN ==================#

#================== FRAME CREDITS ==================#

#================== KẾT THÚC FRAME CREDITS ==================#

#================== FRAME GAME ==================#
game = tk.Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, highlightthickness=0)

side_left_img = load_image("assets/bg_game.png", WINDOW_WIDTH, WINDOW_HEIGHT)
game.create_image(0, 0, anchor=tk.NW, image=side_left_img)

game.create_rectangle(0, 0, 160, WINDOW_HEIGHT, fill="#3C68BA", outline="gray", width=3)
game.create_text(80, 40, text="SOKOBAN", fill="white", font=("Arial", 20, "bold"))

game.create_text(80, 620, text="Back", fill="white", font=("Arial", 16, "bold"), tags="prev_text")
def on_prev_click(event):
    game.place_forget()  # Ẩn frame game
    menu_start.place(x=0, y=0)
    
game.tag_bind("prev_text", "<Button-1>", on_prev_click)
game.tag_bind("prev_text", "<Enter>", lambda e: game.itemconfig("prev_text", fill="yellow"))
game.tag_bind("prev_text", "<Leave>", lambda e: game.itemconfig("prev_text", fill="white"))
#================== KẾT THÚC FRAME GAME ==================# 

# ---------------- Map rendering on GAME frame ----------------
# Holds references to image objects to prevent GC
game_image_objs = []

def clear_game_map():
    global game_image_objs
    game.delete("map")
    game_image_objs = []

def render_game_map(index):
    """Render the `maps_list[index]` grid onto the `game` canvas using images from `assets`.
    This draws tiles starting at a padded area to the right of the left sidebar.
    """
    clear_game_map()
    if not maps_list:
        return
    index = index % len(maps_list)
    m = maps_list[index]
    grid = m.get("grid", [])
    rows = len(grid)
    cols = max((len(r) for r in grid), default=0)
    if rows == 0 or cols == 0:
        return

    # define drawable area (leave sidebar 160px)
    pad_left = 180
    pad_top = 40
    pad_right = 20
    pad_bottom = 40
    area_w = WINDOW_WIDTH - pad_left - pad_right
    area_h = WINDOW_HEIGHT - pad_top - pad_bottom

    # cell size chosen to fit the grid
    cell = max(16, min(64, min(area_w // cols, area_h // rows)))

    map_w = cols * cell
    map_h = rows * cell
    start_x = pad_left + (area_w - map_w) // 2
    start_y = pad_top + (area_h - map_h) // 2

    # load tile images scaled to `cell`
    tile_paths = {
        'floor': "assets/floor.png",
        'wall': "assets/wall.png",
        'box': "assets/box.png",
        'box_target': "assets/box_in_target.png",
        'target': "assets/target.png",
        'player': "assets/player.png",
    }

    tiles = {}
    for k, p in tile_paths.items():
        img = load_image(p, cell, cell)
        tiles[k] = img

    # draw tiles: always draw floor first, then overlays
    global game_image_objs
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            x = start_x + c * cell
            y = start_y + r * cell
            # floor
            floor_img = tiles.get('floor')
            if floor_img:
                iid = game.create_image(x, y, anchor=tk.NW, image=floor_img, tags=("map",))
                game_image_objs.append(floor_img)

            # overlay depending on cell value
            # mapping based on preview colors: 0 floor,1 wall,2 box,3 target,4 player,6 box on target
            if val == 1:
                img = tiles.get('wall')
            elif val == 2:
                img = tiles.get('box')
            elif val == 3:
                img = tiles.get('target')
            elif val == 4:
                img = tiles.get('player')
            elif val == 6:
                img = tiles.get('box_target')
            else:
                img = None

            if img:
                iid = game.create_image(x, y, anchor=tk.NW, image=img, tags=("map",))
                game_image_objs.append(img)

# ---------------- end map rendering ----------------

# ---------------- Game state & movement ----------------
# current game state: base layer (0 floor,1 wall,3 target), object layer (None,'box','player')
game_level_index = None
current_base = None
current_obj = None
player_pos = None

def init_game_state(index):
    """Create current_base/current_obj/player_pos from maps_list[index]."""
    global game_level_index, current_base, current_obj, player_pos
    if not maps_list:
        return
    index = index % len(maps_list)
    m = maps_list[index]
    grid = m.get("grid", [])
    rows = len(grid)
    cols = max((len(r) for r in grid), default=0)
    # normalize ragged rows
    current_base = [[0 for _ in range(cols)] for _ in range(rows)]
    current_obj = [[None for _ in range(cols)] for _ in range(rows)]
    player_pos = None
    for r, row in enumerate(grid):
        for c in range(cols):
            val = row[c] if c < len(row) else 0
            if val == 1:
                current_base[r][c] = 1
            elif val == 3 or val == 6:
                # target or box-on-target -> base is target
                current_base[r][c] = 3
            else:
                current_base[r][c] = 0

            if val == 2:
                current_obj[r][c] = 'box'
            elif val == 6:
                current_obj[r][c] = 'box'
            elif val == 4:
                current_obj[r][c] = 'player'
                player_pos = (r, c)

    game_level_index = index

def render_game_map(index):
    """Render using current state if initialized, otherwise fallback to raw map."""
    clear_game_map()
    if not maps_list:
        return
    index = index % len(maps_list)

    use_state = (globals().get('current_base') is not None and globals().get('game_level_index') == index)
    if use_state:
        base = current_base
        obj = current_obj
        rows = len(base)
        cols = len(base[0]) if rows else 0
    else:
        m = maps_list[index]
        grid = m.get('grid', [])
        rows = len(grid)
        cols = max((len(r) for r in grid), default=0)

    if rows == 0 or cols == 0:
        return

    # define drawable area (leave sidebar 160px)
    pad_left = 180
    pad_top = 40
    pad_right = 20
    pad_bottom = 40
    area_w = WINDOW_WIDTH - pad_left - pad_right
    area_h = WINDOW_HEIGHT - pad_top - pad_bottom

    # cell size chosen to fit the grid
    cell = max(16, min(64, min(area_w // cols, area_h // rows)))

    map_w = cols * cell
    map_h = rows * cell
    start_x = pad_left + (area_w - map_w) // 2
    start_y = pad_top + (area_h - map_h) // 2

    # load tile images scaled to `cell`
    tile_paths = {
        'floor': "assets/floor.png",
        'wall': "assets/wall.png",
        'box': "assets/box.png",
        'box_target': "assets/box_in_target.png",
        'target': "assets/target.png",
        'player': "assets/player.png",
    }

    tiles = {}
    for k, p in tile_paths.items():
        img = load_image(p, cell, cell)
        tiles[k] = img

    global game_image_objs
    for r in range(rows):
        for c in range(cols):
            x = start_x + c * cell
            y = start_y + r * cell

            # determine base/object values
            if use_state:
                b = base[r][c]
                o = obj[r][c]
            else:
                # fallback to original encoded values
                m = maps_list[index]
                grid = m.get('grid', [])
                val = grid[r][c] if c < len(grid[r]) else 0
                if val == 1:
                    b = 1
                    o = None
                elif val == 3:
                    b = 3
                    o = None
                elif val == 2:
                    b = 0
                    o = 'box'
                elif val == 6:
                    b = 3
                    o = 'box'
                elif val == 4:
                    b = 0
                    o = 'player'
                else:
                    b = 0
                    o = None

            # draw wall or floor
            if b == 1:
                img = tiles.get('wall')
                if img:
                    game.create_image(x, y, anchor=tk.NW, image=img, tags=("map",))
                    game_image_objs.append(img)
                continue

            floor_img = tiles.get('floor')
            if floor_img:
                game.create_image(x, y, anchor=tk.NW, image=floor_img, tags=("map",))
                game_image_objs.append(floor_img)

            # draw target underlays
            if b == 3:
                timg = tiles.get('target')
                if timg:
                    game.create_image(x, y, anchor=tk.NW, image=timg, tags=("map",))
                    game_image_objs.append(timg)

            # draw objects
            if o == 'box':
                if b == 3:
                    img = tiles.get('box_target')
                else:
                    img = tiles.get('box')
            elif o == 'player':
                img = tiles.get('player')
            else:
                img = None

            if img:
                game.create_image(x, y, anchor=tk.NW, image=img, tags=("map",))
                game_image_objs.append(img)

def move_player(dr, dc):
    """Attempt to move the player by (dr,dc). Handles pushing boxes."""
    global player_pos, current_obj, current_base
    if player_pos is None:
        return
    pr, pc = player_pos
    nr = pr + dr
    nc = pc + dc
    # bounds check
    if nr < 0 or nc < 0 or nr >= len(current_base) or nc >= len(current_base[0]):
        return

    # wall check
    if current_base[nr][nc] == 1:
        return

    target_obj = current_obj[nr][nc]
    if target_obj == 'box':
        br = nr + dr
        bc = nc + dc
        # bounds for box push
        if br < 0 or bc < 0 or br >= len(current_base) or bc >= len(current_base[0]):
            return
        if current_base[br][bc] == 1:
            return
        if current_obj[br][bc] is not None:
            return
        # push box
        current_obj[br][bc] = 'box'
        current_obj[nr][nc] = 'player'
        current_obj[pr][pc] = None
        player_pos = (nr, nc)
    else:
        # empty -> move player
        if target_obj is None:
            current_obj[nr][nc] = 'player'
            current_obj[pr][pc] = None
            player_pos = (nr, nc)

    # re-render
    render_game_map(game_level_index)

# movement button handlers
def on_up():
    move_player(-1, 0)

def on_down():
    move_player(1, 0)

def on_left():
    move_player(0, -1)

def on_right():
    move_player(0, 1)

# keyboard bindings
root.bind('<Up>', lambda e: on_up())
root.bind('<Down>', lambda e: on_down())
root.bind('<Left>', lambda e: on_left())
root.bind('<Right>', lambda e: on_right())

# ---------------- end game state & movement ----------------

update_frame()
root.mainloop()
