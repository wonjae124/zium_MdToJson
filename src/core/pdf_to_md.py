import os
import re
from pathlib import Path

import fitz  # PyMuPDF

from .markdown_preprocessor import MarkdownPreprocessor
from .llm_parser import LLMParser
from .json_generator import JSONGenerator
from ..config.logging_config import setup_logging

# 로깅 설정
logger = setup_logging(__name__)


def convert_text_to_markdown(text: str, blocks: list) -> str:
    """
    추출된 텍스트를 Markdown 형식으로 변환합니다.

    Args:
        text (str): 변환할 텍스트
        blocks (list): PDF 블록 정보
    Returns:
        str: Markdown 형식으로 변환된 텍스트
    """
    markdown_lines = []
    in_list = False

    # 제목 처리 (폰트 크기 기반)
    for block in blocks:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    # 제목으로 추정되는 텍스트 식별 (폰트 크기로 판단)
                    if span["size"] > 12:  # 임계값 조정 필요
                        text = text.replace(span["text"], f"## {span['text']}")

    # 텍스트 처리
    lines = text.split("\n")
    for line in lines:
        # 빈 줄 처리
        if not line.strip():
            markdown_lines.append("")
            in_list = False
            continue

        # 목록 처리
        if line.strip().startswith("•") or line.strip().startswith("-"):
            if not in_list:
                markdown_lines.append("")
            markdown_lines.append(line.replace("•", "-"))
            in_list = True
            continue

        # 일반 텍스트
        if in_list:
            markdown_lines.append("")
            in_list = False
        markdown_lines.append(line)

    return "\n".join(markdown_lines)


def _setup_output_path(pdf_path: str, output_path: str = None) -> str:
    """
    PDF 파일의 출력 경로를 설정합니다.
    
    Args:
        pdf_path (str): PDF 파일 경로
        output_path (str, optional): 지정된 출력 경로
        
    Returns:
        str: 최종 출력 경로
    """
    if output_path is None:
        # 상위 폴더명으로 된 폴더 생성
        parent_folder_name = os.path.basename(os.path.dirname(pdf_path))
        output_dir = os.path.join(os.path.dirname(pdf_path), parent_folder_name, "out")
        os.makedirs(output_dir, exist_ok=True)

        # 원본 파일명에서 .pdf 확장자를 제거하고 .md로 변경
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.md")
    
    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    return output_path


def convert_pdf_to_md(pdf_path: str, output_path: str = None) -> bool:
    """
    PDF 파일을 Markdown으로 변환합니다.

    Args:
        pdf_path (str): 변환할 PDF 파일 경로
        output_path (str, optional): 출력할 마크다운 파일 경로. 
            None인 경우 PDF 파일과 동일한 위치에 저장됩니다.

    Returns:
        bool: 변환 성공 여부
    """
    try:
        if not os.path.exists(pdf_path):
            logger.error(f"오류: PDF 파일을 찾을 수 없습니다: {pdf_path}")
            return False

        # 출력 경로 설정
        output_path = _setup_output_path(pdf_path, output_path)

        # PDF 파일 열기
        doc = fitz.open(pdf_path)
        markdown_text = ""

        # 페이지별 처리
        for page_num, page in enumerate(doc):
            # 텍스트 추출
            text = page.get_text()
            blocks = page.get_text("dict")["blocks"]
            
            # 마크다운으로 변환
            markdown_text += convert_text_to_markdown(text, blocks)
            markdown_text += "\n\n"  # 페이지 구분을 위한 빈 줄 추가

        # Markdown 파일로 저장
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_text.strip())

        logger.info(f"변환 완료: {output_path}")
        return True

    except Exception as e:
        logger.error(f"변환 중 오류 발생: {e}")
        return False


def find_pdf_files(directory: str, md_filename: str = None) -> list[str]:
    """
    지정된 디렉토리에서 PDF 파일을 찾습니다.
    절대 경로와 상대 경로를 모두 지원합니다.
    프로젝트 루트의 data 폴더도 검색합니다.

    Args:
        directory (str): 검색할 디렉토리 경로 (절대 경로 또는 상대 경로)
        md_filename (str, optional): 마크다운 파일명 (data 폴더 검색용)

    Returns:
        list[str]: 발견된 PDF 파일들의 절대 경로 리스트
    """
    pdf_files = []
    search_paths = []

    if md_filename:
        root_dir = Path.cwd()  # 현재 작업 디렉토리 (main.py가 있는 위치)
        data_dir = root_dir / "data"
        if md_filename.endswith('.md'):
            md_filename = md_filename[:-3]  # .md 확장자 제거
        pdf_dir = data_dir / md_filename
        if pdf_dir.exists():
            search_paths.append(str(pdf_dir))

    # 모든 경로에서 PDF 파일 검색
    for search_path in search_paths:
        for root, dirs, files in os.walk(search_path):
            for file in files:
                if file.lower().endswith(".pdf"):
                    pdf_files.append(os.path.abspath(os.path.join(root, file)))
    
    if not pdf_files:
        paths_str = "\n - ".join(search_paths)
        logger.warning(f"경고: 다음 경로에서 PDF 파일을 찾을 수 없습니다:\n - {paths_str}")

    return pdf_files


def convert_all_pdf_files(input_path: str, output_path: str) -> None:
    """
    디렉토리 내의 모든 PDF 파일을 Markdown으로 변환합니다.

    Args:
        input_path (str): PDF 파일이 있는 디렉토리 경로
        output_path (str): 변환된 Markdown 파일을 저장할 디렉토리 경로
    """
    # 입력 디렉토리 확인
    if not os.path.exists(input_path):
        logger.error(f"오류: {input_path} 디렉토리가 존재하지 않습니다.")
        return

    # PDF 파일 찾기
    pdf_files = find_pdf_files(input_path)
    if not pdf_files:
        logger.error(f"오류: {input_path} 디렉토리에 PDF 파일이 없습니다.")
        return

    # 각 PDF 파일 변환
    for pdf_file in pdf_files:
        # 상위 폴더명으로 된 폴더 생성
        parent_folder_name = os.path.basename(os.path.dirname(pdf_file))
        output_subdir = os.path.join(output_path, parent_folder_name, "out")
        os.makedirs(output_subdir, exist_ok=True)

        # 원본 파일명에서 .pdf 확장자를 제거하고 .md로 변경
        base_name = os.path.splitext(os.path.basename(pdf_file))[0]
        md_file = os.path.join(output_subdir, f"{base_name}.md")

        logger.info(f"변환 시작: {pdf_file} -> {md_file}")

        if convert_pdf_to_md(pdf_file, md_file):
            logger.info(f"변환 완료: {md_file}")
        else:
            logger.error(f"변환 실패: {pdf_file}") 