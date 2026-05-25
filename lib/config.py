"""
MicroPyNES - 硬件引脚配置
=========================
与 DIJI-NES 原始 C++ 项目完全兼容的 GPIO 映射。
所有引脚编号直接对应 ESP32-S3 的物理 GPIO 编号，
可在 MicroPython 中通过 machine.Pin(gpio_number) 直接使用。

硬件清单:
  - MCU:        ESP32-S3-N16R8 (双核 240MHz, 16MB Flash, 8MB PSRAM)
  - 显示屏:     ST7789 TFT LCD 320x240 (SPI)
  - 音频 DAC:   MAX98357A I2S DAC
  - 存储:       SD 卡 (FAT32)
  - 输入:       8 个按键 (直连 GPIO, INPUT_PULLUP)
"""

# ==================== TFT 显示屏 (SPI1) ====================
# ST7789 320x240, 通过 SPI 接口连接
TFT_SCLK = 14       # SPI 时钟
TFT_MOSI = 13       # SPI 数据 (SDA)
TFT_DC   = 11       # 数据/命令选择
TFT_CS   = 10       # 片选
TFT_RST  = 12       # 复位
TFT_SPI_ID = 1      # SPI 总线 ID (1=SPI2_HOST, 2=SPI3_HOST)
TFT_FREQ = 26000000 # SPI 频率 26MHz (兼顾速度和稳定性)
TFT_WIDTH  = 320    # 屏幕物理宽度
TFT_HEIGHT = 240    # 屏幕物理高度
TFT_INVERT = True   # 颜色反转 (与原项目 lgfx_conf.h 中 cfg.invert = true 一致)
TFT_BGR    = True   # BGR 颜色序 (大多数 ST7789 模块使用 BGR)
TFT_OFFSET_X = 0    # 列地址偏移 (部分模块需要 0 或 40)
TFT_OFFSET_Y = 0    # 行地址偏移 (部分模块需要 0 或 40)

# ==================== SD 卡 (SoftSPI) ====================
# ESP32-S3 Octal-SPIRAM 占用 SPI(2)/SPI3_HOST，导致崩溃
# SPI(1)/FSPI 被显示屏占用且引脚不同，无法共享
# 因此 SD 卡必须使用 SoftSPI (软件模拟 SPI)
SD_CS   = 42
SD_SCLK = 40
SD_MISO = 39
SD_MOSI = 41
SD_FREQ = 5000000   # SoftSPI 频率不宜过高

# ==================== I2S 音频 (MAX98357A) ====================
I2S_BCLK = 5        # 位时钟
I2S_LRC  = 4        # 左右声道时钟
I2S_DOUT = 6        # 数据输出
I2S_SAMPLE_RATE = 44100  # 采样率 44100 Hz

# ==================== 游戏控制器按键 ====================
# 所有按键使用 INPUT_PULLUP，按下为低电平 (0)，松开为高电平 (1)
BTN_A      = 48
BTN_B      = 47
BTN_SELECT = 16
BTN_START  = 15
BTN_UP     = 17
BTN_DOWN   = 3
BTN_LEFT   = 8
BTN_RIGHT  = 18

# NES 手柄标准位掩码 (与原项目 controllerState 编码一致)
BTN_MASK_A      = 0x01
BTN_MASK_B      = 0x02
BTN_MASK_SELECT = 0x04
BTN_MASK_START  = 0x08
BTN_MASK_UP     = 0x10
BTN_MASK_DOWN   = 0x20
BTN_MASK_LEFT   = 0x40
BTN_MASK_RIGHT  = 0x80

# ==================== 显示参数 ====================
GAME_WIDTH  = 256   # NES 标准分辨率宽度
GAME_HEIGHT = 240   # NES 标准分辨率高度
TFT_OFFSET_X = (TFT_WIDTH - GAME_WIDTH) // 2  # 横向居中偏移 = 32

# ==================== 菜单颜色 (RGB565) ====================
def rgb565(r, g, b):
    """将 RGB888 转换为 RGB565 格式"""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

MENU_BG_COLOR     = rgb565(32, 32, 32)    # 深灰背景
MENU_HEADER_COLOR = rgb565(72, 77, 72)    # 中灰标题
MENU_TEXT_COLOR   = rgb565(192, 192, 192)  # 浅灰文字
MENU_HIGHLIGHT_BG = rgb565(255, 255, 0)   # 选中项背景 (黄色)
MENU_ARROW_COLOR  = rgb565(168, 174, 168) # 箭头颜色
MENU_HINT_COLOR   = rgb565(120, 120, 120) # 提示文字
MENU_TITLE_COLOR  = rgb565(224, 224, 224) # 标题文字
MENU_BORDER_COLOR = rgb565(80, 85, 80)    # 边框颜色
