from PIL import Image, ImageDraw, ImageFont
import io
import os # 导入 os 用于路径拼接

# --- 配置 ---
CELL_SIZE = 30
BORDER_COLOR = (128, 128, 128) # 灰色
HIDDEN_COLOR = (192, 192, 192) # 浅灰色
REVEALED_COLOR = (224, 224, 224) # 更浅的灰色
MINE_COLOR = (0, 0, 0) # 黑色
FLAG_COLOR = (255, 0, 0) # 红色
EXPLODED_MINE_BG_COLOR = (255, 100, 100) # 踩中地雷的红色背景
COORD_TEXT_COLOR = (80, 80, 80) # 坐标文字的深灰色
COORD_BG_COLOR = (210, 210, 210) # 坐标区域稍有不同的背景色
NUMBER_COLORS = {
    '1': (0, 0, 255),   # 蓝色
    '2': (0, 128, 0),   # 绿色
    '3': (255, 0, 0),   # 红色
    '4': (0, 0, 128),   # 深蓝色
    '5': (128, 0, 0),   # 深红色
    '6': (0, 128, 128), # 青色
    '7': (0, 0, 0),     # 黑色
    '8': (128, 128, 128) # 灰色
}

# 为坐标添加边距
COORD_MARGIN = int(CELL_SIZE * 0.8)

# --- 字体加载 ---
try:
    # 坐标使用较小字体
    COORD_FONT_SIZE = int(COORD_MARGIN * 0.6)
    COORD_FONT = ImageFont.truetype("arial.ttf", COORD_FONT_SIZE)
    # 单元格数字使用主字体
    CELL_FONT_SIZE = int(CELL_SIZE * 0.6)
    FONT = ImageFont.truetype("arial.ttf", CELL_FONT_SIZE)
except IOError:
    try:
        # 为没有 Arial 的系统提供备选字体 (例如某些 Linux 发行版)
        COORD_FONT = ImageFont.truetype("DejaVuSans.ttf", COORD_FONT_SIZE)
        FONT = ImageFont.truetype("DejaVuSans.ttf", CELL_FONT_SIZE)
    except IOError:
        # 如果其他字体加载失败，使用基础备选字体
        COORD_FONT = ImageFont.load_default()
        FONT = ImageFont.load_default()
        print("警告：无法加载首选字体。将使用默认 PIL 字体。")

# --- 辅助函数：获取文本尺寸 --- (处理 Pillow 版本差异)
def get_text_size(font, text):
    try:
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        offset_x = bbox[0]
        offset_y = bbox[1]
    except AttributeError: # 兼容旧版 Pillow
        width, height = font.getsize(text)
        offset_x = 0
        offset_y = 0
    return width, height, offset_x, offset_y

# --- 绘制函数 (已调整以适应 COORD_MARGIN 偏移) ---

def draw_cell(draw, x, y, color):
    """绘制单个单元格背景，考虑坐标边距偏移。"""
    draw.rectangle(
        [COORD_MARGIN + x * CELL_SIZE, COORD_MARGIN + y * CELL_SIZE,
         COORD_MARGIN + (x + 1) * CELL_SIZE, COORD_MARGIN + (y + 1) * CELL_SIZE],
        fill=color,
        outline=BORDER_COLOR
    )

def draw_number(draw, x, y, number_char):
    """在单元格中绘制数字，考虑坐标边距偏移。"""
    color = NUMBER_COLORS.get(number_char, (0, 0, 0)) # 默认为黑色
    text_width, text_height, offset_x, offset_y = get_text_size(FONT, number_char)

    # 将文本居中于单元格内
    cell_left = COORD_MARGIN + x * CELL_SIZE
    cell_top = COORD_MARGIN + y * CELL_SIZE
    text_x = cell_left + (CELL_SIZE - text_width) / 2 - offset_x
    text_y = cell_top + (CELL_SIZE - text_height) / 2 - offset_y

    draw.text((text_x, text_y), number_char, fill=color, font=FONT)

def draw_mine(draw, x, y):
    """在单元格中绘制地雷，考虑坐标边距偏移。"""
    center_x = COORD_MARGIN + x * CELL_SIZE + CELL_SIZE / 2
    center_y = COORD_MARGIN + y * CELL_SIZE + CELL_SIZE / 2
    radius = CELL_SIZE * 0.3
    draw.ellipse(
        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
        fill=MINE_COLOR
    )

def draw_flag(draw, x, y):
    """在单元格中绘制旗帜，考虑坐标边距偏移。"""
    center_x = COORD_MARGIN + x * CELL_SIZE + CELL_SIZE / 2
    center_y = COORD_MARGIN + y * CELL_SIZE + CELL_SIZE / 2
    # 简单的旗帜：红色三角形
    poly = [
        (center_x - CELL_SIZE * 0.2, center_y - CELL_SIZE * 0.3),
        (center_x + CELL_SIZE * 0.3, center_y),
        (center_x - CELL_SIZE * 0.2, center_y + CELL_SIZE * 0.3)
    ]
    draw.polygon(poly, fill=FLAG_COLOR)
    # 旗杆
    draw.line([(center_x - CELL_SIZE * 0.2, center_y - CELL_SIZE * 0.3),
               (center_x - CELL_SIZE * 0.2, center_y + CELL_SIZE * 0.4)], fill=(0,0,0), width=2)

