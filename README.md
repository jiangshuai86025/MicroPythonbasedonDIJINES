# MicroPythonbasedonDIJINES
首次新建比较实用的项目，并从本地上传
**基于 DIJINES ESP32-S3 硬件的 MicroPython 游戏引擎**

一个运行在 ESP32-S3 上的 MicroPython 游戏平台，硬件引脚与 DIJINES NES 掌机完全兼容，支持内置游戏和 SD 卡扩展用户自定义游戏。

## 特性

- 🎮 **3 款内置游戏** - 贪吃蛇、打砖块、太空侵略者
- 📦 **即插即玩** - 烧录固件后自动启动菜单
- 🕹️ **8 键输入** - NES 手柄布局 (A/B/START/SELECT + 方向键)
- 🔊 **I2S 音频** - MAX98357A 数字功放支持
- 📁 **SD 卡扩展** - 将 `.py` 游戏文件放入 SD 卡即可运行
- 🛠️ **开发友好** - 继承 Game 类，实现 3 个方法即可创建游戏
- 🔌 **硬件兼容** - 引脚布局与 DIJINES NES 掌机完全一致

## 硬件平台

| 组件 | 规格 |
|------|------|
| MCU | ESP32-S3-N16R8 (双核 240MHz, 16MB Flash, 8MB PSRAM) |
| 显示屏 | ST7789 TFT LCD 320×240 (SPI) |
| 音频 | MAX98357A I2S DAC |
| 存储 | SD 卡 (FAT32, SPI) |
| 输入 | 8 个轻触开关 (INPUT_PULLUP) |

## 快速开始

### 1. 烧录 MicroPython

```bash
pip install esptool mpremote

# 擦除并烧录 (替换 COM3 为你的串口)
esptool.py --chip esp32s3 --port COM3 erase_flash
esptool.py --chip esp32s3 --port COM3 --baud 460800 write_flash -z 0x0 \
  ESP32_GENERIC_S3-SPIRAM-FLASH-16M.bin
```

### 2. 部署项目

```bash
cd MicroPyNES

# Windows
deploy.bat

# Linux/Mac
chmod +x deploy.sh && ./deploy.sh

# 或手动部署
mpremote connect COM3 cp boot.py :boot.py
mpremote connect COM3 cp main.py :main.py
mpremote connect COM3 cp -r lib :lib
mpremote connect COM3 cp -r games :games
```

### 3. 准备 SD 卡

```
SD卡/
└── games/
    └── my_game.py      ← 你的自定义游戏
```

### 4. 上电运行

插入 SD 卡，给 ESP32-S3 上电，菜单自动显示。

## 操作说明

### 菜单操作

| 按键 | 功能 |
|------|------|
| UP / DOWN | 选择游戏 |
| START / A | 启动游戏 |

### 游戏中操作

| 按键 | 功能 |
|------|------|
| 方向键 | 游戏控制 |
| A / B | 动作键 |
| START + SELECT | 暂停 |
| B (暂停时) | 退出到菜单 |

## 创建你的游戏

只需 3 步:

```python
from lib.engine import Game, BLACK, CYAN

class MyGame(Game):
    def __init__(self):
        super().__init__("My Game")

    def init(self):
        self.x = 160

    def update(self, dt):
        if self.buttons.is_pressed('LEFT'):
            self.x -= 100 * dt
        if self.buttons.is_pressed('RIGHT'):
            self.x += 100 * dt

    def draw(self):
        self.display.fill(BLACK)
        self.display.fill_rect(int(self.x), 120, 16, 16, CYAN)
        self.display.show()
```

保存到 SD 卡的 `/games/` 目录，重启即可在菜单中看到。

详细 API 文档请参阅 [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)。

## 项目结构

```
MicroPyNES/
├── boot.py               ← 启动配置 (CPU频率/内存)
├── main.py               ← 主程序 (菜单/游戏加载)
├── lib/                   ← 核心库
│   ├── config.py          ← 硬件引脚配置
│   ├── display.py         ← ST7789 TFT 驱动 + 绘图API
│   ├── buttons.py         ← 8键输入驱动
│   ├── audio.py           ← I2S 音频驱动
│   ├── sdcard.py          ← SD 卡文件系统
│   └── engine.py          ← 游戏引擎框架
├── games/                 ← 内置游戏
│   ├── snake.py           ← 贪吃蛇
│   ├── breakout.py        ← 打砖块
│   └── invaders.py        ← 太空侵略者
├── examples/              ← 示例和模板
│   └── template_game.py   ← 游戏开发模板
├── DEPLOYMENT.md          ← 详细部署指南
├── DEVELOPER_GUIDE.md     ← 游戏开发API文档
└── README.md              ← 本文件
```

## 与 DIJINES 的关系

本项目使用与 [DIJI-NES](https://github.com/UF-Evan/DIJI-NES) NES 掌机**完全相同的硬件引脚布局**，但使用 MicroPython 替代 Arduino C++，实现了不同的功能目标:

| 对比项 | DIJINES (原项目) | MicroPyNES (本项目) |
|--------|-----------------|---------------------|
| 固件 | Arduino C++ | MicroPython |
| 功能 | NES 模拟器 | 原生游戏引擎 |
| 游戏来源 | NES ROM (.nes) | Python 脚本 (.py) |
| 开发门槛 | 需要修改 C++ | 只需写 Python |
| 显示库 | LovyanGFX | 自研 ST7789 驱动 |
| 音频 | NES APU 模拟 | I2S 音调合成 |
| 双核 | 使用 | 未使用 |

## 许可证

MIT License

## 致谢

- [DIJI-NES](https://github.com/UF-Evan/DIJI-NES) - 原始硬件设计和模拟器实现
- [MicroPython](https://micropython.org/) - Python 嵌入式实现
- [LovyanGFX](https://github.com/lovyan03/LovyanGFX) - 显示驱动参考
=======


