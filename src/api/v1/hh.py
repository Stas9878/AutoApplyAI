import re
from typing import Annotated
from fastapi import APIRouter, Query

from src.core.logger import logger
from src.core.settings import settings
from src.services.matching import EmbeddingMatcher
from src.platforms.hh.client import HHPublicClient
from src.api.v1.schemas.hh import HHSearchResponse

hh_router = APIRouter(prefix='/hh', tags=['HeadHunter'])

# Инициализируем матчинг
_matcher = EmbeddingMatcher()


def _clean_html(raw_html: str) -> str:
    '''Удаляет HTML-теги и нормализует текст.'''
    if not raw_html:
        return ''

    clean = re.sub(r'<[^>]+>', ' ', raw_html)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()


@hh_router.get('/search', response_model=HHSearchResponse)
async def search_and_match_vacancies(
    text: str,
    experience: Annotated[list[str], Query()] = ['between1And3', 'between3And6'],
    employment: Annotated[list[str], Query()] = ['full'],
    area_id: int = 113,
    only_with_salary: bool = False,
    min_match_threshold: Annotated[float, Query(ge=0.0, le=1.0)] = 0.7,
    limit: Annotated[int, Query(gt=0, le=50)] = 10
):
    '''
    Ищет вакансии на HeadHunter и оценивает их соответствие вашему резюме.
    Возвращает отсортированный по релевантности список.
    '''
    results = []
    processed_ids = set()

    async with HHPublicClient() as client:
        async for vacancy in client.search_all_vacancies(
            text=text,
            experience=experience,
            employment=employment,
            area_id=area_id,
            only_with_salary=only_with_salary,
            max_pages=3
        ):
            if len(results) >= limit:
                break

            vac_id = vacancy['id']
            if vac_id in processed_ids:
                continue
            processed_ids.add(vac_id)

            try:
                details = await client.get_vacancy_details(vac_id)
            except Exception as e:
                logger.warning(f'Пропущена вакансия {vac_id}: {e}')
                continue

            title = vacancy.get('name', '')
            description = _clean_html(details.get('description', ''))
            key_skills = [skill['name'] for skill in details.get('key_skills', [])]
            published_at = vacancy.get('published_at', '')

            score = _matcher.compute_match_score(
                resume_text=settings.resume_text,
                vacancy_title=title,
                vacancy_description=description,
                key_skills=key_skills
            )

            if score >= min_match_threshold:
                results.append({
                    'vacancy_id': vac_id,
                    'title': title,
                    'company': vacancy['employer']['name'],
                    'url': vacancy['alternate_url'].strip(),  # уберём пробелы
                    'match_score': round(score, 3),
                    'salary': vacancy.get('salary'),
                    'published_at': published_at,
                    'snippet': description[:200] + ('...' if len(description) > 200 else '')
                })

    results.sort(key=lambda x: x['match_score'], reverse=True)
    return {'results': results}