# --- 坐标绘制函数 ---
def draw_coordinates(draw, width, height):
    """在边距中绘制列号和行号。"""
    # 绘制坐标区域背景
    draw.rectangle([0, 0, COORD_MARGIN, COORD_MARGIN + height * CELL_SIZE], fill=COORD_BG_COLOR)
    draw.rectangle([0, 0, COORD_MARGIN + width * CELL_SIZE, COORD_MARGIN], fill=COORD_BG_COLOR)
    # 绘制左上角方块
    draw.rectangle([0, 0, COORD_MARGIN, COORD_MARGIN], fill=COORD_BG_COLOR, outline=BORDER_COLOR)

    # 绘制列号 (X轴)
    for x in range(width):
        num_str = str(x + 1)
        text_width, text_height, offset_x, offset_y = get_text_size(COORD_FONT, num_str)
        cell_center_x = COORD_MARGIN + x * CELL_SIZE + CELL_SIZE / 2
        text_x = cell_center_x - text_width / 2 - offset_x
        text_y = (COORD_MARGIN - text_height) / 2 - offset_y
        draw.text((text_x, text_y), num_str, fill=COORD_TEXT_COLOR, font=COORD_FONT)
        # 在数字下方绘制网格线
        draw.line([(COORD_MARGIN + x * CELL_SIZE, 0), (COORD_MARGIN + x * CELL_SIZE, COORD_MARGIN)], fill=BORDER_COLOR)

    # 绘制行号 (Y轴)
    for y in range(height):
        num_str = str(y + 1)
        text_width, text_height, offset_x, offset_y = get_text_size(COORD_FONT, num_str)
        cell_center_y = COORD_MARGIN + y * CELL_SIZE + CELL_SIZE / 2
        text_x = (COORD_MARGIN - text_width) / 2 - offset_x
        text_y = cell_center_y - text_height / 2 - offset_y
        draw.text((text_x, text_y), num_str, fill=COORD_TEXT_COLOR, font=COORD_FONT)
        # 在数字右侧绘制网格线
        draw.line([(0, COORD_MARGIN + y * CELL_SIZE), (COORD_MARGIN, COORD_MARGIN + y * CELL_SIZE)], fill=BORDER_COLOR)

    # 绘制主网格区域的外边框线
    draw.line([(COORD_MARGIN, COORD_MARGIN), (COORD_MARGIN + width * CELL_SIZE, COORD_MARGIN)], fill=BORDER_COLOR)
    draw.line([(COORD_MARGIN, COORD_MARGIN), (COORD_MARGIN, COORD_MARGIN + height * CELL_SIZE)], fill=BORDER_COLOR)


# --- 主渲染函数 --- (已调整以适应坐标)

def render_board(game_state):
    """将扫雷棋盘状态渲染为带坐标的 PIL 图像。"""
    width = game_state["width"]
    height = game_state["height"]
    board = game_state["board"]
    revealed = game_state["revealed"]
    flagged = game_state["flagged"]
    game_over = game_state["game_over"]
    won = game_state["won"]
    mine_locations = game_state["mine_locations"]
    lost_mine_location = game_state["lost_mine_location"]

    # 计算包含坐标边距的图像尺寸
    img_width = width * CELL_SIZE + COORD_MARGIN
    img_height = height * CELL_SIZE + COORD_MARGIN
    image = Image.new('RGB', (img_width, img_height), color='white') # 白色背景
    draw = ImageDraw.Draw(image)

    # 首先绘制坐标数字
    draw_coordinates(draw, width, height)

    # 绘制游戏单元格 (考虑 COORD_MARGIN 偏移)
    for y in range(height):
        for x in range(width):
            cell_char = board[y][x]
            is_revealed = revealed[y][x]
            is_flagged = flagged[y][x]
            is_mine = (x, y) in mine_locations

            # 首先确定背景色
            bg_color = HIDDEN_COLOR
            if is_revealed:
                bg_color = REVEALED_COLOR
                if is_mine and (x,y) == lost_mine_location: # 高亮显示导致游戏结束的地雷
                     bg_color = EXPLODED_MINE_BG_COLOR

            draw_cell(draw, x, y, bg_color) # 使用带偏移的绘制函数

            # 根据状态绘制内容 (使用带偏移的绘制函数)
            if is_revealed:
                if is_mine:
                    draw_mine(draw, x, y)
                elif cell_char.isdigit():
                    draw_number(draw, x, y, cell_char)
            elif is_flagged:
                 draw_flag(draw, x, y)
            elif game_over and not won and is_mine:
                 draw_mine(draw, x, y)

            if game_over and is_mine and is_flagged:
                 draw_flag(draw, x, y)

    # 将图像转换为字节流
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr
