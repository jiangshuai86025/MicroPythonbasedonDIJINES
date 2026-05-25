"""
MicroPyNES - 内置游戏: 贪吃蛇 (Snake)
========================================
经典贪吃蛇游戏。

操作:
  - 方向键: 控制蛇的移动方向
  - START+SELECT: 暂停/恢复

规则:
  - 吃到食物蛇身变长，得分增加
  - 碰到墙壁或自身则游戏结束
"""

import urandom
from lib.engine import Game, GREEN, RED, WHITE, BLACK, YELLOW, DARK_GRAY, LIGHT_GRAY
from lib.config import rgb565

# 游戏区域参数
CELL_SIZE = 8          # 每个格子的像素大小
GRID_W = 30            # 网格宽度 (格子数)
GRID_H = 26            # 网格高度 (格子数)
OFFSET_X = 16          # X 偏移 (居中)
OFFSET_Y = 28          # Y 偏移 (留出分数区域)

# 蛇的移动间隔 (秒)，越小越快
INITIAL_SPEED = 0.15
SPEED_INCREASE = 0.002  # 每吃一个食物加速


class SnakeGame(Game):
    """贪吃蛇游戏"""

    def __init__(self):
        super().__init__("Snake")

    def init(self):
        """初始化游戏状态"""
        # 蛇身: 列表，每个元素为 (grid_x, grid_y)，索引 0 为蛇头
        start_x = GRID_W // 2
        start_y = GRID_H // 2
        self.snake = [
            (start_x, start_y),
            (start_x - 1, start_y),
            (start_x - 2, start_y),
        ]

        # 移动方向 (dx, dy)
        self.direction = (1, 0)
        self.next_direction = (1, 0)

        # 食物位置
        self.food = self._random_food()

        # 速度控制
        self.move_timer = 0.0
        self.move_interval = INITIAL_SPEED

        # 颜色
        self.color_bg = rgb565(10, 40, 10)       # 深绿背景
        self.color_grid = rgb565(15, 50, 15)     # 网格线
        self.color_snake_head = rgb565(0, 200, 0) # 蛇头亮绿
        self.color_snake_body = rgb565(0, 150, 0) # 蛇身绿
        self.color_food = rgb565(255, 50, 50)     # 食物红色
        self.color_wall = rgb565(80, 80, 80)      # 墙壁灰色

        self.score = 0
        self.game_over = False

    def _random_food(self):
        """生成随机食物位置 (不与蛇身重叠)"""
        attempts = 0
        while attempts < 200:
            fx = urandom.randint(0, GRID_W - 1)
            fy = urandom.randint(0, GRID_H - 1)
            if (fx, fy) not in self.snake:
                return (fx, fy)
            attempts += 1
        return (0, 0)

    def update(self, dt):
        """更新游戏逻辑"""
        # 检测方向输入 (不允许反向)
        if self.buttons.is_pressed('UP') and self.direction != (0, 1):
            self.next_direction = (0, -1)
        elif self.buttons.is_pressed('DOWN') and self.direction != (0, -1):
            self.next_direction = (0, 1)
        elif self.buttons.is_pressed('LEFT') and self.direction != (1, 0):
            self.next_direction = (-1, 0)
        elif self.buttons.is_pressed('RIGHT') and self.direction != (-1, 0):
            self.next_direction = (1, 0)

        # 移动计时
        self.move_timer += dt
        if self.move_timer < self.move_interval:
            return
        self.move_timer = 0.0

        # 应用方向
        self.direction = self.next_direction
        dx, dy = self.direction

        # 计算新蛇头位置
        head_x, head_y = self.snake[0]
        new_head = (head_x + dx, head_y + dy)

        # 碰撞检测: 墙壁
        nx, ny = new_head
        if nx < 0 or nx >= GRID_W or ny < 0 or ny >= GRID_H:
            self.game_over = True
            self.running = False
            self.audio.snd_game_over()
            return

        # 碰撞检测: 自身
        if new_head in self.snake:
            self.game_over = True
            self.running = False
            self.audio.snd_game_over()
            return

        # 移动蛇
        self.snake.insert(0, new_head)

        # 检查是否吃到食物
        if new_head == self.food:
            self.score += 10
            self.food = self._random_food()
            self.move_interval = max(0.05, self.move_interval - SPEED_INCREASE)
            self.audio.snd_score()
        else:
            # 没吃到食物，移除蛇尾
            self.snake.pop()

    def draw(self):
        """绘制游戏画面"""
        d = self.display

        # 清屏
        d.fill(BLACK)

        # 绘制分数
        d.text("SCORE: {}".format(self.score), 10, 8, YELLOW)

        # 绘制边框
        d.rect(OFFSET_X - 2, OFFSET_Y - 2,
               GRID_W * CELL_SIZE + 4, GRID_H * CELL_SIZE + 4,
               self.color_wall)

        # 绘制背景网格
        for gx in range(GRID_W):
            for gy in range(GRID_H):
                px = OFFSET_X + gx * CELL_SIZE
                py = OFFSET_Y + gy * CELL_SIZE
                d.fill_rect(px, py, CELL_SIZE, CELL_SIZE, self.color_bg)

        # 绘制食物
        fx, fy = self.food
        px = OFFSET_X + fx * CELL_SIZE
        py = OFFSET_Y + fy * CELL_SIZE
        d.fill_rect(px + 1, py + 1, CELL_SIZE - 2, CELL_SIZE - 2, self.color_food)
        # 食物上的小装饰
        d.fill_rect(px + 2, py + 2, 2, 2, YELLOW)

        # 绘制蛇
        for i, (sx, sy) in enumerate(self.snake):
            px = OFFSET_X + sx * CELL_SIZE
            py = OFFSET_Y + sy * CELL_SIZE
            color = self.color_snake_head if i == 0 else self.color_snake_body
            d.fill_rect(px + 1, py + 1, CELL_SIZE - 2, CELL_SIZE - 2, color)
            # 蛇头眼睛
            if i == 0:
                dx, dy = self.direction
                eye_color = BLACK
                if dx == 1:  # 向右
                    d.pixel(px + 6, py + 2, eye_color)
                    d.pixel(px + 6, py + 5, eye_color)
                elif dx == -1:  # 向左
                    d.pixel(px + 1, py + 2, eye_color)
                    d.pixel(px + 1, py + 5, eye_color)
                elif dy == -1:  # 向上
                    d.pixel(px + 2, py + 1, eye_color)
                    d.pixel(px + 5, py + 1, eye_color)
                else:  # 向下
                    d.pixel(px + 2, py + 6, eye_color)
                    d.pixel(px + 5, py + 6, eye_color)

        # 游戏结束画面
        if self.game_over:
            # 半透明遮罩
            for y in range(OFFSET_Y, OFFSET_Y + GRID_H * CELL_SIZE, 2):
                d.hline(OFFSET_X, y, GRID_W * CELL_SIZE, BLACK)

            d.text_center("GAME OVER", 100, RED, scale=2)
            d.text_center("Score: {}".format(self.score), 130, YELLOW)
            d.text_center("Press START", 160, LIGHT_GRAY)
