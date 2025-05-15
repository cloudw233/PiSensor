from config import init_config
init_config()
import os
import importlib.util
import asyncio
from typing import List, Callable, Any
import inspect
import signal
from pathlib import Path
from loguru import logger

from core.relay_server import run_relay_server
from core.forwarding import forward_messages

# 配置loguru
logger.remove()  # 移除默认的处理器
logger.add(
    "logs/app_{time}.log",  # 日志文件路径
    rotation="1 day",  # 每天轮换一次
    retention="7 days",  # 保留30天的日志
    format="<green>[{time:YYYY-MM-DD HH:mm:ss}]</green>"
           "<cyan>[{name}]</cyan>"
           "<magenta>[{function}]</magenta>"
           "<level>[{level}]</level>"
           " <level>{message}</level>",
    level="INFO",
    enqueue=True,  # 异步写入
)

logger.add(
    sink=lambda msg: print(msg, flush=True),  # 输出到控制台
    format="<green>[{time:YYYY-MM-DD HH:mm:ss}]</green>"
           "<cyan>[{name}]</cyan>"
           "<magenta>[{function}]</magenta>"
           "<level>[{level}]</level>"
           " <level>{message}</level>",
    colorize=True,  # 启用颜色
    level="INFO"    # 设置日志级别
)

# 用于存储所有运行的任务
running_tasks: List[asyncio.Task] = []

# 初始化配置
init_config()


async def import_and_collect_runners(driver_path: str) -> List[Callable[[], Any]]:
    """
    导入driver文件夹中的所有模块的run函数
    按照module1/__init__.py, module2/__init__.py的结构导入
    """
    runners = []
    driver_dir = Path(driver_path)

    # 确保driver文件夹存在
    if not driver_dir.exists() or not driver_dir.is_dir():
        raise FileNotFoundError(f"Driver path '{driver_path}' does not exist or is not a directory")

    # 遍历driver文件夹中的所有子文件夹
    for module_dir in driver_dir.iterdir():
        if not module_dir.is_dir() or module_dir.name.startswith('__'):
            continue

        init_file = module_dir / '__init__.py'
        if not init_file.exists():
            logger.warning(f"No __init__.py found in {module_dir}")
            continue

        try:
            # 动态导入模块
            module_name = module_dir.name
            spec = importlib.util.spec_from_file_location(
                module_name,
                str(init_file)
            )
            if spec is None or spec.loader is None:
                logger.warning(f"Could not load spec for module: {module_name}")
                continue

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 检查模块是否有run函数
            if hasattr(module, 'run'):
                run_func = getattr(module, 'run')

                # 检查是否是可调用对象
                if not callable(run_func):
                    logger.warning(f"'run' in {module_name} is not callable")
                    continue

                # 检查是否是异步函数
                if not inspect.iscoroutinefunction(run_func):
                    logger.warning(f"'run' in {module_name} is not an async function")
                    continue

                runners.append((module_name, run_func))
                logger.success(f"Successfully loaded run function from {module_name}")
            else:
                logger.warning(f"Module {module_name} does not contain a run function")

        except Exception as e:
            logger.exception(f"Error loading module {module_name}")
            continue

    return runners


async def run_module(name: str, run_func: Callable) -> None:
    """
    运行单个模块的run函数并处理异常
    """
    try:
        logger.info(f"Starting module: {name}")
        await run_func()
    except asyncio.CancelledError:
        logger.info(f"Module {name} received cancel signal")
        raise
    except Exception as e:
        logger.exception(f"Error in module {name}")
    finally:
        logger.info(f"Module {name} stopped")


async def shutdown(signal_: signal.Signals) -> None:
    """
    关闭所有运行的任务
    """
    logger.info(f"Received exit signal {signal_.name}...")

    # 取消所有运行的任务
    for task in running_tasks:
        task.cancel()

    # 等待所有任务完成
    logger.info("Waiting for tasks to complete...")
    await asyncio.gather(*running_tasks, return_exceptions=True)

    # 停止事件循环
    loop = asyncio.get_running_loop()
    loop.stop()


def handle_exception(loop: asyncio.AbstractEventLoop, context: dict) -> None:
    """
    处理未捕获的异常
    """
    exception = context.get("exception", context["message"])
    logger.exception(f"Unhandled exception: {exception}")


async def main():
    ascii_art = r"""
  ____    _   ____                                      
 |  _ \  (_) / ___|    ___   _ __    ___    ___    _ __ 
 | |_) | | | \___ \   / _ \ | '_ \  / __|  / _ \  | '__|
 |  __/  | |  ___) | |  __/ | | | | \__ \ | (_) | | |   
 |_|     |_| |____/   \___| |_| |_| |___/  \___/  |_|   
    """
    logger.info(ascii_art)
    logger.info("Here we go!")
    driver_path = os.path.join(os.path.dirname(__file__), 'modules')

    try:
        # 收集所有的run函数
        runners = await import_and_collect_runners(driver_path)

        if not runners:
            logger.warning("No valid run functions found in any module")
            return

        # 设置信号处理
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(shutdown(s))
            )

        # 设置未捕获异常处理器
        loop.set_exception_handler(handle_exception)

        # 为每个模块创建任务
        logger.info(f"Starting {len(runners)} modules")
        global running_tasks
        running_tasks = [
            asyncio.create_task(run_module(name, run_func), name=name)
            for name, run_func in runners
        ]
        logger.info('Starting relay server...')
        running_tasks.append(asyncio.create_task(run_module('relay_server', run_relay_server), name='relay_server'))
        logger.info('Starting message forwarding service...')
        running_tasks.append(asyncio.create_task(run_module('forward_messages', forward_messages), name='forward_messages'))
        await asyncio.gather(*running_tasks, return_exceptions=True)

    except Exception as e:
        logger.exception("Main execution failed")
    finally:
        logger.info("Main process ended")


if __name__ == "__main__":
    try:
        logger.info("=== Starting application ===")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    finally:
        logger.info("=== Application terminated ===")