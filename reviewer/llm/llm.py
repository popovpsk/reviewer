import logging
import re
from typing import Callable

from openai import OpenAI

from reviewer.config.reviewer_config import (
    InferenceProvider,
    MODEL_API_KEY, MODEL_BASE_URL, FALLBACK_MODEL_BASE_URL, FALLBACK_MODEL_API_KEY, MODEL_NAME,
    FALLBACK_MODEL_NAME, Configuration,
)
from reviewer.llm.prompt_logger import PromptLogger # Import the new logger

class LLM:
    def __init__(self, configuration: Configuration):
        self.__config = configuration
        self.__prompt_logger = PromptLogger() # Instantiate the logger

        self.__model = OpenAI(
            api_key=MODEL_API_KEY, base_url=MODEL_BASE_URL
        )
        self.__fallback_model = OpenAI(api_key=FALLBACK_MODEL_API_KEY, base_url=FALLBACK_MODEL_BASE_URL)

        if configuration.inference_provider == InferenceProvider.LlamaCpp:
            # Ensure that models.list() and its data attribute are valid before accessing.
            # This assumes the API client behaves as expected.
            try:
                models_data = self.__fallback_model.models.list().data
                if models_data: # Check if the list is not empty
                    logging.info(f"llama.cpp model: {models_data[0].id}")
                else:
                    logging.warning("llama.cpp model list is empty.")
            except Exception as e:
                logging.error(f"Failed to retrieve llama.cpp model list: {e}")


    def generate(self, name: str, prompt: str) -> str:
        llm_executor: Callable[[str], str] = {
            InferenceProvider.LlamaCpp: self.__generate_llama,
            InferenceProvider.BigModel: self.__generate_with_fallback_llama,
        }[self.__config.inference_provider]
        result = llm_executor(prompt)
        self.__prompt_logger.log_prompt(name, prompt, result) # Use the logger instance
        return result

    def __generate(self, prompt: str) -> str:
        response = self.__model.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        if response.usage: # Check if usage data is available
            logging.info(
                f"prompt_eval_count:{response.usage.prompt_tokens}, total_tokens:{response.usage.total_tokens}, eval:{response.usage.total_tokens-response.usage.prompt_tokens}"
            )
        else:
            logging.warning("Usage data not available in response from primary model.")

        content = response.choices[0].message.content.strip()
        content = self.__remove_think_blocks(content)
        return self.__remove_code_fence(content)

    def __generate_llama(self, prompt: str) -> str:
        response = self.__fallback_model.chat.completions.create(
            model=FALLBACK_MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        if response.usage: # Check if usage data is available
            logging.info(
                f"prompt_eval_count:{response.usage.prompt_tokens}, total_tokens:{response.usage.total_tokens}, eval:{response.usage.total_tokens - response.usage.prompt_tokens}"
            )
        else:
            logging.warning("Usage data not available in response from fallback (llama) model.")

        content = response.choices[0].message.content.strip()
        content = self.__remove_think_blocks(content)
        return self.__remove_code_fence(content)

    def __generate_with_fallback_llama(self, prompt: str) -> str:
        try:
            return self.__generate(prompt)
        except BaseException as e: # Consider catching more specific exceptions
            logging.error(f"LLM error with primary model: {e}, falling back to local model.")
            return self.__generate_llama(prompt)

    @staticmethod
    def __remove_think_blocks(text: str) -> str:
        # Removes all <think>...</think> blocks including content
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    @staticmethod
    def __remove_code_fence(text: str) -> str:
        # Regex to find ``` or ```language
        pattern = r"```(?:\w+)?"
        # Replace all occurrences with an empty string
        result = re.sub(pattern, "", text)
        return result
