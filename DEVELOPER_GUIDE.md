# 游戏开发框架指南

## 概述

MicroPyNES 提供了一个简洁的游戏开发框架。你只需编写一个 Python 类，实现 3 个方法，就可以在 ESP32-S3 上运行自己的游戏。

## 快速开始

### 最小游戏

```python
from lib.engine import Game, BLACK, CYAN, YELLOW, WHITE

class HelloGame(Game):
    def __init__(self):
        super().__init__("Hello World")

    def init(self):
        self.x = 160
        self.y = 120

    def update(self, dt):
        if self.buttons.is_pressed('LEFT'):
            self.x -= 80 * dt
        if self.buttons.is_pressed('RIGHT'):
            self.x += 80 * dt
        if self.buttons.is_pressed('UP'):
            self.y -= 80 * dt
        if self.buttons.is_pressed('DOWN'):
            self.y += 80 * dt

    def draw(self):
        self.display.fill(BLACK)
        self.display.fill_rect(int(self.x) - 8, int(self.y) - 8, 16, 16, CYAN)
        self.display.text("Hello MicroPyNES!", 80, 10, YELLOW)
        self.display.show()
```

将此代码保存为 `.py` 文件，放入 SD 卡的 `/games/` 目录，重启 ESP32 即可。

---

## Game 类参考

### 生命周期

```
__init__()  →  init()  →  update(dt) + draw() [循环]  →  cleanup()
   ↑              ↑              ↑                           ↑
 创建实例      开始游戏        每帧调用                   退出游戏
```

### 必须实现的方法

#### `init(self)`
初始化游戏状态。在游戏开始时调用一次。
```python
def init(self):
    self.score = 0
    self.lives = 3
    self.player_x = 160
    self.player_y = 120
```

#### `update(self, dt)`
更新游戏逻辑。每帧调用一次。
```python
def update(self, dt):
    # dt = 上一帧耗时 (秒)，通常 0.033 (30FPS)
    speed = 100  # 像素/秒
    if self.buttons.is_pressed('LEFT'):
        self.player_x -= speed * dt
```

#### `draw(self)`
绘制游戏画面。每帧调用一次，紧跟 update() 之后。
```python
def draw(self):
    self.display.fill(BLACK)  # 清屏
    self.display.fill_rect(100, 100, 20, 20, RED)  # 画方块
    self.display.show()  # 刷新到屏幕
```

### 可选实现的方法

#### `cleanup(self)`
游戏退出时调用，用于清理资源。

#### `on_pause(self)` / `on_resume(self)`
游戏暂停/恢复时调用。

### Game 类属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `self.display` | Display | 显示驱动，用于绘图 |
| `self.buttons` | Buttons | 按键驱动，用于读取输入 |
| `self.audio` | Audio | 音频驱动，用于播放音效 |
| `self.name` | str | 游戏名称 |
| `self.running` | bool | 设为 False 退出游戏 |
| `self.score` | int | 当前分数 |
| `self.paused` | bool | 是否暂停 |

### Game 类方法

| 方法 | 说明 |
|------|------|
| `self.quit_game()` | 退出游戏，返回主菜单 |
| `self.check_pause()` | 检测暂停组合键 (START+SELECT) |

---

## 按键输入

### 按键名称

| 名称 | 对应功能 |
|------|----------|
| `'A'` | A 按钮 |
| `'B'` | B 按钮 |
| `'START'` | 开始 |
| `'SELECT'` | 选择 |
| `'UP'` | 上 |
| `'DOWN'` | 下 |
| `'LEFT'` | 左 |
| `'RIGHT'` | 右 |

### 按键检测方法

```python
# 持续按住检测 (每帧都会返回 True)
if self.buttons.is_pressed('A'):
    ...

# 边沿触发 (仅在按下那一帧返回 True)
if self.buttons.just_pressed('A'):
    ...

# 等待任意按键按下 (阻塞)
key = self.buttons.wait_for_press()
```

---

## 绘图 API

所有绘图操作通过 `self.display` 对象完成。

### 基础绘图

```python
# 清屏 (用指定颜色填充整个屏幕)
self.display.fill(BLACK)

# 画像素点
self.display.pixel(x, y, color)

# 画线
self.display.hline(x, y, width, color)      # 水平线
self.display.vline(x, y, height, color)      # 垂直线
self.display.line(x1, y1, x2, y2, color)     # 任意斜线

# 画矩形
self.display.rect(x, y, w, h, color)         # 空心
self.display.fill_rect(x, y, w, h, color)    # 实心

# 画圆
self.display.circle(cx, cy, radius, color)   # 空心
self.display.fill_circle(cx, cy, radius, color)  # 实心
```

### 文字渲染

```python
# 基本文字 (左对齐)
self.display.text("Hello", x, y, color)

# 缩放文字 (scale=2 表示放大 2 倍)
self.display.text("Big", x, y, color, scale=2)

# 居中文字
self.display.text_center("Centered", y, color)
self.display.text_center("Big Centered", y, color, scale=2)
```

### 精灵绘制

```python
# 从字节数组绘制精灵 (RGB565 格式)
# buf 是一个 bytearray，每个像素 2 字节
self.display.blit(buf, x, y, width, height)
```

### 预定义颜色

