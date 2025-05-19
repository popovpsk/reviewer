import logging
from reviewer.locator.service_locator import ServiceLocator

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

def main():
   locator = ServiceLocator()
   processor = locator.get_reviewer_processor()
   processor.process_review()

if __name__ == "__main__":
    main()
