import pygame
import threading
from obj_map import ListMap
from A_Star import solve_sokoban

filename = "Maps/sokoban_map.json"
ls = ListMap().doc_file(filename)
game_state = "MENU"
buttons = []
original_map = []
reset_button_rect = pygame.Rect(0, 0, 0, 0)
back_button_rect = pygame.Rect(0, 0, 0, 0)
AI_PLAY_rect = pygame.Rect(0, 0, 0, 0)
ai_path = [] # Danh sách các bước AI sẽ đi
last_ai_move_time = 0 # Tốc độ AI di chuyển

is_ai_calculating = False # Kiểm tra trạng thái tìm kiếm
def ai_worker(start_p, boxes, goals, sokoban_map):
    global ai_path, is_ai_calculating
    is_ai_calculating = True
    result = solve_sokoban(start_p, boxes, goals, sokoban_map)
    if result:
        ai_path = result
    else:
        print("Không tìm thấy lời giải!")
    is_ai_calculating = False
    
# TẢI HÌNH ẢNH
IMAGES = {}

def load_game_assets(tile_size):
    global IMAGES
    # tile_size là kích thước ô vuông (OBJ_W, OBJ_H)
    size = (int(tile_size), int(tile_size))
    
    try:
        IMAGES = {
            0: pygame.transform.scale(pygame.image.load("Images/san.png"), size),        # Sàn
            1: pygame.transform.scale(pygame.image.load("Images/tuong.png"), size),      # Tường
            2: pygame.transform.scale(pygame.image.load("Images/hop.png"), size),        # Hộp
            3: pygame.transform.scale(pygame.image.load("Images/dich.png"), size),       # Đích
            4: pygame.transform.scale(pygame.image.load("Images/nhan_vat.png"), size),   # Nhân vật
            5: pygame.transform.scale(pygame.image.load("Images/nhan_vat.png"), size),   # Nhân vật trên đích
            6: pygame.transform.scale(pygame.image.load("Images/hop_de_dich.png"), size) # Hộp trên đích
        }
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tải ảnh: {e}")
        pygame.quit()
        exit()

# ĐỊNH NGHĨA MÀU
COLORS = {
    0: (240, 240, 240), # Màu xám - SÀN
    1: (50, 50, 50), # Màu xám đậm - TƯỜNG
    2: (184, 134, 11), # Vàng sẫm - HỘP
    3: (34, 139, 34), # Xanh lá - ĐÍCH
    4: (220, 20, 60), # Đỏ - NHÂN VẬT
    5: (220, 20, 60), # Đỏ - NHÂN VẬT NẰM TRÊN Ô ĐÍCH
    6: (225, 0 , 255), # Hồng - THÙNG NẰM TRÊN Ô ĐÍCH
    7: (50, 125, 168) # Xanh dương nhạt
}


# KHUNG TRÒ CHƠI
SCREEN_W = 1000
SCREEN_H = 700

TILE_SIZE = 50

# Bộ đếm
COST = 0


pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

OBJ_W = OBJ_H = TILE_SIZE
load_game_assets(TILE_SIZE)

clock = pygame.time.Clock()
running = True
is_won = False

# Hàm lấy vị trí của nhân vật
def get_pos_player(matrix):
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            if matrix[i][j] == 4 or matrix[i][j] == 5:
                return i, j
    return None

# Hàm xử lý win
def check_win(matrix):
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            if matrix[i][j] == 3 or matrix[i][j] == 5:
                return False
    return True

btn_win_back_rect = pygame.Rect(0, 0, 0, 0)

