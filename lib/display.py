"""
MicroPyNES - ST7789 TFT 显示驱动
=================================
针对 ESP32-S3 + ST7789 320x240 SPI 显示屏的驱动实现。
与 DIJI-NES 原始硬件引脚配置完全兼容。

功能:
  - SPI 初始化与 ST7789 命令序列
  - 帧缓冲区 (framebuffer) 支持，避免逐像素 SPI 写入
  - 基础绘图: 像素、矩形、线条、圆形
  - 文字渲染 (内置 5x8 像素字体)
  - 精灵绘制 (带透明色支持)
  - 整屏刷新与局部刷新
"""

import machine
import time
import struct
from lib.config import (
    TFT_SCLK, TFT_MOSI, TFT_DC, TFT_CS, TFT_RST,
    TFT_SPI_ID, TFT_FREQ, TFT_WIDTH, TFT_HEIGHT, TFT_INVERT,
    rgb565
)

# ==================== ST7789 命令定义 ====================
_ST7789_SWRESET   = 0x01
_ST7789_SLPOUT    = 0x11
_ST7789_NORON     = 0x13
_ST7789_INVON     = 0x21
_ST7789_INVOFF    = 0x20
_ST7789_DISPON    = 0x29
_ST7789_CASET     = 0x2A
_ST7789_RASET     = 0x2B
_ST7789_RAMWR     = 0x2C
_ST7789_MADCTL    = 0x36
_ST7789_COLMOD    = 0x3A
_ST7789_PORCTRL   = 0xB2
_ST7789_GCTRL     = 0xB7
_ST7789_VCOMS     = 0xBB
_ST7789_LCMCTRL   = 0xC0
_ST7789_VDVVRHEN  = 0xC2
_ST7789_VRHS      = 0xC3
_ST7789_VDVS      = 0xC4
_ST7789_FRCTRL2   = 0xC6
_ST7789_PWCTRL1   = 0xD0
_ST7789_PVGAMCTRL = 0xE0
_ST7789_NVGAMCTRL = 0xE1

# MADCTL 标志位
_MADCTL_MY  = 0x80
_MADCTL_MX  = 0x40
_MADCTL_MV  = 0x20
_MADCTL_ML  = 0x10
_MADCTL_RGB = 0x00
_MADCTL_BGR = 0x08

