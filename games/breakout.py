"""
MicroPyNES - 内置游戏: 打砖块 (Breakout)
==========================================
经典打砖块街机游戏。

操作:
  - LEFT/RIGHT: 移动挡板
  - A: 发射球 (开局时)
  - START+SELECT: 暂停/恢复

规则:
  - 球碰到砖块则消除砖块，得分
  - 球掉出底部则失去一条命
  - 3 条命用完则游戏结束
  - 消除所有砖块则胜利
"""

import urandom
from lib.engine import Game, WHITE, BLACK, RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA, LIGHT_GRAY
from lib.config import rgb565

# 游戏参数
PADDLE_W = 40          # 挡板宽度
PADDLE_H = 6           # 挡板高度
PADDLE_Y = 220         # 挡板 Y 坐标
PADDLE_SPEED = 200     # 挡板移动速度 (像素/秒)
BALL_SIZE = 4          # 球的大小
BALL_SPEED = 150       # 球的初始速度 (像素/秒)
BRICK_ROWS = 5         # 砖块行数
BRICK_COLS = 10        # 砖块列数
BRICK_W = 28           # 砖块宽度
BRICK_H = 10           # 砖块高度
BRICK_PAD = 2          # 砖块间距
BRICK_OFFSET_X = 18    # 砖块区域 X 偏移
BRICK_OFFSET_Y = 40    # 砖块区域 Y 偏移


