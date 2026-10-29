# sys · StudyBot

Colab 노트북·강의 녹취·필기를 모아 한국어 공부 노트와 개념 기억을 만드는 GitHub Actions 봇입니다.

[연결 설정](docs/SETUP.md) · [구현 계획](docs/PLAN.md) · [공식 근거](docs/RESEARCH.md) · [테스트](https://github.com/cjdwneo2021-netizen/sys/actions/workflows/check.yml)

## 현재 연결 상태와 운영 기록

**2026-10-12 확인:** Google Cloud·Drive 인증과 GitHub Actions를 연결했고, 실제 Excel 자료에서 공부 노트 1건·개념 기억 4개·질문·ZIP이 생성된 것을 확인했습니다. 모델 설정은 `gemini-3.1-flash-lite`입니다. 첫 노트는 원본과 대조해 전처리 예시·DTM 빈도·미작성 셀 설명을 보완했습니다. 저장소는 사용자 선택에 따라 공개로 유지합니다.

서비스별 역할, 실제 등록한 설정값, 무료 호출 한도, MCP·브라우저 도구 사용 내역, 검증 결과와 남은 작업은 **[진행 현황과 운영 안내](docs/PROGRESS.md)**에 정리했습니다. 설정값이 바뀌면 이 문서도 함께 갱신하세요.

[Colab에서 연결 설정 열기](https://colab.research.google.com/github/cjdwneo2021-netizen/sys/blob/main/colab/setup.ipynb) · [강의 저장 템플릿 열기](https://colab.research.google.com/github/cjdwneo2021-netizen/sys/blob/main/colab/lecture-template.ipynb)

## 사용 방법

1. 연결 설정 노트북에서 Google Cloud 프로젝트 ID를 입력하고 인증 리소스를 구성합니다.
2. Drive의 `StudyBotInbox` 폴더를 봇 서비스 계정에 뷰어로 공유합니다.
3. `StudyBotInbox/과목_주차/`에 노트북·녹취·필기를 저장합니다.
4. GitHub에 설정값과 모델 키를 등록한 뒤 `STUDYBOT_ENABLED=true`로 활성화합니다.

약 1시간마다 확인하며, 두 번의 관찰과 45분의 안정 기간을 거친 자료를 정리합니다.
예약 실행 지연이나 모델 한도에 따라 완료까지 더 오래 걸릴 수 있습니다.

<!-- studybot:status:start -->

## 운영 현황

저장된 실행 시점의 스냅샷입니다. 현재 시각의 실시간 사용량은 아닙니다.

| 확인 항목 | 기록 |
|---|---|
| 기준 시각 (UTC) | 2026-10-29T21:47:46+00:00 |
| 설정 출처 | 최근 실행에서 저장한 설정 |
| 모델 | gemini / gemini-3.1-flash-lite |
| 기준일 호출 시도 (2026-10-29 UTC) | 0 / 32회 |
| 기준일 남은 자체 일일 예산 | 32회 |
| 실행당 자체 호출 한도 | 8회 |
| 마지막 build 호출 | 시도 0 · 응답 검증 완료 0 · 오류 0 · 캐시 재사용 0회 |
| 마지막 자료 수집 | 완료 · 0건 · 2026-10-29T21:47:46+00:00 · [실행 로그](https://github.com/cjdwneo2021-netizen/sys/actions/runs/40960713845) |
| 마지막 노트 생성 | 완료 · 0건 · 2026-10-29T21:47:46+00:00 · [실행 로그](https://github.com/cjdwneo2021-netizen/sys/actions/runs/40960713845) |
| 마지막 build 재개 대기 사유 | 해당 없음 |
| 자료 처리 | 수집된 자료 1건 · 생성/갱신 대기 0건 · 안정성 관찰 대기 0건 |
| 생성 결과 | 노트 1건 · 개념 4개 · ZIP 1개 |
| 안정 대기 / 모델 처리 시간 한도 | 2700초 / 1500초 |
| 토큰·실제 요금·제공업체 잔여 한도 | 미수집 · [AI Studio](https://aistudio.google.com/usage)에서 확인 |

### 최근 호출 기록 (UTC, 최대 7일)

| 날짜 | 시도 | 응답 검증 완료 | 오류 | 결과 미확인 |
|---|---:|---:|---:|---:|
| 2026-10-13 | 6 | 6 | 0 | 0 |
| 2026-10-12 | 1 | 0 | 1 | 0 |
| 2026-10-07 | 8 | 0 | 0 | 8 |

호출 시도에는 한도 오류와 응답 검증 실패도 포함하며 캐시 재사용은 제외합니다. 이전 기록은 시도 횟수만 복원하므로 결과 미확인으로 표시합니다. 새 기록은 호출 전후에 저장하며, 호출 도중 중단되면 결과 미확인으로 남습니다. 다른 앱의 호출은 포함하지 않습니다. 자체 예산은 제공업체 할당량과 별개이며 UTC 날짜가 바뀌면 초기화됩니다.

[호출 기록](state/usage.json) · [실행 상태](state/operations.json) · [처리 체크포인트](state/)

<!-- studybot:status:end -->

## 공부 노트

<!-- studybot:start -->

| 강의 | 공부 노트 | 원본 | 다운로드 |
|---|---|---|---|
| NLP_전처리단계설계_및_DTM직접구성_윤태은_2021011984.xlsx의 사본 | [보기](notes/1Emvy2lGi1XM5prSCO5pNGk8UM-rMfht8.md) | [원본 목록](materials/1Emvy2lGi1XM5prSCO5pNGk8UM-rMfht8/manifest.json) | [ZIP](downloads/1Emvy2lGi1XM5prSCO5pNGk8UM-rMfht8.zip?raw=true) |

[개념 기억](memory/index.md) · [질문 기록](memory/questions.md)

<!-- studybot:end -->

## 동작

- Drive → GitHub 단방향 수집. 노트북 코드는 실행하지 않습니다.
- 노트북, 텍스트, Markdown, Python 파일 및 Google Docs 텍스트를 읽습니다.
- Excel `.xlsx`의 시트·셀·수식·저장된 계산 결과도 읽습니다. 수식은 재계산하지 않습니다.
- Inbox 바로 아래의 파일은 파일 하나를 강의 하나로 처리하고, 하위 폴더는 기존처럼 폴더별로 처리합니다.
- 원본 스냅샷·개념 Markdown·강의 간 연결·질문 기록을 저장합니다.
- README 목록은 코드로 생성하며 ZIP에는 공부 노트와 출처 목록을 담습니다.
- 자료가 같으면 AI를 호출하지 않고, 호출 한도에 걸리면 다음 실행에서 재개합니다.
- Gemini 또는 OpenAI 호환 모델 서버를 선택할 수 있습니다.

파일당 10 MiB, 강의당 30 MiB 수집 한도가 있습니다. 큰 파일은 Drive 링크로 남기며, PDF·이미지·음성은 현재 본문을 추출하지 않습니다.
기억 연결은 개념명과 단어 기반 검색을 사용합니다. 동의어 통합과 고급 의미 검색은 추후 확장할 수 있습니다.

## 개발

```bash
python -m pip install .
python -m unittest discover -s tests -v
studybot sync
studybot build
```

테스트에는 실제 Google 계정이나 모델 키가 필요하지 않습니다.
계정 연결 후 OIDC·Drive 공유·모델 응답 품질은 별도로 확인해야 합니다.