# ==================== 内置 5x8 ASCII 字体 ====================
# 覆盖 ASCII 32 (空格) 到 126 (~)，每个字符 5 字节，列扫描格式
_FONT_5X8 = (
    b'\x00\x00\x00\x00\x00'  # 32 (space)
    b'\x00\x00\x5F\x00\x00'  # 33 !
    b'\x00\x07\x00\x07\x00'  # 34 "
    b'\x14\x7F\x14\x7F\x14'  # 35 #
    b'\x24\x2A\x7F\x2A\x12'  # 36 $
    b'\x23\x13\x08\x64\x62'  # 37 %
    b'\x36\x49\x55\x22\x50'  # 38 &
    b'\x00\x05\x03\x00\x00'  # 39 '
    b'\x00\x1C\x22\x41\x00'  # 40 (
    b'\x00\x41\x22\x1C\x00'  # 41 )
    b'\x08\x2A\x1C\x2A\x08'  # 42 *
    b'\x08\x08\x3E\x08\x08'  # 43 +
    b'\x00\x50\x30\x00\x00'  # 44 ,
    b'\x08\x08\x08\x08\x08'  # 45 -
    b'\x00\x60\x60\x00\x00'  # 46 .
    b'\x20\x10\x08\x04\x02'  # 47 /
    b'\x3E\x51\x49\x45\x3E'  # 48 0
    b'\x00\x42\x7F\x40\x00'  # 49 1
    b'\x42\x61\x51\x49\x46'  # 50 2
    b'\x21\x41\x45\x4B\x31'  # 51 3
    b'\x18\x14\x12\x7F\x10'  # 52 4
    b'\x27\x45\x45\x45\x39'  # 53 5
    b'\x3C\x4A\x49\x49\x30'  # 54 6
    b'\x01\x71\x09\x05\x03'  # 55 7
    b'\x36\x49\x49\x49\x36'  # 56 8
    b'\x06\x49\x49\x29\x1E'  # 57 9
    b'\x00\x36\x36\x00\x00'  # 58 :
    b'\x00\x56\x36\x00\x00'  # 59 ;
    b'\x00\x08\x14\x22\x41'  # 60 <
    b'\x14\x14\x14\x14\x14'  # 61 =
    b'\x41\x22\x14\x08\x00'  # 62 >
    b'\x02\x01\x51\x09\x06'  # 63 ?
    b'\x32\x49\x79\x41\x3E'  # 64 @
    b'\x7E\x11\x11\x11\x7E'  # 65 A
    b'\x7F\x49\x49\x49\x36'  # 66 B
    b'\x3E\x41\x41\x41\x22'  # 67 C
    b'\x7F\x41\x41\x22\x1C'  # 68 D
    b'\x7F\x49\x49\x49\x41'  # 69 E
    b'\x7F\x09\x09\x01\x01'  # 70 F
    b'\x3E\x41\x41\x51\x32'  # 71 G
    b'\x7F\x08\x08\x08\x7F'  # 72 H
    b'\x00\x41\x7F\x41\x00'  # 73 I
    b'\x20\x40\x41\x3F\x01'  # 74 J
    b'\x7F\x08\x14\x22\x41'  # 75 K
    b'\x7F\x40\x40\x40\x40'  # 76 L
    b'\x7F\x02\x04\x02\x7F'  # 77 M
    b'\x7F\x04\x08\x10\x7F'  # 78 N
    b'\x3E\x41\x41\x41\x3E'  # 79 O
    b'\x7F\x09\x09\x09\x06'  # 80 P
    b'\x3E\x41\x51\x21\x5E'  # 81 Q
    b'\x7F\x09\x19\x29\x46'  # 82 R
    b'\x46\x49\x49\x49\x31'  # 83 S
    b'\x01\x01\x7F\x01\x01'  # 84 T
    b'\x3F\x40\x40\x40\x3F'  # 85 U
    b'\x1F\x20\x40\x20\x1F'  # 86 V
    b'\x7F\x20\x18\x20\x7F'  # 87 W
    b'\x63\x14\x08\x14\x63'  # 88 X
    b'\x03\x04\x78\x04\x03'  # 89 Y
    b'\x61\x51\x49\x45\x43'  # 90 Z
    b'\x00\x00\x7F\x41\x41'  # 91 [
    b'\x02\x04\x08\x10\x20'  # 92 backslash
    b'\x41\x41\x7F\x00\x00'  # 93 ]
    b'\x04\x02\x01\x02\x04'  # 94 ^
    b'\x40\x40\x40\x40\x40'  # 95 _
    b'\x00\x01\x02\x04\x00'  # 96 `
    b'\x20\x54\x54\x54\x78'  # 97 a
    b'\x7F\x48\x44\x44\x38'  # 98 b
    b'\x38\x44\x44\x44\x20'  # 99 c
    b'\x38\x44\x44\x48\x7F'  # 100 d
    b'\x38\x54\x54\x54\x18'  # 101 e
    b'\x08\x7E\x09\x01\x02'  # 102 f
    b'\x08\x54\x54\x54\x3C'  # 103 g
    b'\x7F\x08\x04\x04\x78'  # 104 h
    b'\x00\x44\x7D\x40\x00'  # 105 i
    b'\x20\x40\x44\x3D\x00'  # 106 j
    b'\x00\x7F\x10\x28\x44'  # 107 k
    b'\x00\x41\x7F\x40\x00'  # 108 l
    b'\x7C\x04\x18\x04\x78'  # 109 m
    b'\x7C\x08\x04\x04\x78'  # 110 n
    b'\x38\x44\x44\x44\x38'  # 111 o
    b'\x7C\x14\x14\x14\x08'  # 112 p
    b'\x08\x14\x14\x18\x7C'  # 113 q
    b'\x7C\x08\x04\x04\x08'  # 114 r
    b'\x48\x54\x54\x54\x20'  # 115 s
    b'\x04\x3F\x44\x40\x20'  # 116 t
    b'\x3C\x40\x40\x20\x7C'  # 117 u
    b'\x1C\x20\x40\x20\x1C'  # 118 v
    b'\x3C\x40\x30\x40\x3C'  # 119 w
    b'\x44\x28\x10\x28\x44'  # 120 x
    b'\x0C\x50\x50\x50\x3C'  # 121 y
    b'\x44\x64\x54\x4C\x44'  # 122 z
    b'\x00\x08\x36\x41\x00'  # 123 {
    b'\x00\x00\x7F\x00\x00'  # 124 |
    b'\x00\x41\x36\x08\x00'  # 125 }
    b'\x08\x08\x2A\x1C\x08'  # 126 ~
)


