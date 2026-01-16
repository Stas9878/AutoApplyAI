import asyncio
import aiohttp
from bs4 import BeautifulSoup

from src.core.logger import logger


class HabrParser:
    '''Парсер карточек компаний на Хабр'''

    def __init__(self, base_url: str = 'https://career.habr.com'):
        self.base_url = base_url.rstrip('/')

    async def fetch_html(self, session: aiohttp.ClientSession, url: str) -> str | None:
        '''Получает HTML-страницу.'''
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                logger.warning(f'HTTP {response.status} при запросе {url}')
                return None
        except Exception as e:
            logger.error(f'Ошибка при запросе {url}: {e}')
            return None

    async def parse_companies_page(self, session: aiohttp.ClientSession, page: int) -> list[dict[str, str]]:
        '''Парсит одну страницу списка компаний.'''
        url = f'{self.base_url}/companies?page={page}'
        html = await self.fetch_html(session, url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', class_='companies-item')
        if not items:
            return []

        companies = []
        for item in items:
            title_tag = item.find('a', class_='title')
            if not title_tag:
                continue
            href = title_tag.get('href')
            name = title_tag.get_text(strip=True)
            if href and name:
                full_url = f'{self.base_url}{href}' if href.startswith('/') else href
                companies.append({
                    'name': name,
                    'url': full_url
                })
        return companies

    async def extract_email_from_company(self, session: aiohttp.ClientSession, company_url: str) -> str | None:
        '''Извлекает email с карточки компании.'''
        html = await self.fetch_html(session, company_url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')
        contacts = soup.find_all('div', class_='contact')
        for contact in contacts:
            type_div = contact.find('div', class_='type')
            value_div = contact.find('div', class_='value')
            if (
                type_div
                and value_div
                and 'Email' in type_div.get_text()
            ):
                email = value_div.get_text(strip=True)
                if '@' in email:
                    return email
        return None

    async def parse_emails(self) -> list[dict[str, str]]:
        '''Парсит ВСЕ страницы компаний с Habr Career до конца.'''
        logger.info(f'🔍 Начинаю парсинг всех страниц на {self.base_url}...')
        all_contacts = []
        page = 1

        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            while True:
                logger.info(f'📄 Страница {page}...')
                companies = await self.parse_companies_page(session, page)
                if not companies:
                    logger.info('✅ Достигнут конец списка компаний.')
                    break

                tasks = [
                    self.extract_email_from_company(session, comp['url'])
                    for comp in companies
                ]
                emails = await asyncio.gather(*tasks)

                for comp, email in zip(companies, emails):
                    if email:
                        all_contacts.append({
                            'email': email,
                            'company_name': comp['name'],
                            'source_url': comp['url']
                        })

                page += 1

        logger.info(f'✅ Всего найдено {len(all_contacts)} email\'ов')
        return all_contacts