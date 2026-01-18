import asyncio
from urllib.parse import urljoin
from typing import AsyncGenerator
from aiohttp import ClientSession, ClientTimeout, ClientError

from src.core.logger import logger


class HHPublicAPIError(Exception):
    """Исключение для ошибок публичного HH API"""
    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class HHPublicClient:
    BASE_URL = 'https://api.hh.ru'
    MAX_PER_PAGE = 100
    REQUEST_DELAY = 0.2  # секунд между запросами

    def __init__(
        self,
        session: ClientSession | None = None,
        timeout: int = 10,
    ):
        self._session = session
        self._timeout = ClientTimeout(total=timeout)
        self._owns_session = session is None

    async def __aenter__(self) -> 'HHPublicClient':
        if self._owns_session:
            self._session = ClientSession(
                timeout=self._timeout,
                headers={
                    'User-Agent': 'AutoApplyAI/1.0 (+https://github.com/stas9878)',
                }
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Универсальный запрос к публичному API HH"""
        url = urljoin(self.BASE_URL, path.lstrip('/'))

        try:
            async with self._session.request(method, url, **kwargs) as resp:
                logger.debug(f'HH Public API {method} {url} → {resp.status}')
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 429:
                    raise HHPublicAPIError('Rate limit exceeded (429)', status_code=429)
                else:
                    error_text = await resp.text()
                    logger.warning(f'HH API error {resp.status}: {error_text}')
                    raise HHPublicAPIError(
                        f'HTTP {resp.status}: {error_text}', status_code=resp.status
                    )
        except ClientError as e:
            logger.error(f'Network error on {method} {url}: {e}')
            raise HHPublicAPIError(f'Network error: {e}')

    async def search_vacancies_page(
        self,
        text: str,
        experience: list[str] | None = None,
        employment: list[str] | None = None,
        area_id: int = 113,
        only_with_salary: bool = False,
        per_page: int = 100,
        page: int = 0,
    ) -> dict:
        """
        Получить одну страницу вакансий из публичного API.
        """
        params = {
            'text': text,
            'area': area_id,
            'only_with_salary': str(only_with_salary).lower(),
            'per_page': min(per_page, self.MAX_PER_PAGE),
            'page': page,
        }
        if experience:
            params['experience'] = experience
        if employment:
            params['employment'] = employment

        return await self._request('GET', '/vacancies', params=params)

    async def search_all_vacancies(
        self,
        text: str,
        experience: list[str] | None = None,
        employment: list[str] | None = None,
        area_id: int = 113,
        only_with_salary: bool = False,
        max_pages: int = 20,
    ) -> AsyncGenerator[dict, None]:
        """
        Генератор: возвращает все найденные вакансии (до max_pages).
        """
        for page in range(max_pages):
            try:
                response = await self.search_vacancies_page(
                    text=text,
                    experience=experience,
                    employment=employment,
                    area_id=area_id,
                    only_with_salary=only_with_salary,
                    page=page
                )
                items: list = response.get('items', [])
                if not items:
                    break

                for item in items:
                    yield item

                # Проверка: последняя страница?
                if page >= response.get('pages', 0) - 1:
                    break

                # Пауза между запросами
                await asyncio.sleep(self.REQUEST_DELAY)

            except HHPublicAPIError as e:
                if e.status_code == 429:
                    logger.warning('Rate limited. Stopping pagination.')
                    break
                else:
                    raise

    async def get_vacancy_details(self, vacancy_id: str) -> dict:
        """
        Получить полное описание вакансии (включая description и key_skills).
        """
        data = await self._request('GET', f'/vacancies/{vacancy_id}')
        await asyncio.sleep(self.REQUEST_DELAY)
        return data