def show_win_message():
    global btn_win_back_rect, game_state
    
    # 1. Vẽ một lớp phủ màu đen trong suốt (Optional)
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150)) # 150 là độ trong suốt
    screen.blit(overlay, (0, 0))
    
    # 2. Vẽ bảng thông báo chính giữa
    panel_w, panel_h = 400, 250
    panel_x = (SCREEN_W - panel_w) // 2
    panel_y = (SCREEN_H - panel_h) // 2
    pygame.draw.rect(screen, (255, 255, 255), (panel_x, panel_y, panel_w, panel_h), border_radius=15)
    pygame.draw.rect(screen, COLORS[3], (panel_x, panel_y, panel_w, panel_h), 5, border_radius=15) # Viền xanh lá
    
    # 3. Hiện chữ "YOU WIN"
    font_win = pygame.font.SysFont("Patrick Hand", 60, True)
    text = font_win.render("WIN!!!", True, COLORS[3])
    screen.blit(text, (panel_x + (panel_w - text.get_width())//2, panel_y + 40))
    
    # 4. Hiện nút "QUAY LẠI MENU"
    btn_win_back_rect = draw_button("MENU", panel_x + 100, panel_y + 140, 200, 60, (200, 200, 200))

def move_player(old_r, old_c, new_r, new_c):
    # Nếu ô cũ là 'Nhân vật trên đích' (5) thì trả lại 'Đích' (3), ngược lại trả về 'Sàn' (0)
    sokoban_map[old_r][old_c] = 3 if original_map[old_r][old_c] in [3, 5, 6] else 0
    
    # Nếu ô mới là 'Đích' (3), nhân vật tới đó sẽ thành 'Nhân vật trên đích' (5)
    if sokoban_map[new_r][new_c] == 3:
        sokoban_map[new_r][new_c] = 5
    else:
        sokoban_map[new_r][new_c] = 4

# Hàm xử lý các nút
def button_click():
    global running, game_state, sokoban_map, ROWS, COLS, OBJ_W, OBJ_H, original_map, COST, ai_path
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            
            # 1. Logic ở MENU
            if game_state == "MENU":
                for btn in buttons:
                    if btn["rect"].collidepoint(mouse_pos):
                        # QUAN TRỌNG: Lưu bản copy sâu để reset
                        original_map = [row[:] for row in btn["map_data"]]
                        sokoban_map = [row[:] for row in btn["map_data"]]
                        ROWS = len(sokoban_map)
                        COLS = len(sokoban_map[0])
                        
                        # --- TÍNH TOÁN LẠI KÍCH THƯỚC Ô ---
                        SIDEBAR_W = 200
                        padding = 40  # Khoảng cách đệm để map không dính sát mép màn hình
                        
                        # Vùng khả dụng để vẽ map
                        available_w = SCREEN_W - SIDEBAR_W - padding
                        available_h = SCREEN_H - padding
                        
                        # Tính TILE_SIZE sao cho vừa cả chiều rộng và chiều cao
                        TILE_SIZE = min(available_w // COLS, available_h // ROWS)
                        
                        # Giới hạn kích thước tối đa (không để ô quá to nếu map quá nhỏ)
                        if TILE_SIZE > 60: 
                            TILE_SIZE = 60 
                        
                        OBJ_W = OBJ_H = TILE_SIZE
                        
                        # TẢI LẠI ẢNH THEO KÍCH THƯỚC MỚI
                        load_game_assets(TILE_SIZE)
                        
                        game_state = "PLAYING"
                        return

            # 2. Logic ở PLAYING
            elif game_state == "PLAYING":
                # Nhấn nút quay về Menu khi đã thắng
                if check_win(sokoban_map):
                    if btn_win_back_rect.collidepoint(mouse_pos):
                        game_state = "MENU"
                        COST = 0
                        return
                
                # Nút Reset (luôn bấm được khi đang chơi)
                if reset_button_rect.collidepoint(mouse_pos):
                    sokoban_map = [row[:] for row in original_map]
                    COST = 0
                
                # Nút Back (quay lại menu bất cứ lúc nào)
                if back_button_rect.collidepoint(mouse_pos):
                    game_state = "MENU"
                    COST = 0
                
                if AI_PLAY_rect.collidepoint(mouse_pos):
                    # Trích xuất dữ liệu để giải
                    p_pos = get_pos_player(sokoban_map)
                    # Lưu ý: get_pos_player trả về (row, col), solver cần (x, y)
                    start_p = (p_pos[1], p_pos[0]) 
                    
                    boxes = []
                    goals = []
                    for r in range(len(sokoban_map)):
                        for c in range(len(sokoban_map[0])):
                            if sokoban_map[r][c] in [2, 6]: 
                                boxes.append((c, r))
                            if sokoban_map[r][c] in [3, 5, 6]: 
                                goals.append((c, r))
                    
                    ai_path = solve_sokoban(start_p, boxes, goals, sokoban_map)
                    ai_result = solve_sokoban(start_p, boxes, goals, sokoban_map)
                    if ai_result:
                        ai_path = ai_result
                    else:
                        print("AI không tìm thấy đường đi cho màn này!")
                        return
                
                if AI_PLAY_rect.collidepoint(mouse_pos) and not is_ai_calculating:
                    # Reset lại đường đi cũ
                    ai_path.clear() 
                    
                    p_pos = get_pos_player(sokoban_map)
                    start_p = (p_pos[1], p_pos[0])
                    
                    boxes = []
                    goals = []
                    for r in range(len(sokoban_map)):
                        for c in range(len(sokoban_map[0])):
                            if sokoban_map[r][c] in [2, 6]: 
                                boxes.append((c, r))
                            if sokoban_map[r][c] in [3, 5, 6]: 
                                goals.append((c, r))

                    # CHỈ CHẠY THREAD, không gọi hàm solve trực tiếp ở đây
                    threading.Thread(target=ai_worker, args=(start_p, boxes, goals, [row[:] for row in sokoban_map]), daemon=True).start()

        # 3. Logic điều khiển nhân vật
        if event.type == pygame.KEYDOWN and game_state == "PLAYING" and not check_win(sokoban_map):
            if ai_path:
                continue
            
            if event.key == pygame.K_r: # Phím tắt Reset
                sokoban_map = [row[:] for row in original_map]
                COST = 0
                return
            if event.key == pygame.K_ESCAPE:
                game_state = "MENU"
                COST = 0
                return
            playe_r, playe_c = get_pos_player(sokoban_map)
            dir_c, dir_r = 0, 0
            if event.key == pygame.K_RIGHT: 
                dir_c = 1
            elif event.key == pygame.K_LEFT: 
                dir_c = -1
            elif event.key == pygame.K_UP: 
                dir_r = -1
            elif event.key == pygame.K_DOWN: 
                dir_r = 1
            
            new_r, new_c = playe_r + dir_r, playe_c + dir_c
            
            if 0 <= new_r < ROWS and 0 <= new_c < COLS:
                target = sokoban_map[new_r][new_c]
                if target in [0, 3]: # Đi vào sàn/đích
                    move_player(playe_r, playe_c, new_r, new_c)
                    COST += 1
                elif target in [2, 6]: # Đẩy hộp
                    br, bc = new_r + dir_r, new_c + dir_c
                    if 0 <= br < ROWS and 0 <= bc < COLS:
                        if sokoban_map[br][bc] in [0, 3]:
                            sokoban_map[br][bc] = 6 if sokoban_map[br][bc] == 3 else 2
                            move_player(playe_r, playe_c, new_r, new_c)
                            COST += 1
                            
# Màn chơi
def level_game(sokoban_map):
    global reset_button_rect, back_button_rect, AI_PLAY_rect, COST
    
    # --- PHẦN 1: VẼ SIDEBAR (THANH ĐIỀU KHIỂN) ---
    SIDEBAR_W = 200
    # Vẽ nền cho thanh sidebar để phân biệt với vùng chơi
    pygame.draw.rect(screen, (45, 45, 45), (0, 0, SIDEBAR_W, SCREEN_H))
    pygame.draw.line(screen, (100, 100, 100), (SIDEBAR_W, 0), (SIDEBAR_W, SCREEN_H), 2)

    # Vẽ các nút bấm nằm gọn trong sidebar
    back_button_rect = draw_button("BACK", 25, 50, 150, 50, (200, 200, 200))
    reset_button_rect = draw_button("RESET", 25, 130, 150, 50, (255, 165, 0))
    draw_button(f"STEP: {COST}", 25, 210, 150, 50, COLORS[7])
    AI_PLAY_rect = draw_button("AI", 25, 290, 150, 50, COLORS[3])
    
    if is_ai_calculating:
        img = pygame.font.SysFont("Patrick Hand", 30).render("AI ĐANG TÍNH TOÁN...", True, (255, 0, 0))
        screen.blit(img, (25, 360))
    
    
    # --- PHẦN 2: VẼ KHU VỰC CHƠI GAME (CĂN GIỮA TRONG PHẦN CÒN LẠI) ---
    # Chiều rộng vùng chơi còn lại là (SCREEN_W - SIDEBAR_W)
    playable_area_w = SCREEN_W - SIDEBAR_W
    
    # Tính toán căn giữa dựa trên vùng chơi còn lại
    offset_x = SIDEBAR_W + (playable_area_w - (COLS * OBJ_W)) // 2
    offset_y = (SCREEN_H - (ROWS * OBJ_H)) // 2
    
    for row in range(len(sokoban_map)):
        for col in range(len(sokoban_map[row])):
            obj_id = sokoban_map[row][col]
            
            x = offset_x + col * OBJ_W
            y = offset_y + row * OBJ_H
            
            # Luôn vẽ sàn bên dưới
            screen.blit(IMAGES[0], (x, y))
            
            if obj_id != 0:
                # Nếu là nhân vật hoặc hộp trên đích, vẽ đích trước
                if obj_id in [5, 6]:
                    screen.blit(IMAGES[3], (x, y))
                screen.blit(IMAGES[obj_id], (x, y))

# Hàm vẽ button
def draw_button(text, x, y, w, h, color):
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, color, rect)
    img = pygame.font.SysFont("Patrick Hand", 40, True).render(text, True, (0, 0, 0))
    screen.blit(img, (x + (w - img.get_width())//2, y + (h - img.get_height())//2))
    return rect

# Menu chọn màn
def menu():
    global game_state, sokoban_map, ROWS, COLS, OBJ_W, OBJ_H
    
    # Tiêu đề
    title_font = pygame.font.SysFont("Patrick Hand", 70, True)
    level_font = pygame.font.SysFont("Patrick Hand", 30, False)
    
    title_text = title_font.render("SOKOBAN AI", True, (255, 255, 255))
    level_text = level_font.render("Level Select", True, COLORS[7])
    
    screen.blit(title_text, (SCREEN_W // 2 - title_text.get_width() // 2, 50))
    screen.blit(level_text, (SCREEN_W // 2 - level_text.get_width() // 2, 130))
    

    # Cấu hình vị trí nút
    start_x = 80
    start_y = 220
    button_w = 140
    button_h = 100
    gap = 30 # Khoảng cách giữa các nút

    buttons.clear() # Làm trống danh sách nút mỗi lần vẽ lại

    # Chỉ lấy tối đa 10 màn chơi đầu tiên để vẽ
    for i in range(min(len(ls), 10)):
        row = i // 5  # Hàng 0 hoặc 1
        col = i % 5   # Cột từ 0 đến 4
        
        x = start_x + col * (button_w + gap)
        y = start_y + row * (button_h + gap)
        
        # Vẽ nút bằng hàm draw_button của bạn
        # Lấy id_map làm tên nút (ví dụ: "Map 1")
        rect = draw_button(f"Màn {ls[i].id_map}", x, y, button_w, button_h, (200, 200, 200))
        
        # Lưu lại Rect và dữ liệu map để xử lý click
        buttons.append({"rect": rect, "map_data": ls[i].grid})


# Chạy game
while running:
    screen.fill((30, 30, 30))
    
    button_click() # Xử lý sự kiện
    
    if game_state == "MENU":
        menu()
    elif game_state == "PLAYING":
        level_game(sokoban_map)
        if check_win(sokoban_map):
            show_win_message()
    
    if game_state == "PLAYING" and ai_path:
        now = pygame.time.get_ticks()
        if now - last_ai_move_time > 200:
            move = ai_path.pop(0)
            p_r, p_c = get_pos_player(sokoban_map)
            dr, dc = 0, 0
            if move == 'U': 
                dr = -1
            elif move == 'D': 
                dr = 1
            elif move == 'L': 
                dc = -1
            elif move == 'R': 
                dc = 1
            
            new_r, new_c = p_r + dr, p_c + dc
            target = sokoban_map[new_r][new_c]

            # TRƯỜNG HỢP 1: Đi vào ô trống hoặc ô đích (không có thùng)
            if target in [0, 3]:
                move_player(p_r, p_c, new_r, new_c)
                COST += 1
            
            # TRƯỜNG HỢP 2: Đẩy thùng (dùng elif để tránh chạy cả 2 khối lệnh)
            elif target in [2, 6]: 
                br, bc = new_r + dr, new_c + dc
                if 0 <= br < ROWS and 0 <= bc < COLS:
                    # Kiểm tra ô phía sau thùng KHÔNG được là tường hoặc thùng khác
                    if sokoban_map[br][bc] in [0, 3]:
                        # Cập nhật vị trí thùng mới: nếu là đích thì thành 6, không thì thành 2
                        sokoban_map[br][bc] = 6 if sokoban_map[br][bc] == 3 else 2
                        # Di chuyển nhân vật vào vị trí cũ của thùng
                        move_player(p_r, p_c, new_r, new_c)
                        COST += 1
            
            last_ai_move_time = now

        
    pygame.display.flip()
    clock.tick(60)


pygame.quit()