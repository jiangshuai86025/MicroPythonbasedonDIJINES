"""
MicroPyNES - 游戏引擎核心
===========================
提供游戏开发的基础框架，用户只需继承 Game 类并实现
init()、update()、draw() 三个方法即可创建游戏。

功能:
  - Game 基类 (游戏生命周期管理)
  - GameEngine (主循环、帧率控制、状态管理)
  - 碰撞检测工具
  - 随机数工具
  - 计时器工具
  - 向量/数学工具

设计原则:
  - 简单易用: 最少的代码即可创建可运行的游戏
  - 硬件无关: 游戏代码不直接操作 GPIO/SPI
  - 性能友好: 帧率控制、脏区域刷新
"""

import time
import urandom
from lib.display import Display, rgb565
from lib.buttons import Buttons
from lib.audio import Audio
from lib.config import TFT_WIDTH, TFT_HEIGHT


# ==================== 预定义颜色常量 ====================
BLACK   = 0x0000
WHITE   = 0xFFFF
RED     = 0xF800
GREEN   = 0x07E0
BLUE    = 0x001F
YELLOW  = 0xFFE0
CYAN    = 0x07FF
MAGENTA = 0xF81F
ORANGE  = 0xFD20
GRAY    = 0x8410
DARK_GRAY  = 0x4208
LIGHT_GRAY = 0xC618


class Game:
    """
    游戏基类 - 所有游戏必须继承此类

    生命周期:
        1. __init__() - 构造函数，设置游戏基本属性
        2. init()     - 初始化游戏资源 (每次开始游戏时调用)
        3. update(dt) - 更新游戏逻辑 (每帧调用)
        4. draw()     - 绘制游戏画面 (每帧调用)
        5. cleanup()  - 清理资源 (退出游戏时调用)

    子类必须实现:
        - init(): 初始化游戏状态
        - update(dt): 更新游戏逻辑，dt 为上一帧耗时 (秒)
        - draw(): 绘制当前帧到 display

    可选实现:
        - on_pause(): 游戏暂停时调用
        - on_resume(): 游戏恢复时调用
        - cleanup(): 退出时清理

    属性:
        display: Display 对象，用于绘图
        buttons: Buttons 对象，用于读取输入
        audio:   Audio 对象，用于播放音效
        name:    游戏名称
        running: 游戏是否在运行
        score:   当前分数 (可选使用)
        paused:  是否暂停
    """

    def __init__(self, name="Untitled"):
        """
        初始化游戏基础属性

        参数:
            name: 游戏名称
        """
        self.name = name
        self.display = None   # 由 GameEngine 注入
        self.buttons = None   # 由 GameEngine 注入
        self.audio = None     # 由 GameEngine 注入
        self.running = True   # 设为 False 退出游戏
        self.score = 0        # 当前分数
        self.paused = False   # 是否暂停
        self._return_to_menu = False  # 请求返回菜单

    def init(self):
        """
        初始化游戏 (必须实现)

        在这里设置初始游戏状态、加载资源等。
        每次开始新游戏时会调用此方法。
        """
        raise NotImplementedError("子类必须实现 init() 方法")

    def update(self, dt):
        """
        更新游戏逻辑 (必须实现)

        参数:
            dt: 上一帧到当前帧的时间差 (秒)

        在这里处理输入、更新游戏状态、碰撞检测等。
        """
        raise NotImplementedError("子类必须实现 update() 方法")

    def draw(self):
        """
        绘制游戏画面 (必须实现)

        使用 self.display 进行绘图操作。
        注意: draw() 结束后需要调用 self.display.show() 刷新到屏幕。
        """
        raise NotImplementedError("子类必须实现 draw() 方法")

    def cleanup(self):
        """清理游戏资源 (可选实现)"""
        pass

    def on_pause(self):
        """游戏暂停时调用 (可选实现)"""
        pass

    def on_resume(self):
        """游戏恢复时调用 (可选实现)"""
        pass

    def quit_game(self):
        """请求退出游戏，返回主菜单"""
        self._return_to_menu = True
        self.running = False

    def check_pause(self):
        """
        检测暂停组合键 (START + SELECT)

        在 update() 中调用此方法以支持暂停功能。
        """
        if self.buttons.is_pressed('START') and self.buttons.is_pressed('SELECT'):
            self.paused = not self.paused
            if self.paused:
                self.on_pause()
            else:
                self.on_resume()
            # 等待按键释放
            while self.buttons.is_pressed('START') or self.buttons.is_pressed('SELECT'):
                time.sleep_ms(20)
            time.sleep_ms(100)
            return True
        return False

    def show_pause_screen(self):
        """显示暂停画面覆盖层"""
        d = self.display
        # 半透明效果: 隔行黑色
        for y in range(0, TFT_HEIGHT, 2):
            d.hline(0, y, TFT_WIDTH, 0x0000)

        # 暂停框
        bx = 80
        by = 80
        bw = 160
        bh = 80
        d.fill_rect(bx, by, bw, bh, DARK_GRAY)
        d.rect(bx, by, bw, bh, WHITE)
        d.rect(bx + 1, by + 1, bw - 2, bh - 2, WHITE)

        d.text_center("PAUSED", by + 15, YELLOW, scale=2)
        d.text_center("START+SEL: Resume", by + 45, LIGHT_GRAY)
        d.text_center("B: Quit to Menu", by + 58, LIGHT_GRAY)
        d.show()


