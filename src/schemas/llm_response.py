from typing import Any

from pydantic import BaseModel, Field


class LLMResponseURLSchema(BaseModel):
    """Схема ответа от LLM для анализа запроса"""
    url: str = Field(description="URL для парсинга")
    fields: list[str] = Field(description="Список полей для CSV")
    description: str = Field(description="Описание что мы ищем")


class ParsedDataSchema(BaseModel):
    """Упрощенная схема для распарсенных данных"""
    data: list[dict[str, Any]] | None = Field(default=[], description="Список записей с данными")