import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.logger import logger
from src.core.outreach_service import send_outreach_batch


async def main():
    logger.info('📬 Запуск рассылки...')
    total_sent = 0
    while True:
        sent = await send_outreach_batch(batch_size=20, pause_sec=100)
        if sent == 0:
            break
        total_sent += sent
    logger.info(f'🏁 Рассылка завершена. Всего отправлено: {total_sent}')


if __name__ == '__main__':
    asyncio.run(main())