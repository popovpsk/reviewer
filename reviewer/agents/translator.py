from reviewer.config.reviewer_config import Configuration
from reviewer.llm.llm import LLM


class Translator:
    PROMPT = """<SRC_TEXT>
{}
</SRC_TEXT>
Инструкции:
Твоя задача перевести SRC_TEXT на русский язык. Этот текст это результат код ревью.
Этот текст содержит ссылки на код.
Тебе ЗАПРЕЩЕНО переводить сам код или ссылки на код.
Ты ДОЛЖЕН переводить только весь остальной текст.
Форматируй этот перевод так, чтобы длина строки в выходном тексте была не больше 200 символов.
    """

    def __init__(self, llm: LLM, config: Configuration) -> None:
        self.llm = llm
        self.__config = config

    def translate(self, src: str) -> str:
        if not self.__config.translate_enabled:
            return src

        return self.llm.generate("translate", self.PROMPT.format(src))
