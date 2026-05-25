# 部署指南

## 概述

本文档详细说明如何将 MicroPyNES 固件和游戏部署到 ESP32-S3-N16R8 开发板上。

本项目基于 DIJINES ESP32-S3 NES 掌机的硬件设计，使用 MicroPython 替代原有的 Arduino C++ 固件。

---

## 前置条件

### 硬件需求

| 组件 | 型号/规格 | 备注 |
|------|-----------|------|
| 开发板 | ESP32-S3-N16R8 | 16MB Flash, 8MB PSRAM |
| 显示屏 | ST7789 TFT LCD | 320×240, SPI 接口 |
| 音频模块 | MAX98357A | I2S 数字功放 |
| 喇叭 | 8Ω 2W | 3W 或以下 |
| SD 卡 | FAT32 格式 | 建议 4GB-32GB |
| SD 卡模块 | SPI 接口 | 板载或外接 |
| 按键 | 8 个轻触开关 | NES 手柄布局 |

### 软件需求

- **Python 3.8+** (主机电脑)
- **mpremote** (MicroPython 部署工具)
- **esptool** (ESP32 固件烧录工具)

---

## 步骤一: 安装 MicroPython 固件

### 1.1 下载 MicroPython 固件

从 MicroPython 官网下载 ESP32-S3 固件:
```
https://micropython.org/download/ESP32_GENERIC_S3/
```

选择带 SPIRAM 支持的版本 (文件名包含 `spiram`):
```
ESP32_GENERIC_S3-SPIRAM-FLASH-16M.bin
```

### 1.2 安装 esptool

```bash
pip install esptool
```

### 1.3 擦除 Flash

将 ESP32-S3 连接到电脑，进入下载模式 (按住 BOOT 键后按 RESET 键)。

```bash
esptool.py --chip esp32s3 --port COM3 erase_flash
```

> **注意**: 将 `COM3` 替换为你实际的串口号 (Linux/Mac 上为 `/dev/ttyUSB0` 或 `/dev/ttyACM0`)。

### 1.4 烧录固件

```bash
esptool.py --chip esp32s3 --port COM3 \
  --baud 460800 write_flash -z 0x0 \
  ESP32_GENERIC_S3-SPIRAM-FLASH-16M.bin
```

---

## 步骤二: 安装部署工具

### 2.1 安装 mpremote

```bash
pip install mpremote
```

### 2.2 验证连接

```bash
mpremote connect COM3 repl
```

进入 MicroPython REPL 后，输入以下代码验证:
```python
import sys
print(sys.platform)  # 应输出 'esp32'
```

按 `Ctrl+]` 退出 REPL。

---

## 步骤三: 部署项目文件

### 3.1 准备文件结构

将以下文件复制到 ESP32-S3:

```
ESP32-S3 文件系统:
├── boot.py                    ← 启动配置
├── main.py                    ← 主程序
├── lib/
│   ├── __init__.py
│   ├── config.py              ← 引脚配置
│   ├── display.py             ← 显示驱动
│   ├── buttons.py             ← 按键驱动
│   ├── audio.py               ← 音频驱动
│   ├── sdcard.py              ← SD卡驱动
│   └── engine.py              ← 游戏引擎
└── games/
    ├── snake.py               ← 贪吃蛇
    ├── breakout.py            ← 打砖块
    └── invaders.py            ← 太空侵略者
```

### 3.2 使用 mpremote 部署

```bash
# 进入项目目录
cd MicroPyNES

# 创建目录
python -m mpremote connect COM5 mkdir lib
python -m mpremote connect COM6 mkdir games

# 复制核心文件
python -m mpremote connect COM6 cp boot.py :boot.py
python -m mpremote connect COM6 cp main.py :main.py

# 复制库文件
python -m mpremote connect COM6 cp lib/__init__.py :lib/__init__.py
python -m mpremote connect COM6 cp lib/config.py :lib/config.py
python -m mpremote connect COM6 cp lib/display.py :lib/display.py
python -m mpremote connect COM6 cp lib/buttons.py :lib/buttons.py
python -m mpremote connect COM6 cp lib/audio.py :lib/audio.py
python -m mpremote connect COM6 cp lib/sdcard.py :lib/sdcard.py
python -m mpremote connect COM6 cp lib/engine.py :lib/engine.py

# 复制游戏文件
python -m mpremote connect COM6 cp games/snake.py :games/snake.py
python -m mpremote connect COM6 cp games/breakout.py :games/breakout.py
python -m mpremote connect COM6 cp games/invaders.py :games/invaders.py
```

