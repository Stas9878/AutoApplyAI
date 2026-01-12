import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio

from src.logger import logger
from src.platforms.habr.service import parse_and_save_habr_contacts


async def main():
    logger.info('🚀 Запуск полного парсинга Habr Career...')
    result = await parse_and_save_habr_contacts()
    logger.info(
        f'🏁 Парсинг завершён. '
        f'Активных: {result["total_active"]}, '
        f'новых: {result["new_saved"]}, '
        f'удалённых: {result["deleted_moved"]}'
    )


if __name__ == '__main__':
    asyncio.run(main())