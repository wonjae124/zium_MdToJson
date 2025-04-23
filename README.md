# Markdown to JSON 변환기

이 프로젝트는 마크다운 파일을 JSON 형식으로 변환하는 도구입니다. LLM(Large Language Model)을 활용하여 마크다운 문서의 구조화된 데이터를 추출하고 JSON 형식으로 변환합니다.

## 시스템 요구사항

- Python 3.12 이상
- Docker (선택사항)
- uv (Python 패키지 매니저)
- PostgreSQL (Docker 미사용 시)

## 환경 설정

### 0. Linux 시스템 준비

```bash
# 필수 패키지 설치
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3-pip postgresql postgresql-contrib

# PostgreSQL 서비스 시작 (Docker 미사용 시)
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 1. Windows 시스템 준비

```cmd
# 1. Python 3.12 설치
# https://www.python.org/downloads/ 에서 Python 3.12 설치
# 설치 시 "Add Python to PATH" 옵션 체크

# 2. PostgreSQL 설치 (Docker 미사용 시)
# https://www.postgresql.org/download/windows/ 에서 다운로드
# 설치 중 지정한 비밀번호를 기억해두세요

# 3. Visual C++ 재배포 패키지 설치 (PDF/HWP 변환 기능 사용 시)
# https://aka.ms/vs/17/release/vc_redist.x64.exe 다운로드 후 실행

# PowerShell 관리자 권한으로 실행 후:

# PostgreSQL 서비스 시작 확인
net start postgresql-x64-15

# 환경 변수 설정 (PowerShell)
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\PostgreSQL\15\bin", [System.EnvironmentVariableTarget]::Machine)

# uv 파이썬 패키지 설치
pip install uv
```

### 2. Python 환경 설정

```bash
# Python 3.12 설치 확인
python3 --version

# uv 설치
pip3 install uv

# 가상환경 생성 및 활성화
uv venv
source .venv/bin/activate  # Linux/Mac
.venv/Scripts/activate  # Windows

# 의존성 설치
uv pip install -r requirements.txt
```

### 3. Docker 환경 설정 (선택사항)

```bash
# Docker 및 Docker Compose 설치 (Ubuntu/Debian)
sudo apt-get install -y docker.io docker-compose

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 현재 사용자를 docker 그룹에 추가 (선택사항)
sudo usermod -aG docker $USER

# Docker 이미지 빌드 및 실행
docker-compose up -d
```

## 프로젝트 구조

```
mdToJson/
├── src/                          # 소스 코드 디렉토리
│   ├── config/                   # 설정 관련 코드
│   │   ├── config_manager.py     # 설정 관리 클래스
│   │   ├── constants.py         # 상수 정의
│   │   └── logging_config.py    # 로깅 설정
│   ├── core/                     # 핵심 기능 코드
│   │   ├── file_handler.py      # 파일 처리 클래스
│   │   ├── markdown_preprocessor.py  # 마크다운 전처리 클래스
│   │   ├── llm_parser.py        # LLM 파싱 클래스
│   │   ├── json_generator.py    # JSON 생성 클래스
│   │   ├── process_manager.py   # 전체 프로세스 관리 클래스
│   │   ├── pdf_to_md.py        # PDF to 마크다운 변환
│   │   └── hwp_to_md.py        # HWP to 마크다운 변환
│   └── models/                   # 데이터 모델
│       ├── database.py          # 데이터베이스 설정
│       └── schemas.py           # 데이터 스키마 정의
├── data/                         # 입력 데이터 디렉토리
├── output/                       # 출력 데이터 디렉토리
├── logs/                        # 로그 파일 디렉토리
├── docs/                        # 문서 디렉토리
├── main.py                      # 메인 실행 파일
├── config.ini                   # 설정 파일
├── pyproject.toml              # 프로젝트 설정 및 의존성
├── uv.lock                     # 의존성 잠금 파일
└── docker-compose.yml          # Docker 구성 파일
```

## 실행 방법

1. 설정 파일 준비

   - `config.ini` 파일에서 필요한 설정을 구성합니다.
   - API 키, 입/출력 디렉토리 등을 설정합니다.

2. 프로그램 실행

   ```bash
   # 기본 실행
   python3 main.py  # Linux
   python main.py   # Windows

   # 특정 설정 파일로 실행
   python3 main.py --config custom_config.ini  # Linux
   python main.py --config custom_config.ini   # Windows
   ```

3. 권한 설정 (Linux 전용)

   ```bash
   # 실행 권한 부여
   chmod +x main.py

   # 로그 디렉토리 권한 설정
   sudo chown -R $USER:$USER logs/
   chmod 755 logs/
   ```

## 프로세스 흐름도

1. 초기화 단계

   - 설정 파일 로드
   - 환경 검증
   - 디렉토리 구조 확인

2. 데이터 처리 단계

   - 마크다운 파일 읽기
   - 전처리 작업 수행
     - 헤더 정리
     - 불필요한 공백 제거
     - 특수 문자 처리

3. LLM 처리 단계

   - 컨텍스트 설정
   - 내용 분석
   - 구조화된 데이터 추출

4. 출력 생성 단계
   - JSON 형식 변환
   - 데이터 검증
   - 파일 저장

## 주의사항

- API 키는 반드시 환경 변수나 설정 파일을 통해 안전하게 관리해야 합니다.
- 대용량 파일 처리 시 메모리 사용량에 주의하세요.
- 처리된 파일은 자동으로 백업됩니다.

## 로그 확인

- 로그 파일은 `logs` 디렉토리에 저장됩니다.
- 에러 발생 시 `logs/error.log` 파일을 확인하세요.

## 문제 해결

일반적인 문제 해결 방법:

1. 환경 변수 확인
2. 로그 파일 검토
3. 설정 파일 재확인
4. 가상환경 재활성화

[파싱 순서도]
컨피그 설정
마크다운 파일 읽기
마크다운 전처리
LLM 내용 파싱
데이터 검증 및 정규화(필수 데이터 확인)
json파일 생성

## Linux 특정 주의사항

1. 파일 시스템 권한

   - 입력/출력 디렉토리에 대한 적절한 읽기/쓰기 권한이 필요합니다.
   - 로그 디렉토리에 대한 쓰기 권한이 필요합니다.

2. 데이터베이스 접근

   - PostgreSQL을 직접 설치한 경우, 데이터베이스 사용자 설정이 필요합니다:
     ```bash
     sudo -u postgres createuser -s $USER
     sudo -u postgres createdb bizup_db
     ```

### 2. Docker Desktop 설치 (선택사항)

```cmd
# 1. Docker Desktop 설치
# https://www.docker.com/products/docker-desktop/ 에서 다운로드

# 2. WSL2 설치 (PowerShell 관리자 권한)
wsl --install

# 3. Docker Desktop 실행 후 설정
# - WSL2 기반 엔진 사용 설정
# - 리소스 할당 (메모리 4GB 이상 권장)
```
