import os
from pathlib import Path

import kagglehub
from dotenv import load_dotenv


class KaggleDatasetConnector:
    def __init__(
        self,
        dataset: str = "wspirat/poland-used-cars-offers",
        env_file: Path = Path(".env"),
    ) -> None:
        self.dataset = dataset
        load_dotenv(env_file)

        self.kaggle_api_token = os.getenv("KAGGLE_API_TOKEN")

    def fetch_latest(self) -> None:
        kagglehub.dataset_download(self.dataset, output_dir="./data", force_download=True)


if __name__ == "__main__":
    KaggleDatasetConnector().fetch_latest()
