# sys · StudyBot

Colab 노트북·강의 녹취·필기를 모아 한국어 공부 노트와 개념 기억을 만드는 GitHub Actions 봇입니다.

[연결 설정](docs/SETUP.md) · [구현 계획](docs/PLAN.md) · [공식 근거](docs/RESEARCH.md) · [테스트](https://github.com/cjdwneo2021-netizen/sys/actions/workflows/check.yml)

## 현재 연결 상태와 운영 기록

**2026-10-07 기준:** Google Cloud·Drive 인증, GitHub Actions 활성화, Gemini API 키 등록을 완료했고 [첫 수동 실행](https://github.com/cjdwneo2021-netizen/sys/actions/runs/37627535829)이 성공했습니다. 모델은 `gemini-3.1-flash-lite`이며 AI Studio에서 해당 프로젝트의 무료 등급을 확인했습니다. 빈 폴더로 실행해 수집 0건·노트 0건이었으며 실제 모델 호출은 아직 미검증입니다. 저장소는 사용자 선택에 따라 공개로 유지합니다.

서비스별 역할, 실제 등록한 설정값, 무료 호출 한도, MCP·브라우저 도구 사용 내역, 검증 결과와 남은 작업은 **[진행 현황과 운영 안내](docs/PROGRESS.md)**에 정리했습니다. 설정값이 바뀌면 이 문서도 함께 갱신하세요.

[Colab에서 연결 설정 열기](https://colab.research.google.com/github/cjdwneo2021-netizen/sys/blob/main/colab/setup.ipynb) · [강의 저장 템플릿 열기](https://colab.research.google.com/github/cjdwneo2021-netizen/sys/blob/main/colab/lecture-template.ipynb)

## 사용 방법

1. 연결 설정 노트북에서 Google Cloud 프로젝트 ID를 입력하고 인증 리소스를 구성합니다.
2. Drive의 `StudyBotInbox` 폴더를 봇 서비스 계정에 뷰어로 공유합니다.
3. `StudyBotInbox/과목_주차/`에 노트북·녹취·필기를 저장합니다.
4. GitHub에 설정값과 모델 키를 등록한 뒤 `STUDYBOT_ENABLED=true`로 활성화합니다.

약 1시간마다 확인하며, 두 번의 관찰과 45분의 안정 기간을 거친 자료를 정리합니다.
예약 실행 지연이나 모델 한도에 따라 완료까지 더 오래 걸릴 수 있습니다.

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
