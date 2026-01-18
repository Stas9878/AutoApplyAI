import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.core.logger import logger
from src.core.settings import settings


class EmbeddingMatcher:
    """
    Простой матчинг резюме и вакансии через эмбеддинги.
    Без кэширования, без сохранения состояния между вызовами.
    """
    EMBEDDING_MODEL = settings.embedding_model

    def __init__(self):
        """
        Инициализирует модель эмбеддингов.
        Загрузка происходит один раз при создании экземпляра.
        """
        model = self.EMBEDDING_MODEL
        logger.info(f'Загрузка модели эмбеддингов: {model}')
        self.model = SentenceTransformer(model)
        logger.info('Модель загружена.')

    def compute_match_score(
        self,
        resume_text: str,
        vacancy_title: str,
        vacancy_description: str,
        key_skills: list[str] | None = None,
    ) -> float:
        """
        Вычисляет процент соответствия вакансии резюме.

        :param resume_text: текст резюме (опыт, навыки, проекты)
        :param vacancy_title: название вакансии
        :param vacancy_description: описание вакансии (очищенное от HTML)
        :param key_skills: список ключевых навыков из вакансии (опционально)
        :return: сходство от 0.0 до 1.0
        """
        # Собираем текст вакансии
        vacancy_parts = [vacancy_title, vacancy_description]
        if key_skills:
            vacancy_parts.append(' '.join(key_skills))
        vacancy_text = ' '.join(vacancy_parts).strip()

        if not resume_text or not vacancy_text:
            return 0.0

        # Генерируем эмбеддинги
        try:
            embeddings = self.model.encode([resume_text, vacancy_text])
            resume_emb = embeddings[0]
            vacancy_emb = embeddings[1]

            # Косинусное сходство
            similarity = cosine_similarity([resume_emb], [vacancy_emb])[0][0]
            score = float(np.clip(similarity, 0.0, 1.0))
            return score

        except Exception as e:
            logger.error(f'Ошибка при вычислении матчинга: {e}')
            return 0.0