from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import os

from .file_handler import FileHandler
from .markdown_preprocessor import MarkdownPreprocessor
from .llm_parser import LLMParser
from .json_generator import JSONGenerator
from .hwp_to_md import convert_hwp_to_md, find_hwp_files
from .pdf_to_md import convert_pdf_to_md, find_pdf_files
from ..config.logging_config import setup_logging, LogMessageFormat
from ..models.database import BizSupport

# 로깅 설정
logger = setup_logging(__name__)


class ProcessManager:
    """Manage the overall process of converting MD files to JSON."""

    def __init__(self, config: Dict):
        """Initialize with configuration."""
        self.config = config
        self.file_handler = FileHandler(config)
        self.md_preprocessor = MarkdownPreprocessor()
        self.llm_parser = LLMParser(config)
        self.json_generator = JSONGenerator(config)

        # 병렬 처리 설정
        self.parallel_config = config["parallel"]

        self.stats = {"total_files": 0, "successful": 0, "failed": 0, "total_time": 0}

        logger.info("ProcessManager initialized")

    def process_single_file(self, md_file: Path) -> bool:
        """Process a single markdown file."""
        try:
            file_name = f"[{md_file.name}]"
            logger.info(LogMessageFormat.FILE_PROCESSING_START.format(file_name))

            # 마크다운 파일 읽기
            content = self.file_handler.read_md_file(md_file)

            # 마크다운 전처리
            preprocessed_content = self.md_preprocessor.preprocess(content)

            # LLM으로 내용 파싱
            parsed_data = self.llm_parser.parse_with_llm(preprocessed_content)
            logger.info(f"LLM 파싱 결과: {parsed_data}")

            # 필수 필드 확인
            logger.info("필수 필드 체크 시작")
            has_required = self._check_required_fields(parsed_data)
            logger.info(f"필수 필드 체크 결과: {has_required}")

            # 필수 필드가 누락된 경우 PDF/HWP 처리 시도
            if not has_required:
                # PDF 파일 처리 시도
                logger.warning(f"{file_name} 필수 정보 누락, PDF 파일 처리 시도")
                pdf_result = self._process_pdf_file(md_file)
                if pdf_result:
                    # PDF 결과와 기존 데이터 병합
                    parsed_data = self._merge_data(parsed_data, pdf_result)
                    logger.info(f"PDF 파일 처리 결과와 병합됨: {parsed_data}")

                # HWP 파일 처리 시도
                logger.warning(f"{file_name} HWP 파일 처리 시도")
                hwp_result = self._process_hwp_file(md_file)
                if hwp_result:
                    # HWP 결과와 기존 데이터 병합
                    parsed_data = self._merge_data(parsed_data, hwp_result)
                    logger.info(f"HWP 파일 처리 결과와 병합됨: {parsed_data}")

            # 파일 정보 추가
            parsed_data["original_file_name"] = md_file.name
            parsed_data["file_path"] = str(md_file.absolute())

            # 데이터 검증 및 정규화
            parsed_data = self.json_generator.validate_and_normalize(parsed_data, file_name)

            # JSON 파일 생성
            output_path = self.file_handler.get_output_path(md_file)
            success = self.json_generator.generate_json(parsed_data, output_path)

            if success:
                logger.info(LogMessageFormat.FILE_PROCESSING_SUCCESS.format(file_name))
            else:
                logger.error(LogMessageFormat.FILE_PROCESSING_FAILED.format(file_name))

            return success

        except Exception as e:
            logger.error(LogMessageFormat.FILE_PROCESSING_ERROR.format(file_name, str(e)))
            return False

    def process_all_files(self) -> bool:
        """마크다운 파일들을 병렬 또는 순차적으로 처리합니다."""
        try:
            # 마크다운 파일 목록 가져오기
            md_files = self.file_handler.get_markdown_files(
                self.config["directories"]["file_pattern"]
            )
            if not md_files:
                logger.warning(
                    f"{LogMessageFormat.SYSTEM_PREFIX} 처리할 마크다운 파일을 찾을 수 없습니다."
                )
                return False

            total_files = len(md_files)
            success_count = 0
            failed_files = []  # 실패한 파일들을 추적

            # 처리 방식 결정 (병렬 또는 순차)
            if self.parallel_config["enabled"] and total_files > 1:
                logger.info(
                    f"{LogMessageFormat.SYSTEM_PREFIX} 병렬 처리 시작: {self.parallel_config['max_workers']}개의 작업자로 처리합니다."
                )
                success_count, failed_files = self._process_files_parallel(md_files)
            else:
                logger.info(f"{LogMessageFormat.SYSTEM_PREFIX} 순차 처리 시작")
                success_count, failed_files = self._process_files_sequential(md_files)

            # 처리 결과 보고
            self._report_processing_results(total_files, success_count, failed_files)

            return len(failed_files) == 0

        except Exception as e:
            logger.error(f"{LogMessageFormat.SYSTEM_PREFIX} 일괄 처리 중 오류 발생: {e}")
            return False

    def _process_files_parallel(self, md_files: List[Path]) -> tuple[int, List[Path]]:
        """파일들을 병렬로 처리합니다."""
        success_count = 0
        failed_files = []

        # ThreadPoolExecutor를 사용하여 병렬 처리
        with ThreadPoolExecutor(max_workers=self.parallel_config["max_workers"]) as executor:
            # 각 파일에 대한 처리 작업 제출
            future_to_file = {
                executor.submit(self.process_single_file, md_file): md_file for md_file in md_files
            }

            # 완료되는 작업들을 순서대로 처리
            for future in as_completed(future_to_file):
                md_file = future_to_file[future]
                file_name = f"[{md_file.name}]"
                try:
                    if future.result():
                        success_count += 1
                    else:
                        failed_files.append(md_file)
                except Exception as e:
                    failed_files.append(md_file)
                    logger.error(LogMessageFormat.FILE_PROCESSING_ERROR.format(file_name, e))

        return success_count, failed_files

    def _process_files_sequential(self, md_files: List[Path]) -> tuple[int, List[Path]]:
        """파일들을 순차적으로 처리합니다."""
        success_count = 0
        failed_files = []

        for md_file in md_files:
            file_name = f"[{md_file.name}]"
            try:
                if self.process_single_file(md_file):
                    success_count += 1
                else:
                    failed_files.append(md_file)
            except Exception as e:
                failed_files.append(md_file)
                logger.error(LogMessageFormat.FILE_PROCESSING_ERROR.format(file_name, e))

        return success_count, failed_files

    def _report_processing_results(
        self, total_files: int, success_count: int, failed_files: List[Path]
    ):
        """처리 결과를 로그에 기록합니다."""
        logger.info(LogMessageFormat.REPORT_HEADER)
        logger.info(LogMessageFormat.REPORT_TITLE.format(LogMessageFormat.SYSTEM_PREFIX))
        logger.info(LogMessageFormat.REPORT_HEADER)
        logger.info(LogMessageFormat.REPORT_TOTAL_FILES.format(total_files))
        logger.info(LogMessageFormat.REPORT_SUCCESS_COUNT.format(success_count))
        logger.info(LogMessageFormat.REPORT_FAILED_COUNT.format(len(failed_files)))

        if failed_files:
            logger.info(LogMessageFormat.REPORT_FAILED_FILES_HEADER)
            for file in failed_files:
                logger.info(f"- [{file.name}]")

        success_rate = (success_count / total_files * 100) if total_files > 0 else 0
        logger.info(LogMessageFormat.REPORT_SUCCESS_RATE.format(success_rate))
        logger.info(LogMessageFormat.REPORT_HEADER)

    def generate_report(self):
        """Generate a report of the processing results."""
        logger.info(LogMessageFormat.REPORT_HEADER)
        logger.info(LogMessageFormat.REPORT_TITLE.format(LogMessageFormat.SYSTEM_PREFIX))
        logger.info(LogMessageFormat.REPORT_HEADER)
        logger.info(LogMessageFormat.REPORT_TOTAL_FILES.format(self.stats["total_files"]))
        logger.info(LogMessageFormat.REPORT_SUCCESS_COUNT.format(self.stats["successful"]))
        logger.info(LogMessageFormat.REPORT_FAILED_COUNT.format(self.stats["failed"]))

        if self.stats["total_files"] > 0:
            success_rate = (self.stats["successful"] / self.stats["total_files"]) * 100
            logger.info(LogMessageFormat.REPORT_SUCCESS_RATE.format(success_rate))

            if self.stats["successful"] > 0:
                avg_time = self.stats["total_time"] / self.stats["successful"]
                logger.info(
                    f"{LogMessageFormat.SYSTEM_PREFIX} 파일당 평균 처리 시간: {avg_time:.2f}초"
                )

        logger.info(LogMessageFormat.REPORT_HEADER)

    def _check_required_fields(self, data: Dict) -> bool:
        """필수 필드가 모두 있는지 확인
        하나라도 없거나 빈 문자열이면 False를 반환"""
        required_fields = self.config["fields"]["required"]
        logger.info(f"필수 필드 목록: {required_fields}")
        logger.info(f"검사할 데이터: {data}")

        for field in required_fields:
            value = data.get(field)
            logger.info(f"필드 '{field}' 값: {value}")
            if not value or value.strip() == "":  # 값이 없거나 빈 문자열이면
                logger.info(f"필수 필드 '{field}' 누락 또는 빈 값")
                return False
        return True

    def _process_hwp_file(self, md_file: Path) -> Optional[Dict]:
        """마크다운 파일과 동일한 디렉토리에서 HWP 파일을 찾아 처리합니다."""
        try:
            # 마크다운 파일이 있는 디렉토리와 data 폴더에서 HWP 파일 찾기
            directory = str(md_file.parent)
            hwp_files = find_hwp_files(directory, md_file.name)

            if not hwp_files:
                logger.warning(f"[{md_file.name}] 관련 HWP 파일을 찾을 수 없습니다.")
                return None

            # 마크다운 파일명과 가장 유사한 HWP 파일 선택
            md_name = md_file.stem.lower()
            matching_hwp = None

            for hwp_file in hwp_files:
                hwp_name = Path(hwp_file).stem.lower()
                if md_name in hwp_name or hwp_name in md_name:
                    matching_hwp = hwp_file
                    break

            if not matching_hwp:
                # 매칭되는 파일이 없으면 첫 번째 HWP 파일 사용
                matching_hwp = hwp_files[0]

            logger.info(f"[{md_file.name}] HWP 파일 발견: {matching_hwp}")
            # HWP 파일을 마크다운으로 변환
            # 임시 출력 경로 생성
            temp_dir = self.file_handler.output_dir / "temp"
            temp_md_path = temp_dir / f"{Path(matching_hwp).stem}_converted.md"

            if not convert_hwp_to_md(matching_hwp, str(temp_md_path)):
                logger.error(f"[{md_file.name}] HWP 파일 변환 실패")
                return None

            try:
                # 변환된 마크다운 파일 읽기
                converted_content = self.file_handler.read_md_file(temp_md_path)

                # 변환된 마크다운 전처리
                preprocessed_content = self.md_preprocessor.preprocess(converted_content)

                # LLM으로 내용 파싱
                parsed_data = self.llm_parser.parse_with_llm(preprocessed_content)
                logger.info(f"HWP 파일로부터 파싱된 데이터: {parsed_data}")

                return parsed_data

            finally:
                # 임시 파일 삭제
                try:
                    os.remove(temp_md_path)
                except Exception as e:
                    logger.warning(f"임시 파일 삭제 실패: {str(e)}")

        except Exception as e:
            logger.error(f"[{md_file.name}] HWP 파일 처리 중 오류 발생: {str(e)}")
            return None

    def _process_pdf_file(self, md_file: Path) -> Optional[Dict]:
        """PDF 파일을 처리하여 마크다운으로 변환하고 파싱합니다."""
        try:
            # PDF 파일 찾기
            pdf_files = find_pdf_files(str(md_file.parent), md_file.stem)
            if not pdf_files:
                logger.warning(f"PDF 파일을 찾을 수 없습니다: {md_file.stem}")
                return None

            # PDF를 마크다운으로 변환
            pdf_file = pdf_files[0]  # 첫 번째 PDF 파일 사용
            temp_md_path = md_file.parent / f"{md_file.stem}_pdf.md"
            
            if convert_pdf_to_md(pdf_file, str(temp_md_path)):
                # 변환된 마크다운 파일 읽기
                with open(temp_md_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 마크다운 전처리
                preprocessed_content = self.md_preprocessor.preprocess(content)

                # LLM으로 내용 파싱
                parsed_data = self.llm_parser.parse_with_llm(preprocessed_content)

                # 임시 파일 삭제
                os.remove(temp_md_path)

                return parsed_data

            return None

        except Exception as e:
            logger.error(f"PDF 파일 처리 중 오류 발생: {str(e)}")
            return None

    def _merge_data(self, original_data: Dict, new_data: Dict) -> Dict:
        """두 데이터 딕셔너리를 병합합니다. 새 데이터의 비어있지 않은 필드가 기존 데이터의 빈 필드를 대체합니다."""
        merged_data = original_data.copy()
        
        for field, value in new_data.items():
            # 새 데이터의 필드가 비어있지 않고, 기존 데이터의 필드가 비어있으면 대체
            if value and value.strip() and (field not in merged_data or not merged_data[field].strip()):
                merged_data[field] = value

        return merged_data

    def save_to_db(self, data: Dict, db: Session, file_name: str) -> bool:
        """데이터를 데이터베이스에 저장 또는 업데이트"""
        try:
            # 1. 같은 파일명으로 저장된 데이터가 있는지 검색
            existing = db.query(BizSupport).filter_by(
                original_file_name=data["original_file_name"]
            ).first()

            if existing:
                # 2. 기존 데이터가 있으면 업데이트
                for field, value in data.items():
                    # 새로운 값이 있을 때만 업데이트 (빈 값이나 공백은 무시)
                    if value and value.strip():
                        setattr(existing, field, value)
                logger.info(f"기존 데이터 업데이트: {file_name}")
            else:
                # 3. 기존 데이터가 없으면 새로 생성
                # data 딕셔너리의 키-값을 BizSupport 클래스 생성자에 전달
                db_item = BizSupport(**data)
                db.add(db_item)
                logger.info(f"새 데이터 추가: {file_name}")

            # 4. 변경사항 저장
            db.commit()
            return True
        except Exception as e:
            # 5. 오류 발생시 변경사항 취소
            db.rollback()
            logger.error(f"{file_name} 데이터베이스 저장 중 오류 발생: {str(e)}")
            return False
