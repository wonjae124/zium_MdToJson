import logging
import sys
from pathlib import Path
from typing import Optional

# 로그 파일 경로 설정
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "app.log"

# 로그 포맷 설정 (파일명과 라인 번호 추가)
LOG_FORMAT = "%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s"


# 로그 메시지 형식
class LogMessageFormat:
    # 시스템 관련
    SYSTEM_PREFIX = "[시스템]"

    # 파일 처리 관련
    FILE_PROCESSING_START = "{} 파일 처리 시작"
    FILE_PROCESSING_SUCCESS = "{} 처리 성공"
    FILE_PROCESSING_FAILED = "{} 처리 실패"
    FILE_PROCESSING_ERROR = "{} 처리 중 오류 발생: {}"

    # JSON 생성 관련
    JSON_GENERATION_SUCCESS = "{} JSON 파일 생성 완료: {}"
    JSON_GENERATION_ERROR = "{} JSON 파일 생성 중 오류 발생: {}"

    # 필드 검증 관련
    REQUIRED_FIELD_MISSING = "{} 필수 필드 누락 또는 비어있음: {}"
    FIELD_TYPE_ERROR = "{} 필드 타입 오류 - {}: 문자열이어야 하나 {} 타입임"
    OPTIONAL_FIELD_MISSING = "{} 선택적 필드 '{}' 누락 - 빈 문자열로 설정"

    # 데이터 형식 검증 관련
    DATE_FORMAT_ERROR = "{} 날짜 형식 오류 - {}: {}"
    EMAIL_FORMAT_ERROR = "{} 이메일 형식 오류: {}"
    PHONE_FORMAT_ERROR = "{} 전화번호 형식 오류: {}"

    # 처리 결과 보고서
    REPORT_HEADER = "=" * 50
    REPORT_TITLE = "{} 처리 결과 보고서"
    REPORT_TOTAL_FILES = "전체 파일 수: {}"
    REPORT_SUCCESS_COUNT = "성공: {}"
    REPORT_FAILED_COUNT = "실패: {}"
    REPORT_FAILED_FILES_HEADER = "\n실패한 파일 목록:"
    REPORT_SUCCESS_RATE = "\n성공률: {:.1f}%"


def setup_logging(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """애플리케이션 전체의 로깅 설정

    Args:
        name: 로거 이름 (None인 경우 호출한 모듈의 이름 사용)
        level: 로깅 레벨 (기본값: INFO)

    Returns:
        설정된 로거 인스턴스
    """
    # 기본 로깅 설정
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    # 로거 생성
    logger = logging.getLogger(name if name else __name__)
    logger.setLevel(level)

    return logger