class BreakoutGame(Game):
    """打砖块游戏"""

    def __init__(self):
        super().__init__("Breakout")

    def init(self):
        """初始化游戏状态"""
        # 挡板
        self.paddle_x = (320 - PADDLE_W) // 2

        # 球
        self.ball_x = 160.0
        self.ball_y = float(PADDLE_Y - BALL_SIZE - 2)
        self.ball_dx = 0.0
        self.ball_dy = 0.0
        self.ball_launched = False

        # 砖块: True = 存在, False = 已消除
        self.bricks = []
        for r in range(BRICK_ROWS):
            row = []
            for c in range(BRICK_COLS):
                row.append(True)
            self.bricks.append(row)

        # 砖块颜色 (每行不同)
        self.brick_colors = [
            rgb565(255, 80, 80),    # 红
            rgb565(255, 165, 0),    # 橙
            rgb565(255, 255, 0),    # 黄
            rgb565(0, 200, 0),      # 绿
            rgb565(80, 160, 255),   # 蓝
        ]

        # 游戏状态
        self.lives = 3
        self.score = 0
        self.ball_speed = BALL_SPEED
        self.game_over = False
        self.victory = False

    def _reset_ball(self):
        """重置球到挡板上方"""
        self.ball_x = self.paddle_x + PADDLE_W / 2.0 - BALL_SIZE / 2.0
        self.ball_y = float(PADDLE_Y - BALL_SIZE - 2)
        self.ball_dx = 0.0
        self.ball_dy = 0.0
        self.ball_launched = False

    def update(self, dt):
        """更新游戏逻辑"""
        if self.game_over or self.victory:
            # 等待重新开始
            if self.buttons.is_pressed('A') or self.buttons.is_pressed('START'):
                self.init()
            return

        # 移动挡板
        if self.buttons.is_pressed('LEFT'):
            self.paddle_x -= int(PADDLE_SPEED * dt)
        if self.buttons.is_pressed('RIGHT'):
            self.paddle_x += int(PADDLE_SPEED * dt)
        self.paddle_x = max(0, min(320 - PADDLE_W, self.paddle_x))

        # 发射球
        if not self.ball_launched:
            self.ball_x = self.paddle_x + PADDLE_W / 2.0 - BALL_SIZE / 2.0
            self.ball_y = float(PADDLE_Y - BALL_SIZE - 2)
            if self.buttons.is_pressed('A'):
                import math
                angle = -math.pi / 2 + (urandom.random() - 0.5) * 0.8
                self.ball_dx = self.ball_speed * math.cos(angle)
                self.ball_dy = self.ball_speed * math.sin(angle)
                self.ball_launched = True
            return

        # 更新球的位置
        self.ball_x += self.ball_dx * dt
        self.ball_y += self.ball_dy * dt

        bx = int(self.ball_x)
        by = int(self.ball_y)

        # 墙壁碰撞 (左右)
        if bx <= 0:
            self.ball_x = 0.0
            self.ball_dx = abs(self.ball_dx)
        elif bx >= 320 - BALL_SIZE:
            self.ball_x = float(320 - BALL_SIZE)
            self.ball_dx = -abs(self.ball_dx)

        # 天花板碰撞
        if by <= 0:
            self.ball_y = 0.0
            self.ball_dy = abs(self.ball_dy)

        # 挡板碰撞
        if (by + BALL_SIZE >= PADDLE_Y and by + BALL_SIZE <= PADDLE_Y + PADDLE_H
                and bx + BALL_SIZE >= self.paddle_x and bx <= self.paddle_x + PADDLE_W
                and self.ball_dy > 0):
            # 根据球击中挡板的位置调整反弹角度
            import math
            hit_pos = (bx + BALL_SIZE / 2 - self.paddle_x) / PADDLE_W  # 0~1
            angle = -math.pi / 2 + (hit_pos - 0.5) * 1.2
            speed = (self.ball_dx ** 2 + self.ball_dy ** 2) ** 0.5
            self.ball_dx = speed * math.cos(angle)
            self.ball_dy = speed * math.sin(angle)
            self.ball_y = float(PADDLE_Y - BALL_SIZE - 1)
            self.audio.beep(600, 30)

        # 砖块碰撞
        for r in range(BRICK_ROWS):
            for c in range(BRICK_COLS):
                if not self.bricks[r][c]:
                    continue
                brick_x = BRICK_OFFSET_X + c * (BRICK_W + BRICK_PAD)
                brick_y = BRICK_OFFSET_Y + r * (BRICK_H + BRICK_PAD)

                # 简单 AABB 碰撞
                if (bx + BALL_SIZE > brick_x and bx < brick_x + BRICK_W
                        and by + BALL_SIZE > brick_y and by < brick_y + BRICK_H):
                    self.bricks[r][c] = False
                    self.score += (BRICK_ROWS - r) * 10  # 上排分更高

                    # 确定反弹方向
                    overlap_left = bx + BALL_SIZE - brick_x
                    overlap_right = brick_x + BRICK_W - bx
                    overlap_top = by + BALL_SIZE - brick_y
                    overlap_bottom = brick_y + BRICK_H - by

                    min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                    if min_overlap in (overlap_left, overlap_right):
                        self.ball_dx = -self.ball_dx
                    else:
                        self.ball_dy = -self.ball_dy

                    self.audio.beep(800 + r * 100, 30)
                    self.ball_speed = min(300, self.ball_speed + 2)

                    # 检查胜利
                    if all(not self.bricks[r2][c2]
                           for r2 in range(BRICK_ROWS) for c2 in range(BRICK_COLS)):
                        self.victory = True
                    return

        # 球掉出底部
        if by > 240:
            self.lives -= 1
            self.audio.snd_hit()
            if self.lives <= 0:
                self.game_over = True
                self.audio.snd_game_over()
            else:
                self._reset_ball()

    def draw(self):
        """绘制游戏画面"""
        d = self.display
        d.fill(BLACK)

        # 顶部信息栏
        d.text("SCORE:{}".format(self.score), 10, 4, YELLOW)
        d.text("LIVES:", 200, 4, WHITE)
        for i in range(self.lives):
            d.fill_rect(250 + i * 12, 4, 8, 8, RED)

        # 砖块
        for r in range(BRICK_ROWS):
            for c in range(BRICK_COLS):
                if self.bricks[r][c]:
                    bx = BRICK_OFFSET_X + c * (BRICK_W + BRICK_PAD)
                    by = BRICK_OFFSET_Y + r * (BRICK_H + BRICK_PAD)
                    d.fill_rect(bx, by, BRICK_W, BRICK_H, self.brick_colors[r])
                    # 高光
                    d.hline(bx, by, BRICK_W, WHITE)
                    d.vline(bx, by, BRICK_H, WHITE)

        # 挡板
        d.fill_rect(self.paddle_x, PADDLE_Y, PADDLE_W, PADDLE_H, CYAN)
        d.hline(self.paddle_x, PADDLE_Y, PADDLE_W, WHITE)

        # 球
        d.fill_rect(int(self.ball_x), int(self.ball_y), BALL_SIZE, BALL_SIZE, WHITE)

        # 未发射提示
        if not self.ball_launched and not self.game_over and not self.victory:
            d.text_center("Press A to launch", 200, LIGHT_GRAY)

        # 游戏结束
        if self.game_over:
            for y in range(80, 160, 2):
                d.hline(0, y, 320, BLACK)
            d.text_center("GAME OVER", 100, RED, scale=2)
            d.text_center("Score: {}".format(self.score), 130, YELLOW)
            d.text_center("Press A to restart", 150, LIGHT_GRAY)

        # 胜利
        if self.victory:
            for y in range(80, 160, 2):
                d.hline(0, y, 320, BLACK)
            d.text_center("YOU WIN!", 100, GREEN, scale=2)
            d.text_center("Score: {}".format(self.score), 130, YELLOW)
            d.text_center("Press A to restart", 150, LIGHT_GRAY)
