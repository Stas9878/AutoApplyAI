import sys
import warnings
from pathlib import Path

warnings.filterwarnings(
    'ignore',
    category=UserWarning,
    message='Pydantic serializer warnings*'
)

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.logger import logger
from src.core.outreach_service import send_outreach_batch


async def main():
    logger.info('🚀 Запуск рассылки с генерацией через CrewAI...')

    total_sent = 0
    batch_size = 10      # максимум 10 писем за раз
    pause_sec = 60     # пауза минута между батчами

    while True:
        sent = await send_outreach_batch(batch_size=batch_size, pause_sec=pause_sec)
        if sent == 0:
            break
        total_sent += sent

    logger.info(f'🏁 Рассылка завершена. Всего отправлено: {total_sent}')


if __name__ == '__main__':
    asyncio.run(main())