### 3.3 批量部署脚本 (Windows)

创建 `deploy.bat`:
```batch
@echo off
set PORT=COM3

echo [1/3] 创建目录...
mpremote connect %PORT% mkdir lib
mpremote connect %PORT% mkdir games

echo [2/3] 部署核心文件...
mpremote connect %PORT% cp boot.py :boot.py
mpremote connect %PORT% cp main.py :main.py

echo [3/3] 部署库和游戏...
for %%f in (lib\*.py) do (
    mpremote connect %PORT% cp "%%f" ":lib/%%~nxf"
)
for %%f in (games\*.py) do (
    mpremote connect %PORT% cp "%%f" ":games/%%~nxf"
)

echo 部署完成！重启 ESP32-S3 即可运行。
pause
```

### 3.4 批量部署脚本 (Linux/Mac)

创建 `deploy.sh`:
```bash
#!/bin/bash
PORT="/dev/ttyUSB0"

echo "[1/3] 创建目录..."
mpremote connect $PORT mkdir lib
mpremote connect $PORT mkdir games

echo "[2/3] 部署核心文件..."
mpremote connect $PORT cp boot.py :boot.py
mpremote connect $PORT cp main.py :main.py

echo "[3/3] 部署库和游戏..."
for f in lib/*.py; do
    mpremote connect $PORT cp "$f" ":$f"
done
for f in games/*.py; do
    mpremote connect $PORT cp "$f" ":$f"
done

echo "部署完成！重启 ESP32-S3 即可运行。"
```

