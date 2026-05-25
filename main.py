"""
MicroPyNES - 主启动器
=======================
ESP32-S3 启动后自动运行此文件。

功能:
  1. 初始化硬件
  2. 加载内置游戏
  3. 扫描 SD 卡用户游戏
  4. 显示游戏菜单
  5. 运行选中的游戏
"""

import sys
import gc

def main():
    """主入口函数"""
    print("=" * 40)
    print("  MicroPyNES - ESP32-S3 Game Console")
    print("  基于 DIJINES 硬件兼容设计")
    print("=" * 40)

    # 强制垃圾回收
    gc.collect()
    print("[Main] 可用内存:", gc.mem_free(), "bytes")

    # 导入引擎
    from lib.engine import GameEngine

    # 创建引擎
    engine = GameEngine()

    # 注册内置游戏
    print("[Main] 注册内置游戏...")

    from games.snake import SnakeGame
    engine.register_game(SnakeGame())

    from games.breakout import BreakoutGame
    engine.register_game(BreakoutGame())

    from games.invaders import SpaceInvadersGame
    engine.register_game(SpaceInvadersGame())

    # 扫描 SD 卡用户游戏
    print("[Main] 扫描 SD 卡游戏...")
    _scan_sd_games(engine)

    gc.collect()
    print("[Main] 内存:", gc.mem_free(), "bytes")
    print("[Main] 共注册", len(engine._games), "个游戏")
    print("[Main] 启动菜单系统...")

    # 进入主循环
    engine.run()


def _scan_sd_games(engine):
    """
    扫描 SD 卡上的用户游戏

    扫描位置:
      - /sd/games/*.py  (推荐)
      - /sd/*.py        (根目录)
    """
    try:
        from lib.sdcard import SDCard
        sd = SDCard()
        if not sd.is_mounted:
            return

        game_files = sd.list_games()
        if not game_files:
            print("[Main] SD 卡上未找到游戏")
            return

        for filepath in game_files:
            try:
                game = _load_game_from_sd(filepath)
                if game:
                    engine.register_game(game)
                    print("[Main] 已加载 SD 卡游戏:", game.name)
            except Exception as e:
                print("[Main] 加载游戏失败:", filepath, "-", e)

    except Exception as e:
        print("[Main] SD 卡扫描失败:", e)


def _load_game_from_sd(filepath):
    """
    从 SD 卡动态加载游戏

    参数:
        filepath: 游戏文件路径 (如 /sd/games/my_game.py)

    返回:
        Game 实例，加载失败返回 None
    """
    import machine

    # 提取模块名
    module_name = filepath.split('/')[-1].replace('.py', '')

    # 从 SD 卡读取文件内容
    with open(filepath, 'r') as f:
        code = f.read()

    # 执行游戏模块
    game_globals = {'__name__': module_name, '__file__': filepath}
    exec(code, game_globals)

    # 查找 Game 子类实例
    from lib.engine import Game
    for name, obj in game_globals.items():
        if (isinstance(obj, type) and issubclass(obj, Game) and obj is not Game):
            return obj()

    # 尝试调用 create_game() 函数
    if 'create_game' in game_globals and callable(game_globals['create_game']):
        game = game_globals['create_game']()
        if isinstance(game, Game):
            return game

    print("[Main] 未找到 Game 子类或 create_game() 函数:", filepath)
    return None


if __name__ == "__main__":
    main()
