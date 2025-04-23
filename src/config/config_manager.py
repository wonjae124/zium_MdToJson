import argparse
import configparser
import os
from pathlib import Path
from typing import Dict

from .constants import *
from .logging_config import setup_logging

logger = setup_logging()


class ConfigManager:
    """Parse command line arguments and manage configuration."""

    DEFAULT_CONFIG_PATH = ROOT_DIR / "config.ini"

    def __init__(self):
        """Initialize configuration manager."""
        self.config = self._load_default_config()
        self._load_config_file()  # 먼저 설정 파일을 로드
        self._parse_args()  # 그 다음 명령줄 인자로 덮어쓰기

    def _load_default_config(self) -> Dict:
        """Load default configuration."""
        return {
            "directories": {
                "input_dir": str(ROOT_DIR / "data"),
                "output_dir": str(ROOT_DIR / "output"),
                "file_pattern": "*.md",
            },
            "logging": {
                "log_level": "INFO",
            },
            "llm_api": {
                "provider": "OpenAI",
                "model": "gpt-3.5-turbo",
                "api_key": os.environ.get("OPENAI_API_KEY", ""),
                "max_tokens": 4000,
                "temperature": 0.3,
                "retry_attempts": 3,
                "retry_delay": 5,
            },
            "parallel": {"enabled": True, "max_workers": 4},
            "fields": {"required": [], "optional": []},
            "regex_patterns": REGEX_PATTERNS,
        }

    def _parse_args(self):
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(
            description="Convert support program announcements from MD to JSON"
        )
        parser.add_argument(
            "--input-dir", "-i", type=str, help="Input directory containing MD files"
        )
        parser.add_argument("--output-dir", "-o", type=str, help="Output directory for JSON files")
        parser.add_argument("--config", "-c", type=str, help="Path to configuration file")
        parser.add_argument(
            "--log-level",
            type=str,
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            help="Logging level",
        )
        parser.add_argument("--workers", type=int, help="Number of parallel workers")
        parser.add_argument("--model", type=str, help="OpenAI model to use")

        args = parser.parse_args()

        # Update config with command line arguments
        if args.input_dir:
            self.config["directories"]["input_dir"] = args.input_dir
        if args.output_dir:
            self.config["directories"]["output_dir"] = args.output_dir
        if args.log_level:
            self.config["logging"]["log_level"] = args.log_level
        if args.workers:
            self.config["parallel"]["max_workers"] = args.workers
        if args.model:
            self.config["llm_api"]["model"] = args.model

        if args.config:
            self.config_file_path = Path(args.config)
            self._load_config_file()

    def _load_config_file(self):
        """Load configuration from INI file."""
        config_path = getattr(self, "config_file_path", self.DEFAULT_CONFIG_PATH)

        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}")
            return

        try:
            parser = configparser.ConfigParser()
            parser.read(config_path, encoding="utf-8")

            # directories 섹션
            if parser.has_section("directories"):
                self.config["directories"].update(dict(parser.items("directories")))

            # logging 섹션
            if parser.has_section("logging"):
                self.config["logging"].update(dict(parser.items("logging")))

            # llm_api 섹션
            if parser.has_section("llm_api"):
                llm_config = dict(parser.items("llm_api"))
                # 숫자형 값 변환
                for key in ["max_tokens", "retry_attempts", "retry_delay"]:
                    if key in llm_config:
                        llm_config[key] = int(llm_config[key])
                llm_config["temperature"] = float(
                    parser.get("llm_api", "temperature", fallback=0.3)
                )
                self.config["llm_api"].update(llm_config)

            # parallel 섹션
            if parser.has_section("parallel"):
                parallel_config = dict(parser.items("parallel"))
                parallel_config["enabled"] = parser.getboolean("parallel", "enabled", fallback=True)
                parallel_config["max_workers"] = int(
                    parser.get("parallel", "max_workers", fallback=4)
                )
                self.config["parallel"].update(parallel_config)

            # fields 섹션
            if parser.has_section("fields"):
                fields_config = {}
                if parser.has_option("fields", "required"):
                    fields_config["required"] = [
                        f.strip() for f in parser.get("fields", "required").split(",")
                    ]
                if parser.has_option("fields", "optional"):
                    fields_config["optional"] = [
                        f.strip() for f in parser.get("fields", "optional").split(",")
                    ]
                self.config["fields"].update(fields_config)

            # regex_patterns 섹션
            if parser.has_section("regex_patterns"):
                self.config["regex_patterns"].update(dict(parser.items("regex_patterns")))

            logger.info(f"Successfully loaded config from {config_path}")

        except Exception as e:
            logger.error(f"Error loading config file: {e}")

    def get_config(self) -> Dict:
        """Get the complete configuration."""
        return self.config