```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 步骤四: 准备 SD 卡

### 4.1 格式化 SD 卡

使用 FAT32 格式化 SD 卡 (推荐 4GB-32GB)。

### 4.2 创建游戏目录

```
SD卡根目录/
├── games/                    ← 推荐的游戏存放目录
│   ├── template_game.py      ← 示例游戏模板
│   └── your_game.py          ← 你的自定义游戏
└── (其他文件可忽略)
```

### 4.3 部署示例游戏到 SD 卡

将 `examples/template_game.py` 复制到 SD 卡的 `/games/` 目录。

---

## 步骤五: 首次启动

### 5.1 连接硬件

按照 DIJINES 的引脚连接图完成硬件接线 (参见下文"引脚连接")。

### 5.2 插入 SD 卡

将准备好的 SD 卡插入 SD 卡槽。

### 5.3 上电

给 ESP32-S3 上电，系统将:
1. 执行 `boot.py` (设置 CPU 频率)
2. 执行 `main.py` (初始化硬件，加载游戏)
3. 显示游戏菜单

### 5.4 操作

| 按键 | 功能 |
|------|------|
| UP / DOWN | 选择游戏 |
| START / A | 启动选中的游戏 |
| START + SELECT | 游戏中暂停 |
| B (暂停时) | 退出游戏返回菜单 |

---

## 引脚连接图

### TFT 显示屏 (SPI1)

| TFT 引脚 | ESP32-S3 GPIO | 说明 |
|----------|---------------|------|
| SCLK | GPIO 14 | SPI 时钟 |
| MOSI | GPIO 13 | SPI 数据 |
| DC | GPIO 11 | 数据/命令选择 |
| CS | GPIO 10 | 片选 |
| RST | GPIO 12 | 复位 |
| VCC | 3.3V | 电源 |
| GND | GND | 地 |
| BLK | 3.3V | 背光 (可接 GPIO 控制) |

### SD 卡 (SPI2)

| SD 卡引脚 | ESP32-S3 GPIO | 说明 |
|-----------|---------------|------|
| CS | GPIO 42 | 片选 |
| SCLK | GPIO 40 | SPI 时钟 |
| MISO | GPIO 39 | 主入从出 |
| MOSI | GPIO 41 | 主出从入 |
| VCC | 3.3V | 电源 |
| GND | GND | 地 |

### I2S 音频 (MAX98357A)

| MAX98357A 引脚 | ESP32-S3 GPIO | 说明 |
|----------------|---------------|------|
| BCLK | GPIO 5 | 位时钟 |
| LRC | GPIO 4 | 左右声道时钟 |
| DIN | GPIO 6 | 数据输入 |
| VIN | 5V | 电源 |
| GND | GND | 地 |

### 按键 (全部接 GND，使用内部上拉)

| 按键 | ESP32-S3 GPIO |
|------|---------------|
| A | GPIO 48 |
| B | GPIO 47 |
| SELECT | GPIO 16 |
| START | GPIO 15 |
| UP | GPIO 17 |
| DOWN | GPIO 3 |
| LEFT | GPIO 8 |
| RIGHT | GPIO 18 |

> **注意**: 所有按键一端接 GPIO，另一端接 GND。使用 ESP32 内部上拉电阻 (INPUT_PULLUP)。

---

## 故障排除

### 屏幕无显示

1. 检查 SPI 接线是否正确 (特别是 DC 和 CS 引脚)
2. 确认显示屏为 ST7789 驱动芯片
3. 检查 RST 引脚连接
4. 尝试调整 SPI 频率 (修改 `display.py` 中的 `baudrate`)

### 无声音

1. 检查 I2S 接线 (BCLK/LRC/DOUT)
2. 确认 MAX98357A 供电正常
3. 检查喇叭是否连接正确

### 按键无响应

1. 确认按键一端接 GPIO，另一端接 GND
2. 用万用表测试按键是否正常导通
3. 检查 GPIO 编号是否正确

### SD 卡无法识别

1. 确认 SD 卡为 FAT32 格式
2. 检查 SPI 接线
3. 尝试更换 SD 卡
4. 确认 SD 卡模块供电正常

### 内存不足

1. 确认使用的是 SPIRAM 版本的 MicroPython 固件
2. 减少游戏中的精灵/纹理使用量
3. 使用 `gc.collect()` 手动垃圾回收

### 游戏帧率低

1. 减少 `draw()` 中的绘图操作
2. 使用整数运算代替浮点运算
3. 避免在游戏循环中创建新对象
4. 参考 `DEVELOPER_GUIDE.md` 中的性能优化建议

---

## 从 DIJINES Arduino 固件切换

如果你的板子已经烧录了 DIJINES 的 Arduino 固件，切换到 MicroPython 的步骤:

1. **备份**: 如有需要，先备份 SD 卡上的 NES ROM 文件
2. **擦除**: 使用 `esptool.py erase_flash` 擦除 Flash
3. **烧录**: 按照步骤一烧录 MicroPython 固件
4. **部署**: 按照步骤三部署 MicroPyNES 文件
5. **SD 卡**: 格式化 SD 卡 (FAT32)，放入游戏 `.py` 文件

> **注意**: 切换后原有的 NES ROM 将无法运行。MicroPyNES 使用原生 Python 游戏，不支持 NES 模拟。

---

## 开发模式

### 使用 REPL 调试

```bash
# 连接 REPL
mpremote connect COM3 repl

# 手动运行游戏进行测试
import main
main.main()
```

### 实时文件编辑

```bash
# 编辑远程文件
mpremote connect COM3 cat :games/snake.py > snake_local.py
# 在本地编辑 snake_local.py
mpremote connect COM3 cp snake_local.py :games/snake.py

# 重启运行
mpremote connect COM3 reset
```

### 查看启动日志

```bash
mpremote connect COM3 repl
# 按 ESP32 上的 RESET 键，查看启动输出
```
