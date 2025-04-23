from pathlib import Path

# File and Directory Paths
ROOT_DIR = Path(__file__).parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"
CONFIG_FILE = ROOT_DIR / "config.ini"

# File Patterns
MD_FILE_PATTERN = "*.md"
JSON_FILE_PATTERN = "*.json"

# Environment Variables
ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
ENV_LOG_LEVEL = "LOG_LEVEL"


# Regular Expression Patterns
REGEX_PATTERNS = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "phone": r"(?:\+\d{1,3}[-\s]?)?\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4}",
    "department": r"([가-힣]+(?:과|팀|실|국|부))[^\n]*?([가-힣]{2,4})\s*(?=담당|$)",
    "date": r"\d{4}[./-]\d{1,2}[./-]\d{1,2}",
    "title": r"^#\s+(.+)$",
    "contact_section": r"(?:문의처|담당자|연락처|문의)[\s:]*\n*((?:[^\n]+\n?)+)",
    "application_section": r"(?:신청방법|접수방법|지원방법)[\s:]*\n*((?:[^\n]+\n?)+)",
}

# Default Configuration
DEFAULT_CONFIG = {
    "directories": {
        "input_dir": str(ROOT_DIR / "data"),
        "output_dir": None,
        "file_pattern": MD_FILE_PATTERN,
    },
    "logging": {
        "log_level": ENV_LOG_LEVEL,
    },
    "llm_api": {
        "provider": "OpenAI",
        # "model": "gpt-4o-mini",
        "model": "gpt-3.5-turbo",
        "max_tokens": 4000,
        "temperature": 0.3,
        "retry_attempts": 3,
        "retry_delay": 5,
    },
    "parallel": {"enabled": True, "max_workers": 4},
    "regex_patterns": REGEX_PATTERNS,
}

# Error Messages
ERROR_MESSAGES = {
    "api_key_missing": "OpenAI API key is missing. Please set it in .env file or environment variables.",
    "input_dir_not_found": "Input directory does not exist: {}",
    "output_dir_not_found": "Output directory does not exist: {}",
    "file_read_error": "Error reading file {}: {}",
    "file_write_error": "Error writing file {}: {}",
    "parsing_error": "Error parsing content: {}",
}

# 상수 그룹
FILE_CONSTANTS = ["ROOT_DIR", "ENV_FILE", "CONFIG_FILE"]

ENV_CONSTANTS = ["ENV_OPENAI_API_KEY", "ENV_LOG_LEVEL"]

FIELD_CONSTANTS = ["DEFAULT_CONFIG"]

PATTERN_CONSTANTS = ["REGEX_PATTERNS"]

ERROR_CONSTANTS = ["ERROR_MESSAGES"]

CONFIG_CONSTANTS = ["DEFAULT_CONFIG"]

# 모든 상수 그룹을 __all__에 포함
__all__ = (
    FILE_CONSTANTS
    + ENV_CONSTANTS
    + FIELD_CONSTANTS
    + PATTERN_CONSTANTS
    + ERROR_CONSTANTS
    + CONFIG_CONSTANTS
)
