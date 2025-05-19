import logging
import os

from reviewer.agents.translator import Translator
from reviewer.config.reviewer_config import Configuration, ReviewMode
from reviewer.processor.review_modes import ReviewModes
from reviewer.system_utils.diff import DiffFile
from reviewer.system_utils.diff import diff_master,get_git_diff_files

class ReviewerProcessor:
    def __init__(self, config: Configuration, translator: Translator, review_modes: ReviewModes):
        self.config = config
        self.__translator = translator
        self.__review_modes = review_modes

    def process_review(self):
        os.chdir(self.config.repo)
        diff_master(self.config.target_branch)
        diffs = get_git_diff_files("master", self.config.target_branch)
        diffs = self.__filter_files_to_review(diffs, self.config)

        logging.info(
            f"repo: {self.config.repo}, branch: {self.config.target_branch}\nreview_test_files: {self.config.review_test_files}\nmode: {self.config.review_mode}")
        logging.info(f"files to review:\n{str.join("\n", [d.full_name for d in diffs])}")
        logging.info(f"inference provider: {self.config.inference_provider}")
        logging.info(f"translate enabled: {self.config.translate_enabled}")

        output_results: list[str] = []

        if self.config.review_mode == ReviewMode.FileByFile:
            output_results = self.__review_modes.file_by_file(diffs)

        elif self.config.review_mode == ReviewMode.AllFilesAtOnce:
            output_results = self.__review_modes.all_files_at_once(diffs)

        elif self.config.review_mode == ReviewMode.PackageByPackage:
            output_results = self.__review_modes.package_by_package(diffs)

        elif self.config.review_mode == ReviewMode.Auto:
            output_results = self.__review_modes.auto(diffs)

        final_output = str.join("\n", output_results)

        if self.config.translate_enabled and final_output:
            print(self.__translator.translate(final_output))
        elif final_output:
            print(final_output)
        else:
            logging.info("No review results to display.")


    @staticmethod
    def __filter_files_to_review(src: list[DiffFile], config: Configuration) -> list[DiffFile]:
        def skip(x: DiffFile) -> bool:
            return (
                ".pb." in x.name or
                "mock" in x.full_name and "smartmock" not in x.full_name or
                x.full_name.startswith("pkg/") or
                x.name.endswith("swagger.json") or
                x.name == "mimir.yaml" or
                "_test" in x.name and not config.review_test_files or # go tests
                "src/api/generated" in x.full_name or # seller-ui generated clients
                "framework/data/schemas/" in x.full_name or # python tests
                "framework/clients/api_client.py" in x.full_name or # python tests
                "pb/" in x.full_name and (x.name.endswith(".py") or x.name.endswith(".pyi")) or
                x.name in ["go.mod", "go.sum", "poetry.lock", "pyproject.toml"]
            )
        return [x for x in src if not skip(x)]
