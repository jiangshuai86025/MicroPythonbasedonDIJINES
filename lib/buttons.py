"""
MicroPyNES - 按钮输入驱动
==========================
管理 8 个游戏控制器按键，与 DIJI-NES 原始硬件完全兼容。

硬件连接: 所有按键使用 INPUT_PULLUP，按下为低电平 (0)。
提供两种读取模式:
  - 独立读取: 适合菜单导航等低频场景
  - 批量读取: 适合游戏循环中需要同时检测多键的场景
"""

import machine
import time
from lib.config import (
    BTN_A, BTN_B, BTN_SELECT, BTN_START,
    BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT,
    BTN_MASK_A, BTN_MASK_B, BTN_MASK_SELECT, BTN_MASK_START,
    BTN_MASK_UP, BTN_MASK_DOWN, BTN_MASK_LEFT, BTN_MASK_RIGHT
)


class Buttons:
    """
    游戏控制器按键管理

    用法:
        from lib.buttons import Buttons
        btn = Buttons()

        # 方式1: 独立读取
        if btn.is_pressed('A'):
            print("A 按下")

        # 方式2: 获取 NES 手柄状态字节 (兼容原项目编码)
        state = btn.read_nes_state()
        if state & BTN_MASK_UP:
            print("UP 按下")

        # 方式3: 带防抖的等待按键
        key = btn.wait_for_press()
    """

    # 按键名称到 GPIO 引脚的映射
    _PIN_MAP = {
        'A':      BTN_A,
        'B':      BTN_B,
        'SELECT': BTN_SELECT,
        'START':  BTN_START,
        'UP':     BTN_UP,
        'DOWN':   BTN_DOWN,
        'LEFT':   BTN_LEFT,
        'RIGHT':  BTN_RIGHT,
    }

    # 按键名称到位掩码的映射
    _MASK_MAP = {
        'A':      BTN_MASK_A,
        'B':      BTN_MASK_B,
        'SELECT': BTN_MASK_SELECT,
        'START':  BTN_MASK_START,
        'UP':     BTN_MASK_UP,
        'DOWN':   BTN_MASK_DOWN,
        'LEFT':   BTN_MASK_LEFT,
        'RIGHT':  BTN_MASK_RIGHT,
    }

    def __init__(self, debounce_ms=150):
        """
        初始化所有按键引脚

        参数:
            debounce_ms: 防抖时间 (毫秒)
        """
        self._pins = {}
        self._debounce_ms = debounce_ms
        self._last_press_time = 0

        for name, gpio in self._PIN_MAP.items():
            pin = machine.Pin(gpio, machine.Pin.IN, machine.Pin.PULL_UP)
            self._pins[name] = pin

        # 用于 just_pressed() 的上一帧状态
        self._prev_state = {}

    def is_pressed(self, name):
        """
        检测指定按键是否按下

        参数:
            name: 按键名称 ('A', 'B', 'SELECT', 'START', 'UP', 'DOWN', 'LEFT', 'RIGHT')

        返回:
            True 如果按下, False 如果松开
        """
        if name not in self._pins:
            return False
        return self._pins[name].value() == 0

    def just_pressed(self, name):
        """
        检测按键是否刚刚按下 (边沿触发)

        参数:
            name: 按键名称

        返回:
            True 仅在按键从松开变为按下的那一帧

        注意:
            每帧只能检测一次状态变化，
            不会因按键持续按住而重复触发。
        """
        current = self.is_pressed(name)
        prev = self._prev_state.get(name, False)
        self._prev_state[name] = current
        return current and not prev

    def read_nes_state(self):
        """
        读取所有按键状态，返回 NES 手柄标准编码字节

        编码 (与 DIJI-NES 原项目完全一致):
            bit 0 (0x01): A
            bit 1 (0x02): B
            bit 2 (0x04): SELECT
            bit 3 (0x08): START
            bit 4 (0x10): UP
            bit 5 (0x20): DOWN
            bit 6 (0x40): LEFT
            bit 7 (0x80): RIGHT

        返回:
            8-bit 按键状态字节
        """
        state = 0
        for name, pin in self._pins.items():
            if pin.value() == 0:  # 按下 (低电平)
                state |= self._MASK_MAP[name]
        return state

    def read_all(self):
        """
        读取所有按键状态为字典

        返回:
            字典 {按键名称: bool}，True 表示按下
        """
        return {name: pin.value() == 0 for name, pin in self._pins.items()}

    def any_pressed(self):
        """检测是否有任意按键按下"""
        for pin in self._pins.values():
            if pin.value() == 0:
                return True
        return False

    def wait_for_press(self, timeout_ms=None):
        """
        等待任意按键按下并返回按键名称

        参数:
            timeout_ms: 超时时间 (毫秒)，None 表示无限等待

        返回:
            按键名称字符串，超时返回 None
        """
        start = time.ticks_ms()
        while True:
            for name, pin in self._pins.items():
                if pin.value() == 0:
                    time.sleep_ms(50)  # 简单防抖
                    # 确认仍然按下
                    if pin.value() == 0:
                        # 等待释放
                        while pin.value() == 0:
                            time.sleep_ms(10)
                        return name
            if timeout_ms is not None:
                if time.ticks_diff(time.ticks_ms(), start) >= timeout_ms:
                    return None
            time.sleep_ms(10)

    def get_pressed_keys(self):
        """
        获取当前所有按下的按键名称列表

        返回:
            按键名称列表
        """
        pressed = []
        for name, pin in self._pins.items():
            if pin.value() == 0:
                pressed.append(name)
        return pressed

    def debounce_read(self):
        """
        带防抖的读取：在防抖时间内只返回第一次检测到的按键

        返回:
            新按下的按键名称列表，如果没有新按键则返回空列表
        """
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_press_time) < self._debounce_ms:
            return []

        pressed = self.get_pressed_keys()
        if pressed:
            self._last_press_time = now
        return pressed
