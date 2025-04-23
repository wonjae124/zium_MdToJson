import json
import re
from pathlib import Path
from typing import Dict

from ..config.logging_config import LogMessageFormat, setup_logging

# 로깅 설정
logger = setup_logging(__name__)


class JSONGenerator:
    """Generate and validate JSON output."""

    def __init__(self, config: Dict):
        """Initialize with configuration."""
        self.config = config
        self.required_fields = config["fields"]["required"]
        self.optional_fields = config["fields"]["optional"]
        self.regex_patterns = config["regex_patterns"]

    def validate_json(self, data: Dict, file_name: str = "") -> bool:
        """Validate JSON data against required fields."""
        is_valid = True
        missing_fields = []

        # 필수 필드 검사
        for field in self.required_fields:
            if field not in data or not data[field]:
                logger.warning(LogMessageFormat.REQUIRED_FIELD_MISSING.format(file_name, field))
                missing_fields.append(field)
                is_valid = False

        # 모든 필드가 문자열인지 검사
        for field, value in data.items():
            if not isinstance(value, str):
                logger.error(
                    LogMessageFormat.FIELD_TYPE_ERROR.format(file_name, field, type(value))
                )
                return False

        # 필수 필드가 누락되어도 진행
        if not is_valid:
            logger.warning(f"{file_name} 필수 필드 누락: {', '.join(missing_fields)}")
            
        return True  # 항상 True를 반환하여 처리 계속 진행

    def generate_json(self, data: Dict, output_path: Path) -> bool:
        """Generate JSON file from data."""
        file_name = f"[{output_path.stem}]"
        try:
            # JSON 데이터 검증
            if not self.validate_json(data, file_name):
                # return False
                pass

            # JSON 파일 생성
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(LogMessageFormat.JSON_GENERATION_SUCCESS.format(file_name, output_path))
            return True

        except Exception as e:
            logger.error(LogMessageFormat.JSON_GENERATION_ERROR.format(file_name, e))
            return False

    def validate_and_normalize(self, parsed_data: Dict, file_name: str = "") -> Dict:
        """데이터 검증 및 정규화를 수행합니다."""
        # 1. 필수/선택 필드 확인 및 빈 값 처리
        parsed_data = self._validate_fields(parsed_data, file_name)
        
        # 2. 데이터 정규화
        parsed_data = self._normalize_data(parsed_data, file_name)
        
        return parsed_data

    def _validate_fields(self, data: Dict, file_name: str = "") -> Dict:
        """필수 및 선택 필드를 검증하고 누락된 필드를 빈 문자열로 초기화합니다."""
        # 필수 필드 확인
        for field in self.required_fields:
            if field not in data or not data[field]:
                logger.warning(LogMessageFormat.REQUIRED_FIELD_MISSING.format(file_name, field))
                data[field] = ""

        # 선택적 필드 확인
        for field in self.optional_fields:
            if field not in data:
                logger.debug(LogMessageFormat.OPTIONAL_FIELD_MISSING.format(file_name, field))
                data[field] = ""

        return data

    def _normalize_data(self, data: Dict, file_name: str = "") -> Dict:
        """데이터 형식을 정규화합니다."""
        # 이메일 형식 검증
        if "responsible_person_email" in data and data["responsible_person_email"]:
            if not re.match(self.regex_patterns["email"], data["responsible_person_email"]):
                logger.warning(
                    LogMessageFormat.EMAIL_FORMAT_ERROR.format(
                        file_name, data["responsible_person_email"]
                    )
                )

        # 전화번호 형식 검증 및 정규화
        if "tel_number" in data and data["tel_number"]:
            data["tel_number"] = self._normalize_phone(data["tel_number"], file_name)

        return data

    def _normalize_phone(self, phone_str: str, file_name: str = "") -> str:
        """전화번호를 표준 형식으로 정규화합니다."""
        if not phone_str:
            return phone_str

        # 특수문자 제거
        phone = re.sub(r"[^\d+]", "", phone_str)

        # 지역번호가 있는 경우 (예: 053-655-5609)
        area_pattern = r"^(\d{2,3})(\d{3,4})(\d{4})$"
        match = re.match(area_pattern, phone)
        if match:
            area, mid, end = match.groups()
            return f"{area}-{mid}-{end}"

        if not re.match(self.regex_patterns["phone"], phone_str):
            logger.warning(LogMessageFormat.PHONE_FORMAT_ERROR.format(file_name, phone_str))

        return phone_str
