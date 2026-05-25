"""
MicroPyNES - 内置游戏: 太空侵略者 (Space Invaders)
=====================================================
经典太空侵略者射击游戏。

操作:
  - LEFT/RIGHT: 移动飞船
  - A: 射击
  - START+SELECT: 暂停/恢复

规则:
  - 消灭外星人得分，上方外星人分值更高
  - 外星人会逐渐下移并加速
  - 被外星人子弹击中或外星人到达底部则游戏结束
"""

import urandom
from lib.engine import Game, WHITE, BLACK, RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA, LIGHT_GRAY
from lib.config import rgb565

# 游戏参数
PLAYER_W = 16          # 玩家飞船宽度
PLAYER_H = 8           # 玩家飞船高度
PLAYER_Y = 220         # 玩家 Y 坐标
PLAYER_SPEED = 120     # 移动速度 (像素/秒)
BULLET_W = 2           # 子弹宽度
BULLET_H = 6           # 子弹高度
BULLET_SPEED = 250     # 子弹速度
ENEMY_ROWS = 4         # 外星人行数
ENEMY_COLS = 8         # 外星人列数
ENEMY_W = 16           # 外星人宽度
ENEMY_H = 10           # 外星人高度
ENEMY_PAD_X = 4        # 外星人水平间距
ENEMY_PAD_Y = 4        # 外星人垂直间距
ENEMY_BASE_SPEED = 20  # 外星人基础移动速度
ENEMY_DROP = 8         # 外星人下移距离


