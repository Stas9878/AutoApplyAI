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

from src.core.agents import CoverLetterCrew



async def main():
    crew = CoverLetterCrew()
    await crew.generate_letter('Sber')

asyncio.run(main())