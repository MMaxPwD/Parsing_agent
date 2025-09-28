import csv

import requests
from bs4 import BeautifulSoup
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.constants import START
from langgraph.graph import StateGraph, END

from core.config import settings
from schemas.llm_response import ParsedDataSchema, LLMResponseURLSchema
from schemas.state import GraphState


class ParserChain:
    """Цепочка обработки с использованием LangGraph."""

    def __init__(self):
        self.graph = self._build_graph()
        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL_NAME,
            temperature=0
        )

    def _build_graph(self):
        """Создание и настройка графа."""
        workflow = StateGraph(GraphState)

        # Добавляем узлы
        workflow.add_node("analyze_request", self._analyze_request)
        workflow.add_node("parse_webpage", self._parse_webpage)
        workflow.add_node("extract_data", self._extract_data)
        workflow.add_node("save_csv", self._save_csv)

        # Определяем маршрут
        workflow.add_edge(START, "analyze_request")
        workflow.add_edge("analyze_request", "parse_webpage")
        workflow.add_edge("parse_webpage", "extract_data")
        workflow.add_edge("extract_data", "save_csv")
        workflow.add_edge("save_csv", END)

        return workflow.compile()

    async def run(self, input_text: str) -> dict:
        """Точка входа и определение initial_state"""
        initial_state = GraphState(
            user_input=input_text,
            current_step="start"
        )

        result = self.graph.invoke(initial_state)
        return result

    def _analyze_request(self, state: GraphState) -> dict:
        """Анализирует запрос пользователя и определяет URL и поля."""
        print(f"Начинаем анализировать запрос")
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Ты - AI ассистент для парсинга данных. Проанализируй запрос пользователя и определи:
1. URL сайта для парсинга (обязательно)
2. Список полей (столбцов) которые нужно извлечь
3. Краткое описание что мы ищем

Верни ответ в формате JSON."""),
                ("human", "Запрос пользователя: {user_input}")
            ])

            structured_llm = self.llm.with_structured_output(LLMResponseURLSchema)
            chain = prompt | structured_llm
            result = chain.invoke({"user_input": state.user_input})

            print(f"Поля: {result.fields}")
            print(f"URL: {result.url}")

            print(f"Анализ запроса окончен")
            return {
                "url": result.url,
                "fields": result.fields,
                "current_step": "analyzed_request",
                "description": result.description
            }


        except Exception as e:
            return {"error": f"Ошибка анализа запроса: {str(e)}"}

    def _parse_webpage(self, state: GraphState) -> dict:
        """Парсит веб-страницу и извлекает текст."""
        print(f"Начинаем парсинг страницы")
        if state.error:
            return {}

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(state.url, headers=headers, timeout=60)
            response.raise_for_status()
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "lxml")

            # Удаляем скрипты и стили
            for script in soup(["script", "style"]):
                script.decompose()

            # Получаем чистый текст
            text = soup.get_text(separator='\n', strip=True)

            # Ограничиваем размер текста для LLM
            if len(text) > 10000:
                text = text[:10000] + "... [текст обрезан]"
            print(f"Парсинг страницы окончен")
            return {
                "page_content": text,
                "current_step": "parsed_webpage"
            }

        except Exception as e:
            return {"error": f"Ошибка парсинга страницы: {str(e)}"}

    def _extract_data(self, state: GraphState) -> dict:
        """Извлекает данные из текста согласно указанным полям."""
        if state.error:
            return {}

        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Ты - AI для извлечения структурированных данных. 
    Из предоставленного текста веб-страницы извлеки данные согласно указанным полям.

    Поля для CSV: {fields}

    Инструкции:
    1. Извлеки ВСЕ подходящие данные из текста
    2. Если для поля нет данных - сгенерируй его самостоятельно. Не больше трех предложений. Данные должны быть информативными"
    3. Верни данные в формате JSON с ключом "data", который содержит список словарей
    4. Каждый словарь соответствует одной строке в CSV
    5. Извлекай только реальные данные из текста, не генерируй фиктивные
    6. Если данных нет - верни пустой список

    Пример правильного формата:
    {{"data": [{{"название": "Книга 1", "цена": "100 руб"}}]}}

    Текст для анализа:"""),
                ("human", "{page_content}")
            ])

            structured_llm = self.llm.with_structured_output(
                ParsedDataSchema,
                method="function_calling"
            )
            chain = prompt | structured_llm
            result = chain.invoke({
                "fields": state.fields,
                "page_content": state.page_content
            })

            print(f"Извлечение данных страницы окончено. Найдено записей: {len(result.data or [])}")

            return {
                "parsed_data": result.data or [],  # Защита от None
                "current_step": "extracted_data"
            }

        except Exception as e:
            return {"error": f"Ошибка извлечения данных: {str(e)}"}

    def _save_csv(self, state: GraphState) -> dict:
        """Сохраняет данные в CSV файл."""
        print(f"Сохраняем данные в CSV")
        if state.error:
            return {}

        if not state.parsed_data:
            return {"error": "Нет данных для сохранения"}

        try:
            import os
            import uuid

            # Создаем директорию если нет
            os.makedirs("output", exist_ok=True)

            # Генерируем уникальное имя файла
            filename = f"parsed_data_{uuid.uuid4().hex[:8]}.csv"
            csv_path = f"output/{filename}"

            # Сохраняем в CSV
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                if state.parsed_data:
                    writer = csv.DictWriter(csvfile, fieldnames=state.fields)
                    writer.writeheader()
                    for row in state.parsed_data:
                        # Фильтруем только нужные поля
                        filtered_row = {field: row.get(field, "N/A") for field in state.fields}
                        writer.writerow(filtered_row)
            print(f"Данные сохранены в CSV")
            return {
                "csv_path": csv_path,
                "current_step": "saved_csv"
            }

        except Exception as e:
            return {"error": f"Ошибка сохранения CSV: {str(e)}"}
