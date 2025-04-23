## 비동기(Asynchronous) 처리 방식 순서도

```mermaid
graph TD
    A[시작] --> B[마크다운 파일 목록 가져오기]
    B --> C[작업 큐 생성]
    C --> D[세마포어 설정<br/>max_workers]

    subgraph "비동기 작업 풀"
        D --> E1["파일 처리 #1<br/>async"]
        D --> E2["파일 처리 #2<br/>async"]
        D --> E3["파일 처리 #3<br/>async"]

        subgraph "각 파일 처리 태스크"
            E1 --> F1[마크다운 읽기<br/>async]
            F1 --> G1[전처리]
            G1 --> H1["LLM API 호출<br/>async"]
            H1 --> I1{필수 필드<br/>체크}
            I1 -->|누락| J1["PDF 처리<br/>async"]
            J1 --> K1["HWP 처리<br/>async"]
            K1 --> L1[데이터 병합]
            I1 -->|완료| L1
            L1 --> M1["JSON 저장<br/>async"]
            M1 --> N1["DB 저장<br/>async"]
        end
    end

    E1 & E2 & E3 --> O[모든 태스크 완료 대기<br/>gather]
    O --> P[결과 집계]
    P --> Q[종료]

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style Q fill:#f9f,stroke:#333,stroke-width:2px
    style I1 fill:#bbf,stroke:#333,stroke-width:2px
    style O fill:#bfb,stroke:#333,stroke-width:2px

    classDef async fill:#ffe,stroke:#333,stroke-width:2px
    class F1,H1,J1,K1,M1,N1 async
```

### 특징

1. 동시 실행: 여러 파일을 병렬로 처리
2. 논블로킹 I/O: I/O 작업 중 다른 작업 수행 가능
3. 세마포어로 동시 처리량 제어
4. 복잡한 에러 처리: 각 비동기 작업의 에러를 개별 처리
5. await 지점에서 작업 전환
6. 메모리 효율적: 스레드 대신 이벤트 루프 사용

### 주요 비동기 작업

- 파일 읽기/쓰기 (aiofiles)
- API 호출 (aiohttp)
- PDF/HWP 변환
- 데이터베이스 작업 (aiomysql/asyncpg)

### 성능 향상 포인트

1. I/O 작업의 대기 시간 활용
2. CPU 작업과 I/O 작업의 효율적 분배
3. 리소스 사용량 최적화
