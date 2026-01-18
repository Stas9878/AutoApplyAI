import re
from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.logger import logger
from src.platforms.hh.client import HHPublicClient
from src.services.matching import EmbeddingMatcher
from src.db.crud import (
    save_vacancy_if_not_exists,
    has_user_seen_vacancy,
    mark_vacancy_as_sent_to_user
)


_matcher = EmbeddingMatcher()


def _clean_html(raw_html: str) -> str:
    if not raw_html:
        return ''
    clean = re.sub(r'<[^>]+>', ' ', raw_html)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()


async def search_vacancies_for_user(
    session: AsyncSession,
    user_uuid: UUID,
    resume_text: str,
    filter_data: dict,
    max_pages: int = 2,
    limit_per_user: int = 10,
    mark_as_sent: bool = True
) -> list[dict]:
    results = []
    async with HHPublicClient() as client:
        vacancies = client.search_all_vacancies(
            text=filter_data['text_query'],
            experience=filter_data.get('experience'),
            employment=filter_data.get('employment'),
            area_id=filter_data.get('area_id', 113),
            only_with_salary=filter_data.get('only_with_salary', False),
            max_pages=max_pages
        )
        async for vacancy in vacancies:
            if len(results) >= limit_per_user:
                break

            # Пропускаем, если уже отправляли — ТОЛЬКО если mark_as_sent=True
            if mark_as_sent:
                if await has_user_seen_vacancy(session, user_uuid, vacancy['id']):
                    continue

            try:
                details = await client.get_vacancy_details(vacancy['id'])
            except Exception as e:
                logger.warning(f'Ошибка загрузки {vacancy["id"]}: {e}')
                continue

            description_raw = details.get('description', '')
            description_clean = _clean_html(description_raw)
            snippet = description_clean[:200] + ('...' if len(description_clean) > 200 else '')

            key_skills = [s['name'] for s in details.get('key_skills', [])]
            published_at = vacancy.get('published_at', '')

            score = _matcher.compute_match_score(
                resume_text=resume_text,
                vacancy_title=vacancy['name'],
                vacancy_description=description_clean,
                key_skills=key_skills
            )

            if score >= filter_data.get('min_match_threshold', 0.7):
                salary = vacancy.get('salary') or {}
                vac_data = {
                    'id': vacancy['id'],
                    'title': vacancy['name'],
                    'company': vacancy['employer']['name'],
                    'url': vacancy['alternate_url'].strip(),
                    'experience': vacancy.get('experience', {}).get('name', ''),
                    'employment': vacancy.get('employment', {}).get('name', ''),
                    'salary_from': salary.get('from'),
                    'salary_to': salary.get('to'),
                    'currency': salary.get('currency'),
                    'description': description_clean[:2000],
                    'key_skills': key_skills,
                    'published_at': published_at,
                }
                await save_vacancy_if_not_exists(session, vac_data)

                results.append({
                    **vac_data,
                    'match_score': round(score, 3),
                    'snippet': snippet
                })

                # Помечаем ТОЛЬКО если нужно
                if mark_as_sent:
                    await mark_vacancy_as_sent_to_user(session, user_uuid, vacancy['id'])

    results.sort(key=lambda x: x['match_score'], reverse=True)
    return results