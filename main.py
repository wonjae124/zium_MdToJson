import json
from pathlib import Path

from src.config.config_manager import ConfigManager
from src.config.logging_config import setup_logging
from src.core.process_manager import ProcessManager
from src.models.database import SessionLocal, init_db

# 로깅 설정
logger = setup_logging(__name__)


def process_files():
    """마크다운 파일을 처리하고, 필요한 경우 PDF/HWP 파일을 변환하여 JSON으로 변환 후 DB에 저장"""

    # 설정 로드
    config_manager = ConfigManager()
    config = config_manager.get_config()

    # 프로세스 매니저 초기화
    process_manager = ProcessManager(config)

    # 데이터베이스 초기화
    init_db()

    # 입출력 디렉토리 설정
    input_dir = Path(config["directories"]["input_dir"])
    output_dir = (
        Path(config["directories"]["output_dir"])
        if config["directories"]["output_dir"]
        else input_dir
    )

    # 마크다운 파일 목록 가져오기
    md_files = list(input_dir.rglob("*.md"))  # 하위 디렉토리 포함 검색
    logger.info(f"총 {len(md_files)}개의 마크다운 파일을 처리합니다.")

    # 출력 디렉토리 생성
    output_dir.mkdir(exist_ok=True)

    # 데이터베이스 세션 생성
    db = SessionLocal()
    try:
        # 각 파일 처리
        for idx, md_file in enumerate(md_files, 1):
            logger.info(f"[{idx}/{len(md_files)}] {md_file.name} 처리 중...")

            try:
                # ProcessManager를 통한 파일 처리
                success = process_manager.process_single_file(md_file)

                if success:
                    # JSON 파일에서 처리된 데이터 읽기
                    json_path = output_dir / f"{md_file.stem}.json"
                    with open(json_path, "r", encoding="utf-8") as f:
                        parsed_data = json.load(f)

                    # 데이터베이스에 저장
                    if process_manager.save_to_db(parsed_data, db, md_file.name):
                        logger.info(f"{md_file.name} 처리 완료")
                    else:
                        logger.error(f"{md_file.name} 데이터베이스 저장 실패")
                else:
                    logger.error(f"{md_file.name} 처리 실패")

            except Exception as e:
                logger.error(f"{md_file.name} 처리 중 오류 발생: {str(e)}")
                continue

    finally:
        db.close()
        logger.info("모든 처리가 완료되었습니다.")


if __name__ == "__main__":
    process_files()
