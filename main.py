from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp

from .game import MinesweeperGame
from .renderer import render_board

import re # 用于解析参数
from typing import Dict, Optional

# --- 难度设置 ---
DIFFICULTY_LEVELS = {
    "简单": {"width": 9, "height": 9, "mines": 10},
    "easy": {"width": 9, "height": 9, "mines": 10},
    "普通": {"width": 16, "height": 16, "mines": 40},
    "medium": {"width": 16, "height": 16, "mines": 40},
    "困难": {"width": 30, "height": 16, "mines": 99},
    "hard": {"width": 30, "height": 16, "mines": 99},
}
DEFAULT_DIFFICULTY = "普通"

# --- 游戏状态管理 ---
# 按会话（例如，每个聊天窗口或用户私聊）存储游戏
active_games: Dict[str, MinesweeperGame] = {}

# --- 辅助函数 ---
def get_game(session_id: str) -> Optional[MinesweeperGame]:
    """获取会话的活动游戏（如果存在）。"""
    return active_games.get(session_id)

def end_game(session_id: str):
    """移除会话的游戏。"""
    if session_id in active_games:
        del active_games[session_id]

def parse_coords(text: str) -> Optional[tuple[int, int]]:
    """从文本中解析 'x y' 坐标。"""
    match = re.match(r"^\s*(\d+)\s+(\d+)\s*$", text)
    if match:
        # 转换为 0-based 索引
        x = int(match.group(1)) - 1
        y = int(match.group(2)) - 1
        return x, y
    return None

