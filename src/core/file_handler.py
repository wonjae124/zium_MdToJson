import json
from pathlib import Path
from typing import Dict, List

from ..config.logging_config import setup_logging

# 로깅 설정
logger = setup_logging(__name__)


class FileHandler:
    """Handle file operations for markdown and JSON files."""

    def __init__(self, config):
        """Initialize with configuration."""
        self.input_dir = Path(config["directories"]["input_dir"])
        self.output_dir = (
            Path(config["directories"]["output_dir"])
            if config["directories"]["output_dir"]
            else self.input_dir
        )
        self.setup_directories()

    def setup_directories(self):
        """Create input and output directories if they don't exist."""
        # Create input directory if it doesn't exist
        if not self.input_dir.exists():
            logger.warning(f"Input directory does not exist: {self.input_dir}")
            self.input_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created input directory: {self.input_dir}")

        # Create output directory if it doesn't exist and is different from input directory
        if self.output_dir != self.input_dir and not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {self.output_dir}")

    def get_markdown_files(self, file_pattern: str = "*.md") -> List[Path]:
        """Get list of markdown files in input directory."""
        md_files = list(self.input_dir.glob(file_pattern))

        logger.info(f"Found {len(md_files)} markdown files in {self.input_dir}")
        return md_files

    def get_output_path(self, input_file: Path) -> Path:
        """Get output JSON path for given input markdown file."""
        return self.output_dir / f"{input_file.stem}.json"

    def read_md_file(self, file_path: Path) -> str:
        """Read content from a markdown file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.debug(f"Successfully read file: {file_path}")
            return content
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

    def save_json_file(self, md_file_path: Path, json_data: Dict) -> Path:
        """Save data as a JSON file."""
        # Create JSON file path with the same name but .json extension
        json_file_path = self.output_dir / f"{md_file_path.stem}.json"

        try:
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Successfully saved JSON file: {json_file_path}")
            return json_file_path
        except Exception as e:
            logger.error(f"Error saving JSON file {json_file_path}: {e}")
            raise
