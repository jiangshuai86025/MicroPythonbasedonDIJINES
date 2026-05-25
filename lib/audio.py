"""
MicroPyNES - I2S 音频驱动
==========================
通过 MAX98357A I2S DAC 输出音频，与 DIJI-NES 原始硬件兼容。

功能:
  - I2S 初始化 (44100Hz, 16-bit, 立体声)
  - 音调生成 (方波/正弦波)
  - 简单音效播放 (beep, boop 等)
  - 音乐播放 (单音旋律序列)

注意: MicroPython 的 I2S API 在不同固件版本间可能有差异。
      本驱动针对 ESP32-S3 MicroPython 官方固件编写。
"""

import math
from lib.config import I2S_BCLK, I2S_LRC, I2S_DOUT, I2S_SAMPLE_RATE

# 尝试导入 I2S，如果不可用则提供静默降级
try:
    from machine import I2S, Pin
    _I2S_AVAILABLE = True
except ImportError:
    _I2S_AVAILABLE = False


class Audio:
    """
    I2S 音频驱动

    用法:
        from lib.audio import Audio
        audio = Audio()
        audio.beep(440, 200)      # 440Hz 响 200ms
        audio.play_tone(880, 100) # 880Hz 响 100ms
    """

    # NES 风格音频参数
    SAMPLE_RATE = I2S_SAMPLE_RATE  # 44100 Hz
    BITS_PER_SAMPLE = 16
    CHANNELS = 2  # 立体声 (MAX98357A 会混合为单声道输出)

    def __init__(self):
        """初始化 I2S 音频输出"""
        self._i2s = None
        self._enabled = False
        self._volume = 0.5  # 音量 0.0 ~ 1.0

        if _I2S_AVAILABLE:
            try:
                self._i2s = I2S(
                    0,  # I2S 通道 0
                    sck=Pin(I2S_BCLK),
                    ws=Pin(I2S_LRC),
                    sd=Pin(I2S_DOUT),
                    mode=I2S.TX,
                    bits=16,
                    format=I2S.STEREO,
                    rate=self.SAMPLE_RATE,
                    ibuf=2048
                )
                self._enabled = True
            except Exception as e:
                print("[Audio] I2S 初始化失败:", e)
                self._enabled = False

    @property
    def enabled(self):
        return self._enabled

    def set_volume(self, vol):
        """
        设置音量

        参数:
            vol: 音量值 0.0 (静音) ~ 1.0 (最大)
        """
        self._volume = max(0.0, min(1.0, vol))

    def _generate_tone(self, freq, duration_ms):
        """
        生成指定频率和时长的正弦波音频数据

        返回:
            bytes: 16-bit 立体声 PCM 数据
        """
        num_samples = int(self.SAMPLE_RATE * duration_ms / 1000)
        buf = bytearray(num_samples * 2 * 2)  # 2 字节/样本 x 2 通道
        amplitude = int(16000 * self._volume)

        for i in range(num_samples):
            t = i / self.SAMPLE_RATE
            sample = int(amplitude * math.sin(2 * math.pi * freq * t))
            # 限制范围
            sample = max(-32768, min(32767, sample))
            # 写入左右声道 (小端序)
            offset = i * 4
            buf[offset] = sample & 0xFF
            buf[offset + 1] = (sample >> 8) & 0xFF
            buf[offset + 2] = sample & 0xFF
            buf[offset + 3] = (sample >> 8) & 0xFF

        return bytes(buf)

    def _generate_square(self, freq, duration_ms):
        """
        生成指定频率和时长的方波音频数据 (NES 风格)

        返回:
            bytes: 16-bit 立体声 PCM 数据
        """
        num_samples = int(self.SAMPLE_RATE * duration_ms / 1000)
        buf = bytearray(num_samples * 2 * 2)
        amplitude = int(12000 * self._volume)
        period = self.SAMPLE_RATE / freq if freq > 0 else self.SAMPLE_RATE

        for i in range(num_samples):
            # 方波: 前半周期正，后半周期负
            sample = amplitude if (i % period) < (period / 2) else -amplitude
            offset = i * 4
            buf[offset] = sample & 0xFF
            buf[offset + 1] = (sample >> 8) & 0xFF
            buf[offset + 2] = sample & 0xFF
            buf[offset + 3] = (sample >> 8) & 0xFF

        return bytes(buf)

    def play_tone(self, freq, duration_ms, wave_type='sine'):
        """
        播放指定频率的音调

        参数:
            freq: 频率 (Hz)
            duration_ms: 持续时间 (毫秒)
            wave_type: 波形类型 ('sine' 或 'square')
        """
        if not self._enabled or freq <= 0:
            return

        if wave_type == 'square':
            data = self._generate_square(freq, duration_ms)
        else:
            data = self._generate_tone(freq, duration_ms)

        try:
            self._i2s.write(data)
        except Exception:
            pass

    def beep(self, freq=1000, duration_ms=100):
        """
        发出提示音

        参数:
            freq: 频率，默认 1000Hz
            duration_ms: 持续时间，默认 100ms
        """
        self.play_tone(freq, duration_ms, 'square')

    def play_melody(self, notes, tempo=120):
        """
        播放旋律序列

        参数:
            notes: 音符列表，每个元素为 (频率, 持续拍数)
                   频率为 0 表示休止符
            tempo: 每分钟拍数 (BPM)
        """
        if not self._enabled:
            return

        beat_ms = int(60000 / tempo)
        for freq, beats in notes:
            duration = int(beat_ms * beats)
            if freq > 0:
                self.play_tone(freq, duration, 'square')
            else:
                # 休止符: 静音
                silent = bytearray(int(self.SAMPLE_RATE * duration / 1000) * 4)
                try:
                    self._i2s.write(bytes(silent))
                except Exception:
                    pass

    def stop(self):
        """停止音频输出"""
        if self._enabled and self._i2s:
            try:
                # 写入静音数据
                silent = bytearray(256)
                self._i2s.write(bytes(silent))
            except Exception:
                pass

    def deinit(self):
        """释放 I2S 资源"""
        if self._i2s:
            try:
                self._i2s.deinit()
            except Exception:
                pass
        self._enabled = False

    # ==================== NES 风格音效预设 ====================

    def snd_menu_move(self):
        """菜单移动音效"""
        self.beep(800, 30)

    def snd_menu_select(self):
        """菜单选择音效"""
        self.beep(1200, 50)

    def snd_game_start(self):
        """游戏开始音效"""
        self.play_melody([
            (523, 0.15), (659, 0.15), (784, 0.15), (1047, 0.3)
        ], tempo=300)

    def snd_game_over(self):
        """游戏结束音效"""
        self.play_melody([
            (440, 0.3), (349, 0.3), (294, 0.3), (220, 0.6)
        ], tempo=180)

    def snd_score(self):
        """得分音效"""
        self.beep(1500, 50)

    def snd_hit(self):
        """碰撞音效"""
        self.play_tone(200, 80, 'square')

    def snd_shoot(self):
        """射击音效"""
        self.play_tone(800, 50, 'square')