class SpaceInvadersGame(Game):
    """太空侵略者游戏"""

    def __init__(self):
        super().__init__("Space Invaders")

    def init(self):
        """初始化游戏状态"""
        # 玩家
        self.player_x = (320 - PLAYER_W) // 2

        # 玩家子弹
        self.bullets = []  # [(x, y), ...]
        self.shoot_cooldown = 0.0

        # 敌人子弹
        self.enemy_bullets = []
        self.enemy_shoot_timer = 0.0

        # 外星人网格
        self.enemies = []
        for r in range(ENEMY_ROWS):
            for c in range(ENEMY_COLS):
                ex = 40 + c * (ENEMY_W + ENEMY_PAD_X)
                ey = 50 + r * (ENEMY_H + ENEMY_PAD_Y)
                self.enemies.append([ex, ey, True])  # [x, y, alive]

        # 外星人移动
        self.enemy_dir = 1   # 1=右, -1=左
        self.enemy_speed = ENEMY_BASE_SPEED
        self.enemy_move_timer = 0.0
        self.enemy_move_interval = 0.8  # 移动间隔 (秒)

        # 爆炸效果
        self.explosions = []  # [(x, y, timer), ...]

        # 游戏状态
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_over = False
        self.victory = False

    def _spawn_enemies(self):
        """生成新一波外星人"""
        self.enemies.clear()
        for r in range(ENEMY_ROWS):
            for c in range(ENEMY_COLS):
                ex = 40 + c * (ENEMY_W + ENEMY_PAD_X)
                ey = 50 + r * (ENEMY_H + ENEMY_PAD_Y)
                self.enemies.append([ex, ey, True])
        self.enemy_speed += 10
        self.enemy_move_interval = max(0.2, self.enemy_move_interval - 0.1)

    def _enemy_color(self, row):
        """返回不同行外星人的颜色"""
        colors = [
            rgb565(255, 50, 50),   # 红
            rgb565(255, 165, 0),   # 橙
            rgb565(50, 255, 50),   # 绿
            rgb565(50, 200, 255),  # 蓝
        ]
        return colors[row % len(colors)]

    def _draw_enemy(self, d, x, y, color):
        """绘制外星人精灵 (8x10 像素)"""
        # 简单的外星人图案
        pattern = [
            0b00100000,  #   #
            0b00010000,  #  #
            0b01111100,  # #####
            0b11011010,  # ## ## #
            0b11111110,  # #######
            0b01010100,  #  # # #
            0b01000100,  #  #   #
            0b00101000,  #   # #
            0b01000100,  #  #   #
            0b00101000,  #   # #
        ]
        for row in range(len(pattern)):
            for col in range(8):
                if pattern[row] & (1 << (7 - col)):
                    d.pixel(x + col * 2, y + row, color)
                    d.pixel(x + col * 2 + 1, y + row, color)

    def _draw_player(self, d, x, y):
        """绘制玩家飞船精灵"""
        color = CYAN
        # 简单的飞船图案
        pattern = [
            0b00001000,  #    #
            0b00011100,  #   ###
            0b00011100,  #   ###
            0b01111110,  # #######
            0b11111111,  # ########
            0b11111111,  # ########
            0b11111111,  # ########
            0b11111111,  # ########
        ]
        for row in range(len(pattern)):
            for col in range(8):
                if pattern[row] & (1 << (7 - col)):
                    d.pixel(x + col * 2, y + row, color)
                    d.pixel(x + col * 2 + 1, y + row, color)

    def update(self, dt):
        """更新游戏逻辑"""
        if self.game_over or self.victory:
            if self.buttons.is_pressed('A') or self.buttons.is_pressed('START'):
                self.init()
            return

        # 移动玩家
        if self.buttons.is_pressed('LEFT'):
            self.player_x -= int(PLAYER_SPEED * dt)
        if self.buttons.is_pressed('RIGHT'):
            self.player_x += int(PLAYER_SPEED * dt)
        self.player_x = max(0, min(320 - PLAYER_W, self.player_x))

        # 射击冷却
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt

        if self.buttons.is_pressed('A') and self.shoot_cooldown <= 0:
            bx = self.player_x + PLAYER_W // 2 - BULLET_W // 2
            by = PLAYER_Y - BULLET_H
            self.bullets.append([bx, by])
            self.shoot_cooldown = 0.2
            self.audio.snd_shoot()

        # 更新玩家子弹
        for bullet in self.bullets:
            bullet[1] -= BULLET_SPEED * dt
        self.bullets = [b for b in self.bullets if b[1] > -BULLET_H]

        # 更新敌人子弹
        for bullet in self.enemy_bullets:
            bullet[1] += 100 * dt
        self.enemy_bullets = [b for b in self.enemy_bullets if b[1] < 240]

        # 外星人移动
        self.enemy_move_timer += dt
        if self.enemy_move_timer >= self.enemy_move_interval:
            self.enemy_move_timer = 0.0

            # 检查是否需要下移
            need_drop = False
            for ex, ey, alive in self.enemies:
                if alive:
                    if ex + ENEMY_W >= 310 and self.enemy_dir > 0:
                        need_drop = True
                    if ex <= 10 and self.enemy_dir < 0:
                        need_drop = True
                    break

            if need_drop:
                self.enemy_dir *= -1
                for enemy in self.enemies:
                    enemy[1] += ENEMY_DROP
            else:
                move_amount = int(self.enemy_speed * self.enemy_move_interval)
                for enemy in self.enemies:
                    enemy[0] += move_amount * self.enemy_dir

        # 外星人射击
        self.enemy_shoot_timer += dt
        alive_enemies = [(ex, ey) for ex, ey, alive in self.enemies if alive]
        if alive_enemies and self.enemy_shoot_timer >= 1.0:
            self.enemy_shoot_timer = 0.0
            # 随机选择一个外星人射击
            idx = urandom.randint(0, len(alive_enemies) - 1)
            ex, ey = alive_enemies[idx]
            self.enemy_bullets.append([ex + ENEMY_W // 2, ey + ENEMY_H])

        # 子弹-外星人碰撞
        for bullet in self.bullets[:]:
            bx, by = bullet
            for enemy in self.enemies:
                ex, ey, alive = enemy
                if alive and (bx + BULLET_W > ex and bx < ex + ENEMY_W
                              and by + BULLET_H > ey and by < ey + ENEMY_H):
                    enemy[2] = False
                    self.explosions.append([ex, ey, 0.3])
                    if self.bullets.count(bullet) > 0:
                        self.bullets.remove(bullet)
                    # 分值: 上方行分更高
                    row = (ey - 50) // (ENEMY_H + ENEMY_PAD_Y)
                    self.score += max(10, (ENEMY_ROWS - row) * 20)
                    self.audio.beep(1000 + row * 200, 30)
                    break

        # 敌人子弹-玩家碰撞
        px_left = self.player_x
        px_right = self.player_x + PLAYER_W
        py_top = PLAYER_Y
        py_bottom = PLAYER_Y + PLAYER_H
        for bullet in self.enemy_bullets[:]:
            bx, by = bullet
            if (bx + BULLET_W > px_left and bx < px_right
                    and by + BULLET_H > py_top and by < py_bottom):
                self.enemy_bullets.remove(bullet)
                self.lives -= 1
                self.audio.snd_hit()
                if self.lives <= 0:
                    self.game_over = True
                    self.audio.snd_game_over()

        # 检查外星人是否到达底部
        for ex, ey, alive in self.enemies:
            if alive and ey + ENEMY_H >= PLAYER_Y:
                self.game_over = True
                self.audio.snd_game_over()
                break

        # 检查是否消灭所有外星人
        if not any(alive for _, _, alive in self.enemies):
            self.level += 1
            self._spawn_enemies()

        # 更新爆炸效果
        new_explosions = []
        for ex, ey, t in self.explosions:
            t -= dt
            if t > 0:
                new_explosions.append([ex, ey, t])
        self.explosions = new_explosions

    def draw(self):
        """绘制游戏画面"""
        d = self.display
        d.fill(BLACK)

        # 顶部信息
        d.text("SCORE:{}".format(self.score), 5, 4, YELLOW)
        d.text("LV:{}".format(self.level), 140, 4, CYAN)
        d.text("LIVES:", 230, 4, WHITE)
        for i in range(self.lives):
            d.fill_rect(275 + i * 10, 5, 6, 6, GREEN)

        # 底部分隔线
        d.hline(0, PLAYER_Y + PLAYER_H + 4, 320, rgb565(40, 40, 40))

        # 外星人
        for r in range(ENEMY_ROWS):
            for c in range(ENEMY_COLS):
                idx = r * ENEMY_COLS + c
                if idx < len(self.enemies) and self.enemies[idx][2]:
                    ex, ey = self.enemies[idx][0], self.enemies[idx][1]
                    self._draw_enemy(d, ex, ey, self._enemy_color(r))

        # 玩家飞船
        if not self.game_over:
            self._draw_player(d, self.player_x, PLAYER_Y)

        # 玩家子弹
        for bx, by in self.bullets:
            d.fill_rect(bx, by, BULLET_W, BULLET_H, YELLOW)

        # 敌人子弹
        for bx, by in self.enemy_bullets:
            d.fill_rect(bx, by, BULLET_W, BULLET_H, RED)

        # 爆炸效果
        for ex, ey, t in self.explosions:
            d.fill_rect(ex + 2, ey + 2, 4, 4, YELLOW)
            d.fill_rect(ex + 6, ey, 4, 4, rgb565(255, 165, 0))
            d.fill_rect(ex, ey + 4, 4, 4, RED)
            d.fill_rect(ex + 8, ey + 6, 4, 4, YELLOW)

        # 游戏结束
        if self.game_over:
            d.text_center("GAME OVER", 110, RED, scale=2)
            d.text_center("Score: {}".format(self.score), 140, YELLOW)
            d.text_center("Press A to restart", 165, LIGHT_GRAY)

        # 胜利
        if self.victory:
            d.text_center("YOU WIN!", 110, GREEN, scale=2)
            d.text_center("Score: {}".format(self.score), 140, YELLOW)
            d.text_center("Press A to restart", 165, LIGHT_GRAY)
