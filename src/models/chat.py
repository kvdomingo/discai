from langchain.chat_models import BaseChatModel, init_chat_model

from src.settings import settings


def get_chat_model() -> BaseChatModel:
    return init_chat_model(f"google_genai:{settings.CHAT_MODEL}")


def get_title_model() -> BaseChatModel:
    return init_chat_model(f"google_genai:{settings.TITLE_MODEL}")
