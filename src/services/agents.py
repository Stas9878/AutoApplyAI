from crewai import Agent, Task, Crew, LLM, Process

from src.core.logger import logger
from src.core.settings import settings
from src.utils.resume_loader import load_resume_text


class CoverLetterCrew:
    '''Команда агентов для генерации персонализированного сопроводительного письма.'''

    def __init__(self):
        self.llm = LLM(
            model=settings.llm_model,
            base_url=settings.llm_url,
            temperature=0.7,
            top_p=0.9,
            repeat_penalty=1.1
        )
        self.resume_text = load_resume_text()

    def create_crew(self, company_name: str) -> Crew:
        '''Создаёт команду агентов для генерации письма под конкретную компанию.'''
        resume_context = self.resume_text

        generator = Agent(
            role='Профессиональный Python-разработчик',
            goal='Написать персонализированное сопроводительное письмо',
            backstory='Ты — опытный python разработчик. Используй только информацию из предоставленного резюме.',
            llm=self.llm
        )

        validator = Agent(
            role='Редактор технической документации',
            goal='Проверить письмо на соответствие требованиям',
            backstory='Ты проверяешь, что письмо основано на резюме, не содержит упоминаний прошлых компаний и звучит естественно.',
            llm=self.llm
        )

        generate_task = Task(
            description=f'''
                РЕЗЮМЕ КАНДИДАТА:
                {resume_context}

                ИНСТРУКЦИИ:
                — Напиши сопроводительное письмо для компании "{company_name}".
                — Используй **только факты из резюме выше** — не выдумывай.
                — Выдели релевантные технические навыки (например, FastAPI, PostgreSQL, RabbitMQ, Docker, LLM и т.д.).
                — Объясни, почему хочешь работать именно в "{company_name}".
                — **Категорически запрещено** упоминать названия компаний, где ты работал ранее (например, "Хекслет", "Сбербанк" и т.д.).
                — Письмо должно быть дружелюбным, профессиональным, содержать до 7-8 предложений.
            ''',
            expected_output='Только текст письма, без пояснений.',
            agent=generator
        )

        validate_task = Task(
            description=f'''
                Проверь письмо:

                {{{{Task.generate_task}}}}

                Критерии:
                1. В письме есть технические навыки из резюме.
                2. Нет упоминаний прошлых компаний.
                3. Тон профессиональный, но не шаблонный.
                4. Есть персонализация под компанию "{company_name}".

                Если всё в порядке — верни письмо без изменений.
                Если нарушены правила — исправь и верни улучшенную версию.
                Верни ТОЛЬКО итоговое письмо. Никаких комментариев, пояснений или метаданных.
            ''',
            expected_output='Финальное письмо, готовое к отправке.',
            agent=validator
        )

        return Crew(
            agents=[generator, validator],
            tasks=[generate_task, validate_task],
            process=Process.sequential
        )

    async def generate_letter(self, company_name: str) -> str | None:
        '''Генерирует сопроводительное письмо для указанной компании.'''
        try:
            crew = self.create_crew(company_name)
            result = await crew.kickoff_async()
            letter = str(result).strip()
            logger.info(f'✅ CrewAI сгенерировал письмо для {company_name}')
            logger.info(f'📄 Письмо:\n{letter}')
            return letter
        except Exception as e:
            logger.error(f'❌ Ошибка CrewAI для {company_name}: {e}')
            return None