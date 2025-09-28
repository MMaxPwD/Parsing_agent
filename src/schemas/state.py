from pydantic import BaseModel


class GraphState(BaseModel):
    """Состояние графа, передаваемое между узлами."""
    user_input: str = ""
    current_step: str = ""
    error: str | None = None
    url: str | None = None
    fields: list[str] = []
    page_content: str | None = None
    parsed_data: list[dict] = []
    csv_path: str | None = None