class Display:
    """
    ST7789 TFT 显示驱动

    使用内部帧缓冲区 (RGB565)，支持批量刷新以获得较高帧率。

    用法:
        from lib.display import Display
        disp = Display()
        disp.fill(0x0000)         # 清屏为黑色
        disp.pixel(160, 120, 0xFFFF)  # 在中心画白色像素
        disp.text("Hello!", 10, 10, rgb565(255, 255, 0))
        disp.show()               # 刷新到屏幕
    """

    def __init__(self):
        self.width = TFT_WIDTH
        self.height = TFT_HEIGHT
        # 帧缓冲区: 宽度 x 高度 x 2 字节 (RGB565)
        self._buf = bytearray(self.width * self.height * 2)
        self._mv = memoryview(self._buf)

        # 初始化 SPI
        self._spi = machine.SPI(
            TFT_SPI_ID,
            baudrate=TFT_FREQ,
            polarity=0,
            phase=0,
            sck=machine.Pin(TFT_SCLK),
            mosi=machine.Pin(TFT_MOSI),
            miso=None
        )

        # 初始化控制引脚
        self._dc = machine.Pin(TFT_DC, machine.Pin.OUT)
        self._cs = machine.Pin(TFT_CS, machine.Pin.OUT)
        self._rst = machine.Pin(TFT_RST, machine.Pin.OUT)

        # 复位并初始化 ST7789
        self._init_display()

    def _write_cmd(self, cmd):
        """发送命令字节"""
        self._dc.value(0)
        self._cs.value(0)
        self._spi.write(bytes([cmd]))
        self._cs.value(1)

    def _write_data(self, data):
        """发送数据字节"""
        self._dc.value(1)
        self._cs.value(0)
        if isinstance(data, int):
            self._spi.write(bytes([data]))
        else:
            self._spi.write(data)
        self._cs.value(1)

    def _write_cmd_data(self, cmd, data):
        """发送命令 + 数据"""
        self._write_cmd(cmd)
        self._write_data(data)

    def _init_display(self):
        """ST7789 初始化序列"""
        # 硬件复位
        self._rst.value(1)
        time.sleep_ms(50)
        self._rst.value(0)
        time.sleep_ms(50)
        self._rst.value(1)
        time.sleep_ms(150)

        self._write_cmd(_ST7789_SWRESET)
        time.sleep_ms(150)

        self._write_cmd(_ST7789_SLPOUT)
        time.sleep_ms(50)

        # 像素格式: 16bit RGB565
        self._write_cmd_data(_ST7789_COLMOD, bytes([0x55]))

        # Porch 设置
        self._write_cmd_data(_ST7789_PORCTRL, bytes([0x0C, 0x0C, 0x00, 0x33, 0x33]))

        # Gate 控制
        self._write_cmd_data(_ST7789_GCTRL, bytes([0x35]))

        # VCOM 设置
        self._write_cmd_data(_ST7789_VCOMS, bytes([0x19]))

        # LCM 控制
        self._write_cmd_data(_ST7789_LCMCTRL, bytes([0x2C]))

        # VDV/VRH 使能
        self._write_cmd_data(_ST7789_VDVVRHEN, bytes([0x01]))

        # VRH 设置
        self._write_cmd_data(_ST7789_VRHS, bytes([0x12]))

        # VDV 设置
        self._write_cmd_data(_ST7789_VDVS, bytes([0x20]))

        # 帧率控制: 60Hz
        self._write_cmd_data(_ST7789_FRCTRL2, bytes([0x0F]))

        # 电源控制
        self._write_cmd_data(_ST7789_PWCTRL1, bytes([0xA4, 0xA1]))

        # Gamma 正向
        self._write_cmd_data(_ST7789_PVGAMCTRL, bytes([
            0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F,
            0x54, 0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23
        ]))

        # Gamma 反向
        self._write_cmd_data(_ST7789_NVGAMCTRL, bytes([
            0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F,
            0x44, 0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23
        ]))

        # 颜色反转 (与原项目一致)
        if TFT_INVERT:
            self._write_cmd(_ST7789_INVON)

        # MADCTL: 设置显示方向 (横屏, 原项目 rotation=3)
        # LovyanGFX rotation=3 对应: MY + MV (0xA0)
        # 不要加 MX，否则画面水平镜像
        self._write_cmd_data(_ST7789_MADCTL,
                             bytes([_MADCTL_MY | _MADCTL_MV | _MADCTL_RGB]))

        self._write_cmd(_ST7789_NORON)
        time.sleep_ms(10)

        self._write_cmd(_ST7789_DISPON)
        time.sleep_ms(10)

    def _set_window(self, x0, y0, x1, y1):
        """设置绘图窗口"""
        self._write_cmd(_ST7789_CASET)
        self._write_data(struct.pack('>HH', x0, x1))
        self._write_cmd(_ST7789_RASET)
        self._write_data(struct.pack('>HH', y0, y1))
        self._write_cmd(_ST7789_RAMWR)

    def show(self):
        """将整个帧缓冲区刷新到屏幕"""
        self._set_window(0, 0, self.width - 1, self.height - 1)
        self._dc.value(1)
        self._cs.value(0)
        self._spi.write(self._buf)
        self._cs.value(1)

    def show_region(self, x, y, w, h):
        """将帧缓冲区的指定区域刷新到屏幕"""
        self._set_window(x, y, x + w - 1, y + h - 1)
        self._dc.value(1)
        self._cs.value(0)
        # 逐行发送区域数据
        for row in range(h):
            offset = ((y + row) * self.width + x) * 2
            self._spi.write(self._mv[offset:offset + w * 2])
        self._cs.value(1)

    # ==================== 帧缓冲区操作 ====================

    def _pixel_offset(self, x, y):
        """计算像素在缓冲区中的字节偏移"""
        return (y * self.width + x) * 2

    def pixel(self, x, y, color):
        """在帧缓冲区中设置单个像素 (RGB565)"""
        if 0 <= x < self.width and 0 <= y < self.height:
            off = self._pixel_offset(x, y)
            self._buf[off] = (color >> 8) & 0xFF
            self._buf[off + 1] = color & 0xFF

    def pixel_read(self, x, y):
        """读取帧缓冲区中单个像素的颜色"""
        if 0 <= x < self.width and 0 <= y < self.height:
            off = self._pixel_offset(x, y)
            return (self._buf[off] << 8) | self._buf[off + 1]
        return 0

    def fill(self, color=0x0000):
        """用指定颜色填充整个帧缓冲区"""
        hi = (color >> 8) & 0xFF
        lo = color & 0xFF
        buf = self._buf
        for i in range(0, len(buf), 2):
            buf[i] = hi
            buf[i + 1] = lo

    def fill_rect(self, x, y, w, h, color):
        """填充矩形区域"""
        hi = (color >> 8) & 0xFF
        lo = color & 0xFF
        for row in range(max(0, y), min(self.height, y + h)):
            offset = self._pixel_offset(max(0, x), row)
            end_x = min(self.width, x + w)
            start_x = max(0, x)
            for col in range(start_x, end_x):
                self._buf[offset] = hi
                self._buf[offset + 1] = lo
                offset += 2

    def rect(self, x, y, w, h, color):
        """绘制矩形边框"""
        self.hline(x, y, w, color)
        self.hline(x, y + h - 1, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)

    def hline(self, x, y, w, color):
        """绘制水平线"""
        for i in range(w):
            self.pixel(x + i, y, color)

    def vline(self, x, y, h, color):
        """绘制垂直线"""
        for i in range(h):
            self.pixel(x, y + i, color)

    def line(self, x0, y0, x1, y1, color):
        """Bresenham 直线绘制"""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, filled=False):
        """绘制圆形 (中点圆算法)"""
        x = r
        y = 0
        err = 1 - r
        while x >= y:
            if filled:
                self.hline(cx - x, cy + y, 2 * x + 1, color)
                self.hline(cx - x, cy - y, 2 * x + 1, color)
                self.hline(cx - y, cy + x, 2 * y + 1, color)
                self.hline(cx - y, cy - x, 2 * y + 1, color)
            else:
                self.pixel(cx + x, cy + y, color)
                self.pixel(cx - x, cy + y, color)
                self.pixel(cx + x, cy - y, color)
                self.pixel(cx - x, cy - y, color)
                self.pixel(cx + y, cy + x, color)
                self.pixel(cx - y, cy + x, color)
                self.pixel(cx + y, cy - x, color)
                self.pixel(cx - y, cy - x, color)
            y += 1
            if err < 0:
                err += 2 * y + 1
            else:
                x -= 1
                err += 2 * (y - x) + 1

    # ==================== 文字渲染 ====================

    def text(self, s, x, y, color=0xFFFF, bg=None, scale=1):
        """
        在帧缓冲区中绘制文字 (不立即刷新到屏幕)

        参数:
            s:     要显示的字符串
            x, y:  左上角坐标
            color: 文字颜色 (RGB565)
            bg:    背景色 (RGB565)，None 表示透明
            scale: 缩放倍数 (1=原始大小, 2=双倍, ...)
        """
        cx = x
        for ch in s:
            if ch == '\n':
                cx = x
                y += 8 * scale
                continue
            code = ord(ch)
            if 32 <= code <= 126:
                idx = (code - 32) * 5
                for col in range(5):
                    byte = _FONT_5X8[idx + col]
                    for row in range(8):
                        if byte & (1 << row):
                            if scale == 1:
                                self.pixel(cx + col, y + row, color)
                            else:
                                self.fill_rect(cx + col * scale, y + row * scale,
                                               scale, scale, color)
                        elif bg is not None:
                            if scale == 1:
                                self.pixel(cx + col, y + row, bg)
                            else:
                                self.fill_rect(cx + col * scale, y + row * scale,
                                               scale, scale, bg)
                # 字符间距
                gap_w = scale
                if bg is not None:
                    for row in range(8 * scale):
                        if scale == 1:
                            self.pixel(cx + 5, y + row, bg)
                        else:
                            self.fill_rect(cx + 5 * scale, y + row, scale, 1, bg)
                cx += 6 * scale
            else:
                cx += 6 * scale

    def text_width(self, s, scale=1):
        """计算文字像素宽度"""
        return len(s) * 6 * scale - scale

    def text_center(self, s, y, color=0xFFFF, bg=None, scale=1):
        """在屏幕水平居中绘制文字"""
        w = self.text_width(s, scale)
        x = (self.width - w) // 2
        self.text(s, x, y, color, bg, scale)

    # ==================== 精灵绘制 ====================

    def blit(self, buf, x, y, w, h, transparent=None):
        """
        将 RGB565 缓冲区绘制到帧缓冲区 (支持透明色)

        参数:
            buf:       RGB565 格式的字节数组
            x, y:      目标坐标
            w, h:      宽度和高度
            transparent: 透明色 (RGB565)，该颜色不绘制
        """
        src_off = 0
        for row in range(h):
            dst_y = y + row
            if dst_y < 0 or dst_y >= self.height:
                src_off += w * 2
                continue
            for col in range(w):
                dst_x = x + col
                if dst_x < 0 or dst_x >= self.width:
                    src_off += 2
                    continue
                color = (buf[src_off] << 8) | buf[src_off + 1]
                if transparent is None or color != transparent:
                    dst_off = self._pixel_offset(dst_x, dst_y)
                    self._buf[dst_off] = buf[src_off]
                    self._buf[dst_off + 1] = buf[src_off + 1]
                src_off += 2

    def draw_sprite_1bit(self, data, x, y, w, h, color, scale=1):
        """
        绘制 1-bit 单色精灵 (每像素 1 bit，行优先)

        参数:
            data: 字节数组，每行 ceil(w/8) 字节
            x, y: 目标坐标
            w, h: 宽度和高度
            color: 前景色 (RGB565)
            scale: 缩放倍数
        """
        bytes_per_row = (w + 7) // 8
        for row in range(h):
            for col in range(w):
                byte_idx = row * bytes_per_row + (col >> 3)
                bit_idx = 7 - (col & 7)
                if byte_idx < len(data) and (data[byte_idx] >> bit_idx) & 1:
                    if scale == 1:
                        self.pixel(x + col, y + row, color)
                    else:
                        self.fill_rect(x + col * scale, y + row * scale,
                                       scale, scale, color)
