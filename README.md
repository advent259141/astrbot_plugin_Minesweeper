
</div>

<div align="center">

![:name](https://count.getloli.com/@Minesweeper?name=Minesweeper&theme=miku&padding=7&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)

</div>

# AstrBot 扫雷插件 (Minesweeper Plugin)

这是一个扫雷游戏插件，允许用户在聊天中玩经典的扫雷游戏。游戏界面使用 Pillow 库渲染成图片发送。

## ✨ 功能

*   经典的扫雷游戏玩法。
*   通过聊天命令进行交互。
*   使用 Pillow 库生成图像化游戏界面，**带有坐标标注**。
*   支持三种预设难度：
    *   **简单**: 9x9 棋盘，10 个雷
    *   **普通**: 16x16 棋盘，40 个雷
    *   **困难**: 30x16 棋盘，99 个雷
*   每个聊天会话（私聊/群聊）独立维护游戏状态。


## 🚀 使用方法

*   **开始游戏**: `/扫雷 start [难度]`
    *   开始一个新的扫雷游戏。
    *   `[难度]` 是可选参数，可以是 `简单`、`普通`、`困难`。
    *   如果未指定难度，默认为 `普通`。
    *   示例:
        *   `/扫雷 start` (开始普通难度游戏)
        *   `/扫雷 start 简单`
        *   `/扫雷 start 困难`

*   **点击格子**: `/扫雷 click [列号] [行号]`
    *   揭开指定坐标的格子。坐标从 1 开始计数。
    *   示例: `/扫雷 click 3 5` (点击第 3 列，第 5 行的格子)

*   **标记/取消标记**: `/扫雷 flag [列号] [行号]`
    *   在指定坐标的格子上放置或移除旗帜标记。坐标从 1 开始计数。
    *   示例: `/扫雷 flag 1 1` (标记/取消标记左上角的格子)

*   **结束游戏**: `/扫雷 end`
    *   提前结束当前聊天会话中的扫雷游戏。

*   **查看帮助**: `/扫雷 help`
    *   显示插件的命令帮助信息。


## 📄 许可证

MIT License。