class GameEngine:
    """
    游戏引擎 - 管理游戏生命周期和主循环

    功能:
      - 初始化硬件 (显示、按键、音频)
      - 帧率控制
      - 游戏状态管理 (菜单、游戏中、暂停)
      - 内置游戏和用户游戏的加载与运行

    用法:
        from lib.engine import GameEngine
        engine = GameEngine()
        engine.register_game(MyGame())
        engine.run()  # 进入主循环
    """

    # 目标帧率
    TARGET_FPS = 30
    FRAME_TIME_MS = int(1000 / TARGET_FPS)

    def __init__(self):
        """初始化游戏引擎和所有硬件"""
        print("[Engine] 正在初始化硬件...")

        # 初始化硬件
        self.display = Display()
        self.buttons = Buttons()
        self.audio = Audio()

        # 游戏注册表
        self._games = []         # [(name, game_instance_or_loader), ...]
        self._current_game = None
        self._selected_index = 0
        self._scroll_offset = 0
        self._items_per_page = 8

        # 帧率统计
        self._fps = 0
        self._frame_count = 0
        self._fps_timer = time.ticks_ms()

        print("[Engine] 硬件初始化完成")

    def register_game(self, game):
        """
        注册一个游戏

        参数:
            game: Game 子类实例
        """
        self._games.append((game.name, game))

    def register_game_loader(self, name, loader_func):
        """
        注册一个游戏加载器 (延迟加载)

        参数:
            name: 游戏名称
            loader_func: 返回 Game 实例的函数
        """
        self._games.append((name, loader_func))

    def _draw_menu(self):
        """绘制主菜单"""
        d = self.display
        d.fill(DARK_GRAY)

        # 标题栏
        d.fill_rect(0, 0, TFT_WIDTH, 36, rgb565(40, 40, 60))
        d.rect(0, 0, TFT_WIDTH, 36, rgb565(80, 80, 120))
        d.text_center("MicroPyNES", 8, CYAN, scale=2)
        d.hline(10, 34, TFT_WIDTH - 20, rgb565(80, 80, 120))

        # 游戏列表
        if not self._games:
            d.text_center("No games registered", 100, LIGHT_GRAY)
            d.text_center("Add games to SD card", 120, LIGHT_GRAY)
        else:
            start_y = 44
            item_h = 22
            list_x = 20
            list_w = TFT_WIDTH - 40

            for i in range(self._items_per_page):
                idx = self._scroll_offset + i
                if idx >= len(self._games):
                    break

                y = start_y + i * item_h

                if idx == self._selected_index:
                    d.fill_rect(list_x, y, list_w, item_h - 2, YELLOW)
                    d.text(">", list_x + 4, y + 6, BLACK)
                    d.text(self._games[idx][0][:25], list_x + 16, y + 6, BLACK)
                    d.text("<", list_x + list_w - 16, y + 6, BLACK)
                else:
                    d.text(self._games[idx][0][:25], list_x + 16, y + 6, WHITE)

            # 页码
            if len(self._games) > self._items_per_page:
                total_pages = (len(self._games) + self._items_per_page - 1) // self._items_per_page
                current_page = self._scroll_offset // self._items_per_page + 1
                d.text("{}/{}".format(current_page, total_pages),
                       TFT_WIDTH - 50, start_y + self._items_per_page * item_h + 4, LIGHT_GRAY)

        # 底部提示
        d.fill_rect(0, TFT_HEIGHT - 24, TFT_WIDTH, 24, rgb565(40, 40, 60))
        d.hline(0, TFT_HEIGHT - 24, TFT_WIDTH, rgb565(80, 80, 120))
        d.text_center("UP/DOWN: Select   START: Play", TFT_HEIGHT - 16, LIGHT_GRAY)

        d.show()

    def _handle_menu_input(self):
        """处理菜单输入"""
        if not self._games:
            time.sleep_ms(100)
            return None

        if self.buttons.is_pressed('UP'):
            if self._selected_index > 0:
                self._selected_index -= 1
                if self._selected_index < self._scroll_offset:
                    self._scroll_offset = self._selected_index
                self.audio.snd_menu_move()
                self._draw_menu()
            while self.buttons.is_pressed('UP'):
                time.sleep_ms(20)

        elif self.buttons.is_pressed('DOWN'):
            if self._selected_index < len(self._games) - 1:
                self._selected_index += 1
                if self._selected_index >= self._scroll_offset + self._items_per_page:
                    self._scroll_offset = self._selected_index - self._items_per_page + 1
                self.audio.snd_menu_move()
                self._draw_menu()
            while self.buttons.is_pressed('DOWN'):
                time.sleep_ms(20)

        elif self.buttons.is_pressed('START') or self.buttons.is_pressed('A'):
            self.audio.snd_menu_select()
            time.sleep_ms(200)
            return self._selected_index

        return None

    def _run_game(self, game):
        """
        运行单个游戏

        参数:
            game: Game 实例
        """
        print("[Engine] 启动游戏:", game.name)

        # 注入硬件引用
        game.display = self.display
        game.buttons = self.buttons
        game.audio = self.audio

        # 初始化游戏
        game.running = True
        game._return_to_menu = False
        game.paused = False
        game.score = 0
        game.init()

        # 游戏主循环
        self.audio.snd_game_start()
        last_time = time.ticks_ms()
        self._fps = 0
        self._frame_count = 0
        self._fps_timer = last_time

        while game.running:
            frame_start = time.ticks_ms()

            # 计算 dt
            now = time.ticks_ms()
            dt = time.ticks_diff(now, last_time) / 1000.0
            last_time = now
            if dt > 0.1:  # 防止 dt 过大 (如暂停后恢复)
                dt = 0.1

            # 检测暂停
            if game.check_pause():
                if game.paused:
                    game.show_pause_screen()
                    # 等待恢复或退出
                    while game.paused and game.running:
                        if game.buttons.is_pressed('START') and game.buttons.is_pressed('SELECT'):
                            game.paused = False
                            game.on_resume()
                            while game.buttons.is_pressed('START') or game.buttons.is_pressed('SELECT'):
                                time.sleep_ms(20)
                        elif game.buttons.is_pressed('B'):
                            game.quit_game()
                        time.sleep_ms(50)
                    if game.running:
                        continue
                continue

            if not game.paused:
                # 更新游戏逻辑
                game.update(dt)

                # 绘制游戏画面
                game.draw()

                # 刷新到屏幕
                self.display.show()

            # 帧率控制
            elapsed = time.ticks_diff(time.ticks_ms(), frame_start)
            sleep_time = self.FRAME_TIME_MS - elapsed
            if sleep_time > 0:
                time.sleep_ms(sleep_time)

            # FPS 统计
            self._frame_count += 1
            if time.ticks_diff(time.ticks_ms(), self._fps_timer) >= 1000:
                self._fps = self._frame_count
                self._frame_count = 0
                self._fps_timer = time.ticks_ms()

        # 游戏结束
        game.cleanup()
        print("[Engine] 游戏结束:", game.name, "分数:", game.score)

    def run(self):
        """
        进入游戏引擎主循环 (菜单系统)

        此方法不会返回，持续运行菜单系统。
        """
        print("[Engine] 启动菜单系统")
        self._draw_menu()

        while True:
            selection = self._handle_menu_input()

            if selection is not None and selection < len(self._games):
                name, game_or_loader = self._games[selection]

                # 获取游戏实例
                if callable(game_or_loader) and not isinstance(game_or_loader, Game):
                    game = game_or_loader()
                else:
                    game = game_or_loader

                if isinstance(game, Game):
                    self._run_game(game)
                else:
                    print("[Engine] 无效的游戏对象:", name)

                # 返回菜单
                self._draw_menu()

            time.sleep_ms(30)
