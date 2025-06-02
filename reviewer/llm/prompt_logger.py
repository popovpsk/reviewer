import os

from reviewer.system_utils.os import clear_directory


class PromptLogger:
    def __init__(self):
        """Initializes the PromptLogger.
        Creates a 'reviewer_prompts' directory in the current working directory
        and clears it.
        """
        self.log_count = 0
        current_working_directory = os.getcwd()
        self.log_dir = os.path.join(current_working_directory, "reviewer_prompts")

        # Create the directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)

        # Clear the directory
        clear_directory(self.log_dir)

    def log_prompt(self, name: str, prompt: str, result: str):
        """Logs the prompt and its result to files in the instance's log_dir.

        Args:
            name: A descriptive name for the prompt, used in filenames.
            prompt: The input prompt string.
            result: The result string from the LLM.

        """
        sanitized_name = name.replace("/", ".")

        input_filename = os.path.join(self.log_dir, f"{self.log_count}_{sanitized_name}_input.txt")
        output_filename = os.path.join(self.log_dir, f"{self.log_count}_{sanitized_name}_output.txt")

        try:
            with open(input_filename, "w", encoding="utf-8") as file:
                file.write(prompt)
            with open(output_filename, "w", encoding="utf-8") as file:
                file.write(result)
        except IOError as e:
            print(f"Error writing log file: {e}")
            # It's generally better to let the exception propagate if the caller
            # might want to handle it, or if logging failure is critical.
            # For now, just printing and re-raising as per original logic.
            raise

        self.log_count += 1
