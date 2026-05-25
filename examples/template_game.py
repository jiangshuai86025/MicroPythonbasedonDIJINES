"""
MicroPyNES - 用户游戏模板
============================
将此文件复制到 SD 卡的 /games/ 目录下即可在菜单中显示。

使用方法:
  1. 复制此文件到 SD 卡: /sd/games/my_game.py
  2. 重命名为你喜欢的名字
  3. 修改下面的代码实现你的游戏
  4. 重启 ESP32，游戏会自动出现在菜单中

最小游戏只需要:
  - 继承 Game 类
  - 实现 init()、update(dt)、draw() 三个方法
"""

# 必须导入这些
from lib.engine import Game, WHITE, BLACK, RED, GREEN, BLUE, YELLOW, CYAN
from lib.config import rgb565


class MyGame(Game):
    """我的游戏 - 在这里写游戏描述"""

    def __init__(self):
        super().__init__("My Game")  # 设置游戏名称 (菜单中显示)

    def init(self):
        """
        初始化游戏状态

        在这里设置:
          - 玩家初始位置
          - 游戏变量 (分数、生命等)
          - 关卡数据
        """
        self.player_x = 160
        self.player_y = 120
        self.score = 0
        self.frame = 0

    def update(self, dt):
        """
        更新游戏逻辑

        参数:
            dt: 上一帧耗时 (秒)，如 dt=0.033 表示约 30FPS

        常用操作:
          - self.buttons.is_pressed('LEFT')   检测按键
          - self.audio.beep(440, 100)          播放音效
          - self.quit_game()                   返回菜单

        按键名称:
          'A', 'B', 'START', 'SELECT',
          'UP', 'DOWN', 'LEFT', 'RIGHT'
        """
        # 读取方向输入
        speed = 100  # 像素/秒
        if self.buttons.is_pressed('LEFT'):
            self.player_x -= speed * dt
        if self.buttons.is_pressed('RIGHT'):
            self.player_x += speed * dt
        if self.buttons.is_pressed('UP'):
            self.player_y -= speed * dt
        if self.buttons.is_pressed('DOWN'):
            self.player_y += speed * dt

        # 边界限制
        self.player_x = max(8, min(312, self.player_x))
        self.player_y = max(8, min(232, self.player_y))

        # 按 A 键播放音效
        if self.buttons.just_pressed('A'):
            self.score += 10
            self.audio.beep(800, 50)

        self.frame += 1

    def draw(self):
        """
        绘制游戏画面

        常用绘图方法:
          self.display.fill(color)                           清屏
          self.display.pixel(x, y, color)                    画点
          self.display.hline(x, y, w, color)                 水平线
          self.display.vline(x, y, h, color)                 垂直线
          self.display.line(x1, y1, x2, y2, color)           斜线
          self.display.rect(x, y, w, h, color)               空心矩形
          self.display.fill_rect(x, y, w, h, color)          实心矩形
          self.display.circle(cx, cy, r, color)              空心圆
          self.display.fill_circle(cx, cy, r, color)         实心圆
          self.display.text(str, x, y, color, scale=1)       文字
          self.display.text_center(str, y, color, scale=1)   居中文字
          self.display.blit(buf, x, y, w, h)                 绘制缓冲区
          self.display.show()                                刷新到屏幕

        预定义颜色:
          BLACK, WHITE, RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA
          也可以用 rgb565(r, g, b) 自定义颜色 (0-255)
        """
        # 清屏
        self.display.fill(BLACK)

        # 显示分数
        self.display.text("Score: {}".format(self.score), 10, 10, YELLOW)

        # 绘制玩家 (一个彩色方块)
        px = int(self.player_x)
        py = int(self.player_y)
        self.display.fill_rect(px - 8, py - 8, 16, 16, CYAN)
        self.display.rect(px - 8, py - 8, 16, 16, WHITE)

        # 操作提示
        self.display.text_center("D-Pad: Move   A: Score", 225, WHITE)


def create_game():
    """
    可选的工厂函数 (另一种注册游戏的方式)

    如果不想使用类继承方式，可以在 .py 文件中定义
    create_game() 函数，返回一个 Game 实例。
    """
    return MyGame()


# ============================================================
# 你也可以不使用类，而用函数方式创建简单游戏:
#
# from lib.engine import Game
#
# class SimpleGame(Game):
#     def __init__(self):
#         super().__init__("Simple")
#     def init(self):
#         self.x = 0
#     def update(self, dt):
#         if self.buttons.is_pressed('RIGHT'):
#             self.x += 1
#     def draw(self):
#         self.display.fill(0)
#         self.display.fill_rect(self.x, 100, 20, 20, 0x07E0)
#         self.display.show()
#
# ============================================================
