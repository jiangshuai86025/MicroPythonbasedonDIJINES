"""
MicroPyNES - SD 卡文件系统驱动
================================
通过 SPI 接口访问 SD 卡，与 DIJI-NES 原始硬件引脚兼容。

功能:
  - SD 卡初始化与挂载
  - 文件列表扫描 (支持 .py 和 .nes 文件)
  - 文件读写
  - 目录操作

注意: ESP32-S3 MicroPython 使用 machine.SDCard 或 sdcard 模块。
      本驱动使用 sdcard 模块 (MicroPython 标准库)。
"""

import os
import machine
from lib.config import SD_CS, SD_SCLK, SD_MISO, SD_MOSI, SD_FREQ


class SDCard:
    """
    SD 卡文件系统管理

    用法:
        from lib.sdcard import SDCard
        sd = SDCard()
        if sd.mounted:
            files = sd.list_files('/')
            games = sd.list_games()
    """

    def __init__(self, mount_point='/sd'):
        """
        初始化并挂载 SD 卡

        参数:
            mount_point: 挂载点路径
        """
        self._mount_point = mount_point
        self._spi = None
        self._sd = None
        self.mounted = False

        self._init_sd()

    def _init_sd(self):
        """初始化 SD 卡"""
        try:
            # 使用 SoftSPI (软件模拟 SPI)
            # 原因: SPI(2)/SPI3_HOST 被 Octal-SPIRAM 占用会崩溃
            #       SPI(1)/FSPI 被显示屏占用且引脚不同无法共享
            self._spi = machine.SoftSPI(
                baudrate=SD_FREQ,
                polarity=0,
                phase=0,
                sck=machine.Pin(SD_SCLK, machine.Pin.OUT),
                mosi=machine.Pin(SD_MOSI, machine.Pin.OUT),
                miso=machine.Pin(SD_MISO, machine.Pin.IN)
            )

            # 尝试导入 sdcard 模块
            import sdcard
            self._sd = sdcard.SDCard(self._spi, machine.Pin(SD_CS))

            # 挂载文件系统
            os.mount(self._sd, self._mount_point)
            self.mounted = True
            print("[SD] 卡已挂载到", self._mount_point)

        except OSError as e:
            print("[SD] 初始化失败:", e)
            self.mounted = False
        except ImportError:
            print("[SD] sdcard 模块不可用，请确保固件包含 sdcard 支持")
            self.mounted = False
        except Exception as e:
            print("[SD] 未知错误:", e)
            self.mounted = False

    def unmount(self):
        """卸载 SD 卡"""
        if self.mounted:
            try:
                os.umount(self._mount_point)
            except Exception:
                pass
            self.mounted = False

    def remount(self):
        """重新挂载 SD 卡"""
        self.unmount()
        self._init_sd()

    def get_mount_point(self):
        """获取挂载点路径"""
        return self._mount_point

    def list_files(self, path='/', extension=None):
        """
        列出指定目录下的文件

        参数:
            path: 目录路径
            extension: 文件扩展名过滤 (如 '.py', '.nes')

        返回:
            文件路径列表 (相对于挂载点)
        """
        if not self.mounted:
            return []

        full_path = path
        if not path.startswith(self._mount_point):
            full_path = self._mount_point + ('' if path.startswith('/') else '/') + path

        files = []
        try:
            entries = os.listdir(full_path)
            for entry in sorted(entries):
                # 跳过 macOS 元数据文件
                if entry.startswith('._'):
                    continue
                if entry.startswith('.'):
                    continue

                entry_path = full_path + '/' + entry
                try:
                    stat = os.stat(entry_path)
                    # 检查是否为文件 (非目录)
                    if stat[0] & 0x4000 == 0:  # 不是目录
                        if extension is None or entry.lower().endswith(extension.lower()):
                            # 返回相对于挂载点的路径
                            rel_path = entry_path
                            if rel_path.startswith(self._mount_point):
                                rel_path = rel_path[len(self._mount_point):]
                            if not rel_path.startswith('/'):
                                rel_path = '/' + rel_path
                            files.append(rel_path)
                except OSError:
                    continue
        except OSError as e:
            print("[SD] 列出目录失败:", e)

        return files

    def list_games(self):
        """
        列出 SD 卡上所有用户游戏 (.py 文件)

        扫描位置: /sd/games/ 和 /sd/

        返回:
            游戏文件路径列表
        """
        games = []

        # 扫描 /sd/games/ 目录
        games_dir = self._mount_point + '/games'
        try:
            os.stat(games_dir)
            games.extend(self.list_files(games_dir, '.py'))
        except OSError:
            pass  # games 目录不存在

        # 扫描根目录下的 .py 文件
        root_games = self.list_files(self._mount_point, '.py')
        # 排除系统文件
        for g in root_games:
            basename = g.split('/')[-1].lower()
            if basename not in ('boot.py', 'main.py', 'lib.py'):
                games.append(g)

        return games

    def read_file(self, path):
        """
        读取文件内容

        参数:
            path: 文件路径 (相对于挂载点或绝对路径)

        返回:
            文件内容字符串
        """
        if not self.mounted:
            return None

        full_path = path
        if not path.startswith('/'):
            full_path = self._mount_point + '/' + path

        try:
            with open(full_path, 'r') as f:
                return f.read()
        except OSError as e:
            print("[SD] 读取文件失败:", e)
            return None

    def write_file(self, path, content):
        """
        写入文件

        参数:
            path: 文件路径
            content: 文件内容

        返回:
            True 如果成功
        """
        if not self.mounted:
            return False

        full_path = path
        if not path.startswith('/'):
            full_path = self._mount_point + '/' + path

        try:
            with open(full_path, 'w') as f:
                f.write(content)
            return True
        except OSError as e:
            print("[SD] 写入文件失败:", e)
            return False

    def file_exists(self, path):
        """检查文件是否存在"""
        if not self.mounted:
            return False

        full_path = path
        if not path.startswith('/'):
            full_path = self._mount_point + '/' + path

        try:
            os.stat(full_path)
            return True
        except OSError:
            return False

    def get_space(self):
        """
        获取 SD 卡空间信息

        返回:
            (总空间字节, 已用空间字节, 可用空间字节) 或 None
        """
        if not self.mounted:
            return None

        try:
            stat = os.statvfs(self._mount_point)
            total = stat[0] * stat[2]
            free = stat[0] * stat[3]
            used = total - free
            return (total, used, free)
        except OSError:
            return None