```python
from lib.engine import (
    BLACK, WHITE, RED, GREEN, BLUE,
    YELLOW, CYAN, MAGENTA, ORANGE,
    GRAY, DARK_GRAY, LIGHT_GRAY
)

# 自定义颜色 (RGB 各分量 0-255)
from lib.config import rgb565
my_color = rgb565(255, 128, 0)  # 橙色
```

### 刷新屏幕

```python
# 所有绘图操作都是写入内存缓冲区
# 调用 show() 才会刷新到实际屏幕
self.display.show()
```

**重要**: 每帧结束时必须调用 `self.display.show()`，否则画面不会更新。

---

## 音效系统

```python
# 播放简单音调
self.audio.beep(440, 100)   # 440Hz, 持续 100ms

# 播放预设音效
self.audio.snd_score()      # 得分音效
self.audio.snd_hit()        # 命中音效
self.audio.snd_shoot()      # 射击音效
self.audio.snd_game_over()  # 游戏结束音效
self.audio.snd_game_start() # 游戏开始音效
self.audio.snd_menu_move()  # 菜单移动音效
self.audio.snd_menu_select()# 菜单选择音效

# 播放旋律
self.audio.play_melody([
    (523, 200),  # C5, 200ms
    (587, 200),  # D5, 200ms
    (659, 200),  # E5, 200ms
])
```

---

## SD 卡游戏部署

### 文件结构

```
SD卡/
├── games/           ← 推荐的游戏目录
│   ├── my_game.py
│   └── another_game.py
├── game1.py         ← 根目录的游戏也会被扫描
└── ...
```

### 游戏注册方式

**方式一: 类继承 (推荐)**

```python
from lib.engine import Game

class MyGame(Game):
    def __init__(self):
        super().__init__("游戏名称")

    def init(self): ...
    def update(self, dt): ...
    def draw(self): ...
```

系统会自动查找继承了 `Game` 的子类并实例化。

**方式二: 工厂函数**

```python
from lib.engine import Game

class MyGame(Game):
    ...

def create_game():
    return MyGame()
```

系统会调用 `create_game()` 函数获取游戏实例。

---

## 性能优化建议

### 1. 使用整数运算

MicroPython 的浮点运算较慢，尽量使用整数：
```python
# 慢
self.x += 1.5 * dt

# 快 (用整数像素坐标)
self.x += int(speed * dt)
```

### 2. 减少 draw() 中的计算

```python
def update(self, dt):
    # 在 update 中计算好坐标
    self._px = int(self.x)
    self._py = int(self.y)

def draw(self):
    # draw 中直接使用缓存值
    self.display.fill_rect(self._px, self._py, 16, 16, CYAN)
```

### 3. 局部变量比属性快

```python
def draw(self):
    d = self.display  # 局部引用更快
    d.fill(BLACK)
    d.text("Score", 10, 10, YELLOW)
    d.show()
```

### 4. 避免在游戏循环中创建对象

```python
# 不好 - 每帧创建新列表
def update(self, dt):
    self.items = [x for x in self.items if x.active]

# 更好 - 原地修改
def update(self, dt):
    i = 0
    while i < len(self.items):
        if not self.items[i].active:
            self.items.pop(i)
        else:
            i += 1
```

---

## 完整示例: 弹球游戏

```python
from lib.engine import Game, BLACK, WHITE, RED, GREEN, YELLOW, CYAN
import urandom

class PongGame(Game):
    def __init__(self):
        super().__init__("Pong")

    def init(self):
        self.paddle_y = 100
        self.ball_x = 160.0
        self.ball_y = 120.0
        self.ball_dx = 80.0
        self.ball_dy = 60.0
        self.score = 0

    def update(self, dt):
        # 移动挡板
        if self.buttons.is_pressed('UP'):
            self.paddle_y -= 100 * dt
        if self.buttons.is_pressed('DOWN'):
            self.paddle_y += 100 * dt
        self.paddle_y = max(0, min(190, self.paddle_y))

        # 更新球
        self.ball_x += self.ball_dx * dt
        self.ball_y += self.ball_dy * dt

        # 碰撞: 上下墙
        if self.ball_y <= 0 or self.ball_y >= 236:
            self.ball_dy = -self.ball_dy

        # 碰撞: 挡板
        if (self.ball_x <= 20 and
            self.paddle_y <= self.ball_y <= self.paddle_y + 50):
            self.ball_dx = abs(self.ball_dx)
            self.score += 1
            self.audio.beep(600, 30)

        # 球出界
        if self.ball_x < 0:
            self.ball_x = 160.0
            self.ball_y = 120.0
            self.score = 0

        # 碰撞: 右墙
        if self.ball_x >= 316:
            self.ball_dx = -abs(self.ball_dx)

    def draw(self):
        d = self.display
        d.fill(BLACK)
        d.text("Score: {}".format(self.score), 10, 10, YELLOW)
        d.fill_rect(10, int(self.paddle_y), 6, 50, CYAN)
        d.fill_rect(int(self.ball_x), int(self.ball_y), 4, 4, WHITE)
        d.show()
```

---

## 屏幕坐标系

```
(0,0) ──────────────────── (319,0)
  │                           │
  │     320 × 240 像素        │
  │     RGB565 (16位色)       │
  │                           │
(0,239) ──────────────── (319,239)
```

- 原点在左上角
- X 轴向右 (0-319)
- Y 轴向下 (0-239)
