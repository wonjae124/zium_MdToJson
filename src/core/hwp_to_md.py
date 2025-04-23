import os
import re
from pathlib import Path

from hwp5.hwp5txt import TextTransform
from hwp5.xmlmodel import Hwp5File


def convert_text_to_markdown(text: str) -> str:
    """
    추출된 텍스트를 Markdown 형식으로 변환합니다.

    Args:
        text (str): 변환할 텍스트
    Returns:
        str: Markdown 형식으로 변환된 텍스트
    """
    lines = text.split("\n")
    markdown_lines = []
    in_list = False

    for line in lines:
        # 빈 줄 처리
        if not line.strip():
            markdown_lines.append("")
            in_list = False
            continue

        # 제목 처리 (숫자로 시작하는 제목)
        if re.match(r"^\d+\.", line.strip()):
            markdown_lines.append(f"## {line}")
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


def _setup_output_path(hwp_path: str, output_path: str = None) -> str:
    """
    HWP 파일의 출력 경로를 설정합니다.
    Args:
        hwp_path (str): HWP 파일 경로
        output_path (str, optional): 지정된 출력 경로
    Returns:
        str: 최종 출력 경로
    """
    if output_path is None:
        # 상위 폴더명으로 된 폴더 생성
        parent_folder_name = os.path.basename(os.path.dirname(hwp_path))
        output_dir = os.path.join(os.path.dirname(hwp_path), parent_folder_name, "out")
        os.makedirs(output_dir, exist_ok=True)

        # 원본 파일명에서 .hwp 확장자를 제거하고 .md로 변경
        base_name = os.path.splitext(os.path.basename(hwp_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.md")

    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    return output_path


def _convert_hwp_to_text(hwp_path: str, temp_path: str) -> bool:
    """
    HWP 파일을 텍스트로 변환합니다.
    Args:
        hwp_path (str): HWP 파일 경로
        temp_path (str): 임시 파일 경로

    Returns:
        bool: 변환 성공 여부
    """
    try:
        transform = TextTransform()
        hwp5file = Hwp5File(hwp_path)
        with open(temp_path, "wb") as dest:
            transform.transform_hwp5_to_text(hwp5file, dest)
        return True
    except Exception as e:
        print(f"HWP -> 텍스트 변환 중 오류 발생: {e}")
        return False


def convert_hwp_to_md(hwp_path: str, output_path: str = None) -> bool:
    """
    HWP 파일을 Markdown으로 변환합니다.

    Args:
        hwp_path (str): 변환할 HWP 파일 경로
        output_path (str, optional): 출력할 마크다운 파일 경로.
            None인 경우 HWP 파일과 동일한 위치에 저장됩니다.

    Returns:
        bool: 변환 성공 여부
    """
    try:
        if not os.path.exists(hwp_path):
            print(f"오류: HWP 파일을 찾을 수 없습니다: {hwp_path}")
            return False

        # 출력 경로 설정
        output_path = _setup_output_path(hwp_path, output_path)

        # 임시 파일 경로 설정
        temp_txt_name = os.path.join(
            os.path.dirname(output_path),
            os.path.splitext(os.path.basename(hwp_path))[0] + "_temp.txt"
        )

        # HWP -> 텍스트 변환
        if not _convert_hwp_to_text(hwp_path, temp_txt_name):
            return False

        try:
            # 텍스트를 읽어서 Markdown으로 변환
            with open(temp_txt_name, "r", encoding="utf-8") as f:
                text = f.read()

            markdown_text = convert_text_to_markdown(text)

            # Markdown 파일로 저장
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_text)

            print(f"변환 완료: {output_path}")
            return True

        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_txt_name):
                os.remove(temp_txt_name)

    except Exception as e:
        print(f"변환 중 오류 발생: {e}")
        return False


def find_hwp_files(directory: str, md_filename: str = None) -> list[str]:
    """
    지정된 디렉토리에서 HWP 파일을 찾습니다.
    절대 경로와 상대 경로를 모두 지원합니다.
    프로젝트 루트의 data 폴더도 검색합니다.

    Args:
        directory (str): 검색할 디렉토리 경로 (절대 경로 또는 상대 경로)
        md_filename (str, optional): 마크다운 파일명 (data 폴더 검색용)

    Returns:
        list[str]: 발견된 HWP 파일들의 절대 경로 리스트
    """
    hwp_files = []
    search_paths = []

    if md_filename:
        root_dir = Path.cwd()  # 현재 작업 디렉토리 (main.py가 있는 위치)
        data_dir = root_dir / "data"
        if md_filename.endswith('.md'):
            md_filename = md_filename[:-3]  # .md 확장자 제거
        hwp_dir = data_dir / md_filename
        if hwp_dir.exists():
            search_paths.append(str(hwp_dir))

    # 모든 경로에서 HWP 파일 검색
    for search_path in search_paths:
        for root, dirs, files in os.walk(search_path):
            for file in files:
                if file.lower().endswith((".hwp", ".hwpx")):
                    hwp_files.append(os.path.abspath(os.path.join(root, file)))

    if not hwp_files:
        paths_str = "\n - ".join(search_paths)
        print(f"경고: 다음 경로에서 HWP 파일을 찾을 수 없습니다:\n - {paths_str}")

    return hwp_files


def convert_all_hwp_files(input_path: str, output_path: str) -> None:
    """
    디렉토리 내의 모든 HWP 파일을 Markdown으로 변환합니다.

    Args:
        input_path (str): HWP 파일이 있는 디렉토리 경로
        output_path (str): 변환된 Markdown 파일을 저장할 디렉토리 경로
    """
    # 입력 디렉토리 확인
    if not os.path.exists(input_path):
        print(f"오류: {input_path} 디렉토리가 존재하지 않습니다.")
        return

    # HWP 파일 찾기
    hwp_files = find_hwp_files(input_path)
    if not hwp_files:
        print(f"오류: {input_path} 디렉토리에 HWP 파일이 없습니다.")
        return

    # 각 HWP 파일 변환
    for hwp_file in hwp_files:
        # 상위 폴더명으로 된 폴더 생성
        parent_folder_name = os.path.basename(os.path.dirname(hwp_file))
        output_subdir = os.path.join(output_path, parent_folder_name, "out")
        os.makedirs(output_subdir, exist_ok=True)

        # 원본 파일명에서 .hwp 확장자를 제거하고 .md로 변경
        base_name = os.path.splitext(os.path.basename(hwp_file))[0]
        md_file = os.path.join(output_subdir, f"{base_name}.md")

        print(f"변환 시작: {hwp_file} -> {md_file}")

        if convert_hwp_to_md(hwp_file, md_file):
            print(f"변환 완료: {md_file}")
        else:
            print(f"변환 실패: {hwp_file}")
