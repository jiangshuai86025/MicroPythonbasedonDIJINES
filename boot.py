"""
MicroPyNES - 启动配置文件
===========================
ESP32-S3 通电后最先执行的文件。
在此文件中进行最低级别的初始化。
"""

import gc
import machine

# 设置 CPU 频率为 240MHz (最大性能)
machine.freq(240000000)

# 启用垃圾回收
gc.collect()
gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

print("[boot] MicroPyNES 启动中...")
print("[boot] CPU 频率:", machine.freq() // 1000000, "MHz")
print("[boot] 可用内存:", gc.mem_free(), "bytes")