# --- AstrBot 插件类 ---
@register("Minesweeper", "Jason.Joestar","简单的扫雷小游戏", "1.0.0")
class MinesweeperPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        logger.info(f"扫雷插件已加载！")

    async def _send_board(self, event: AstrMessageEvent, game: MinesweeperGame, message: str = ""):
        """渲染并发送当前棋盘状态。"""
        try:
            image_bytes = render_board(game.get_state())
            chain = []
            if message:
                chain.append(Comp.Plain(message)) # 添加换行符以增加间距
            chain.append(Comp.Image.fromBytes(image_bytes))
            yield event.chain_result(chain)
        except Exception as e:
            logger.error(f"渲染或发送棋盘时出错: {e}", exc_info=True)
            yield event.plain_result(f"抱歉，渲染扫雷棋盘时出错: {e}")

    @filter.command("扫雷")
    async def minesweeper_command_group(self, event: AstrMessageEvent):
        """扫雷的基础命令组。"""
        pass

    @filter.command("扫雷 help")
    async def minesweeper_help(self, event: AstrMessageEvent):
        """显示扫雷插件的帮助信息。"""
        help_text = """
        扫雷游戏指令组
        可用子命令: start, click, flag, end, help
        示例:
        /扫雷 start [难度]  (开始一个新游戏，难度可选：简单/普通/困难，默认为普通)
        /扫雷 click [列] [行] (点开指定格子，坐标从1开始)
        /扫雷 flag [列] [行]  (标记/取消标记指定格子，坐标从1开始)
        /扫雷 end             (结束当前游戏)
        /扫雷 help            (显示此帮助信息)
        """
        yield event.plain_result(help_text.strip())

    @filter.command("扫雷 start")
    async def start_game(self, event: AstrMessageEvent):
        """
        开始一个新的扫雷游戏。
        用法: /扫雷 start [难度]
        难度可选: 简单 (easy), 普通 (medium), 困难 (hard)
        如果未指定难度，默认为 普通。
        示例: /扫雷 start 困难
        """
        session_id = event.get_session_id()
        args_text = event.message_str.split("start", 1)[-1].strip()

        difficulty_key = DEFAULT_DIFFICULTY
        if args_text:
            lookup_key = args_text.lower()
            if lookup_key in DIFFICULTY_LEVELS:
                difficulty_key = lookup_key
            else:
                valid_options = ", ".join(k for k in DIFFICULTY_LEVELS.keys() if not k.islower())
                yield event.plain_result(f"无效的难度 '{args_text}'。可用难度: {valid_options}")
                return

        if get_game(session_id):
            yield event.plain_result("你已经有一个正在进行的游戏了。请先使用 /扫雷 end 结束它。")
            return

        try:
            config = DIFFICULTY_LEVELS[difficulty_key]
            width = config["width"]
            height = config["height"]
            mines = config["mines"]

            chosen_difficulty_name = difficulty_key
            if difficulty_key.islower():
                 for name, details in DIFFICULTY_LEVELS.items():
                      if details == config and not name.islower():
                           chosen_difficulty_name = name
                           break

            game = MinesweeperGame(width, height, mines)
            active_games[session_id] = game
            logger.info(f"为会话 {session_id} 启动了新的扫雷游戏 (难度: {chosen_difficulty_name}, {width}x{height}, {mines} 个雷)")
            start_message = f"游戏开始！难度：{chosen_difficulty_name} ({width}x{height}, {mines} 个雷)。\n请使用 /扫雷 click x y 来点开格子 (坐标从1开始)。"
            async for result in self._send_board(event, game, start_message):
                 yield result

        except ValueError as e:
             yield event.plain_result(f"无法开始游戏：{e}")
        except Exception as e:
            logger.error(f"启动游戏时出错: {e}", exc_info=True)
            yield event.plain_result(f"开始游戏时发生未知错误: {e}")

    @filter.command("扫雷 click")
    async def click_cell(self, event: AstrMessageEvent):
        """
        点开一个格子。
        用法: /扫雷 click [列号] [行号]
        示例: /扫雷 click 3 4
        """
        session_id = event.get_session_id()
        game = get_game(session_id)

        if not game:
            yield event.plain_result("当前没有进行中的游戏。请使用 /扫雷 start 开始新游戏。")
            return

        if game.game_over:
             yield event.plain_result("游戏已经结束了！")
             return

        args_text = event.message_str.split("click", 1)[-1].strip()
        coords = parse_coords(args_text)

        if not coords:
            yield event.plain_result("无效的坐标格式。请使用：/扫雷 click [列号] [行号] (例如: /扫雷 click 3 4)")
            return

        x, y = coords
        if not game._is_valid(x, y):
             yield event.plain_result(f"无效的坐标 ({x+1}, {y+1})。坐标范围应在 1-{game.width} 列, 1-{game.height} 行之间。")
             return

        if game.flagged[y][x]:
             yield event.plain_result(f"格子 ({x+1}, {y+1}) 已被标记，请先取消标记 (/扫雷 flag {x+1} {y+1})。")
             return

        if game.revealed[y][x]:
             yield event.plain_result(f"格子 ({x+1}, {y+1}) 已经被点开。")
             return

        logger.info(f"会话 {session_id}: 点击单元格 ({x+1}, {y+1})")
        changed = game.reveal_cell(x, y)

        if not changed:
             yield event.plain_result(f"无法点开格子 ({x+1}, {y+1})。")
             return

        message = ""
        if game.game_over:
            end_game(session_id)
            if game.won:
                message = "恭喜你，你赢了！ 🎉"
                logger.info(f"会话 {session_id}: 游戏胜利")
            else:
                message = "嘣！你踩到雷了！游戏结束。💥"
                logger.info(f"会话 {session_id}: 游戏失败")

        async for result in self._send_board(event, game, message):
            yield result

    @filter.command("扫雷 flag")
    async def flag_cell(self, event: AstrMessageEvent):
        """
        标记/取消标记一个格子作为雷。
        用法: /扫雷 flag [列号] [行号]
        示例: /扫雷 flag 1 1
        """
        session_id = event.get_session_id()
        game = get_game(session_id)

        if not game:
            yield event.plain_result("当前没有进行中的游戏。请使用 /扫雷 start 开始新游戏。")
            return

        if game.game_over:
             yield event.plain_result("游戏已经结束了！")
             return

        args_text = event.message_str.split("flag", 1)[-1].strip()
        coords = parse_coords(args_text)

        if not coords:
            yield event.plain_result("无效的坐标格式。请使用：/扫雷 flag [列号] [行号] (例如: /扫雷 flag 1 1)")
            return

        x, y = coords
        if not game._is_valid(x, y):
             yield event.plain_result(f"无效的坐标 ({x+1}, {y+1})。坐标范围应在 1-{game.width} 列, 1-{game.height} 行之间。")
             return

        if game.revealed[y][x]:
            yield event.plain_result(f"不能标记一个已经点开的格子 ({x+1}, {y+1})。")
            return

        logger.info(f"会话 {session_id}: 切换单元格 ({x+1}, {y+1}) 的标记状态")
        changed = game.flag_cell(x, y)

        if not changed:
             yield event.plain_result(f"无法标记/取消标记格子 ({x+1}, {y+1})。")
             return

        message = ""
        if game.game_over and game.won:
             end_game(session_id)
             message = "恭喜你，你赢了！ 🎉 (所有雷都被正确标记)"
             logger.info(f"会话 {session_id}: 通过标记获胜")

        async for result in self._send_board(event, game, message):
            yield result

    @filter.command("扫雷 end")
    async def end_current_game(self, event: AstrMessageEvent):
        """
        结束当前频道的扫雷游戏。
        """
        session_id = event.get_session_id()
        game = get_game(session_id)

        if not game:
            yield event.plain_result("当前没有进行中的游戏。")
            return

        end_game(session_id)
        logger.info(f"会话 {session_id}: 用户命令结束游戏")
        yield event.plain_result("当前扫雷游戏已结束。")

