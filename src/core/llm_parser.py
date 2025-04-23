import json
import time
from typing import Dict

from openai import OpenAI

from ..config.logging_config import setup_logging

# 로깅 설정
logger = setup_logging(__name__)


class LLMParser:
    """Parse markdown content using LLM API."""

    def __init__(self, config: Dict):
        """Initialize with configuration."""
        self.config = config
        self.llm_config = config["llm_api"]
        self.required_fields = config["fields"]["required"]
        self.optional_fields = config["fields"]["optional"]
        self.regex_patterns = config["regex_patterns"]

        # OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=self.llm_config["api_key"])

        logger.info("LLMParser initialized with model: %s", self.llm_config["model"])

    def create_prompt(self, content: str) -> str:
        """Create prompt for the LLM."""
        prompt = f"""당신은 특화된 데이터 추출 시스템입니다.
당신의 임무는 아래의 지원사업 공고에서 특정 정보를 추출하고, JSON 형식으로 출력하는 것입니다.

공고 내용에서 다음 항목들을 추출해주세요:
- 정책지원금번호, 공고일련번호, 서비스ID (sme_subvention_id): 예) "제2025-095호" 또는 형식으로, 공고 내 명시된 정보를 추출
- 정책지원금제목, 보조금 사업 명, 지원사업에 대한 공고명 (title_name)
- 소관부처명, 지원사업의 주관기관, 보조금 서비스 소관 기관명 (reception_institution_name): 공고 제목이나 내용에서 언급된 주관/시행 기관명 추출 (예: 부산테크노파크, 중소벤처기업진흥공단 등)
- 사업개요내용, 지원사업의 주요 내용, 사업 공고의 주요 내용, 보조금 사업의 목적을 요약 (business_overview_content)
- 지원내용, 보조금 서비스의 상세한 지원 내용, 지원예산액의 세부지원금액 기술 내용, 사업 수행 기간, 협약 기간 (support_content)
- 공고게시일, 지원사업 공고일자, 공모내역의 공고 시작일자 (notice_date)
- 지원자격내용, 보조금 서비스 지원대상과 조건, 지원 가능한 대상 기술 내용 (support_qualification_content)
- 접수시작일, 사업 지원신청 접수시작일자, 접수시작시각 (reception_start_date)
- 접수종료일, 사업 지원신청 접수종료일자, 접수종료시각 (reception_end_date)
- 등록일시, 보조금 사업정보를 최초로 등록한 일시, 작성일, 게시일, 날 (registered_at)
- 지원금액, 공모사업의 지원예산액, 최대 지원금액(원) (support_amount)
- 지역명, 행사 지원 지역명  (area_name): 예) 서울, 충남 등
- 홈페이지주소, 공고URL, 사업 안내 URL, 출처URL (url_address)
- 신청방법내용, 사업 지원신청 접수 방법 기술, 지원사업 신청 방법, 보조급 서비스 신청방법 - 예)방문, 온라인, 직접입력, 신청불필요, 기타, 제출서류안내내용  (application_way_content)
- 담당부서명, 소관부처의 담당부서, 공고 담당자의 소속 (responsible_division_name)
- 담당자명, 공고 담당자의 이름 (responsible_person_name)
- 담당자이메일 (responsible_person_email)
- 담당자전화번호, 지원사업에 대한 공고 담당자의 전화번호, 소관부처의 담당 전화번호 (tel_number)

다음 필드들은 반드시 포함되어야 합니다 (필수):
{", ".join(self.required_fields)}

다음 필드들도 정보가 있다면 반드시 포함해주세요 (선택):
{", ".join(self.optional_fields)}

출력 규칙:
1. 모든 필드는 문자열(string) 형식이어야 합니다.
2. 여러 항목이 있는 경우 쉼표(,)로 구분합니다.
3. 금액은 숫자와 단위를 포함하여 명시합니다.
4. URL은 전체 URL을 포함합니다.
5. 이메일과 전화번호는 제공된 형식 그대로 유지합니다.
6. 부서명과 담당자명은 제공된 형식 그대로 유지합니다.
7. 항목이 텍스트에 존재하지 않을 경우 빈 문자열 ""로 채워주세요.
8. 공고내용은 원문 형식을 유지해주세요.
9. 공고 텍스트에 실제로 명시된 정보만 추출해주세요.
10. 필수 필드는 반드시 포함해야 하며, 선택 필드도 가능한 한 모두 추출해주세요.
11. 정보가 명확하지 않더라도, 문맥상 유추 가능한 정보는 추출해주세요.

아래는 공고 원문입니다:

{content}

JSON 형식으로만 출력해주세요. 설명이나 기타 텍스트는 포함하지 마세요."""

        return prompt

    def parse_with_llm(self, content: str) -> Dict:
        """Parse content using LLM API."""
        prompt = self.create_prompt(content)
        for attempt in range(self.llm_config["retry_attempts"]):
            try:
                response = self.client.responses.create(
                    model=self.llm_config["model"],
                    instructions="다음 텍스트에서 정보를 추출하여 JSON 형식으로 정리하세요.",
                    input=prompt,
                )

                # 응답에서 JSON 부분 추출
                result_text = response.output_text.strip()
                if result_text.startswith("```json"):
                    result_text = result_text[7:-3].strip()
                elif result_text.startswith("```"):
                    result_text = result_text[3:-3].strip()

                result = json.loads(result_text)
                logger.debug("Successfully parsed content with LLM")

                return result

            except Exception as e:
                logger.warning(f"Responses API attempt {attempt + 1} failed: {e}")
                if attempt < self.llm_config["retry_attempts"] - 1:
                    time.sleep(self.llm_config["retry_delay"] * (2**attempt))
                else:
                    logger.error("All Responses API attempts failed.")
                    return self._create_empty_result()

    def _create_empty_result(self) -> Dict:
        """LLM 파싱 실패 시 빈 결과를 생성합니다."""
        result = {}
        # 모든 필수 필드를 빈 문자열로 초기화
        for field in self.required_fields:
            result[field] = ""
        # 모든 선택 필드를 빈 문자열로 초기화
        for field in self.optional_fields:
            result[field] = ""
        return result

    def safe_file_operations(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                f.read()
        except FileNotFoundError:
            logger.error(f"파일을 찾을 수 없습니다: {file_path}")
            raise
        except PermissionError:
            logger.error(f"파일 접근 권한이 없습니다: {file_path}")
            raise
        except UnicodeDecodeError:
            logger.error(f"파일 인코딩 오류: {file_path}")
            raise

