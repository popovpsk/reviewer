from typing import Optional

from reviewer.agents.review import Reviewer
from reviewer.agents.sanitizer import Sanitizer
from reviewer.agents.translator import Translator
from reviewer.ast_parser.ast_parser import ASTParser
from reviewer.config.reviewer_config import Configuration, get_configuration
from reviewer.llm.llm import LLM
from reviewer.processor.processor import ReviewerProcessor
from reviewer.processor.review_modes import ReviewModes
from reviewer.tokenization.token_counter import TokenCounter


class ServiceLocator:
    __reviewer_processor: Optional[ReviewerProcessor] = None
    __configuration: Optional[Configuration] = None
    __llm: Optional[LLM] = None
    __reviewer: Optional[Reviewer] = None
    __sanitizer: Optional[Sanitizer] = None
    __translator: Optional[Translator] = None
    __ast_parser: Optional[ASTParser] = None
    __token_counter: Optional[TokenCounter] = None
    __review_modes: Optional[ReviewModes] = None

    def get_reviewer_processor(self) -> ReviewerProcessor:
        if not self.__reviewer_processor:
            self.__reviewer_processor = ReviewerProcessor(
                self.get_configuration(),
                self.get_translator(),
                self.get_review_modes(),
            )

        return self.__reviewer_processor

    def get_configuration(self) -> Configuration:
        if not self.__configuration:
            self.__configuration = get_configuration()

        return self.__configuration

    def get_translator(self) -> Translator:
        if not self.__translator:
            self.__translator = Translator(self.get_llm(), self.get_configuration())

        return self.__translator

    def get_llm(self) -> LLM:
        if not self.__llm:
            self.__llm = LLM(self.get_configuration())

        return self.__llm

    def get_review_modes(self) -> ReviewModes:
        if not self.__review_modes:
            self.__review_modes = ReviewModes(
                self.get_configuration(),
                self.get_reviewer(),
                self.get_token_counter(),
                self.get_sanitizer(),
            )

        return self.__review_modes

    def get_reviewer(self) -> Reviewer:
        if not self.__reviewer:
            self.__reviewer = Reviewer(self.get_llm())

        return self.__reviewer

    def get_token_counter(self) -> TokenCounter:
        if not self.__token_counter:
            self.__token_counter = TokenCounter("Qwen/Qwen3-8B")

        return self.__token_counter

    def get_sanitizer(self) -> Sanitizer:
        if not self.__sanitizer:
            self.__sanitizer = Sanitizer(self.get_llm(), self.get_ast_parser())

        return self.__sanitizer

    def get_ast_parser(self) -> ASTParser:
        if not self.__ast_parser:
            self.__ast_parser = ASTParser()

        return self.__ast_parser
