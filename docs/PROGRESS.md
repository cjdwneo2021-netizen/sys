# StudyBot 진행 현황과 운영 안내

> 기록일: 2026-10-07, Asia/Seoul. 이 문서는 이번 연결 작업의 확인 기록입니다. API 한도와 서비스 정책은 이후 변경될 수 있습니다. 키 원문, 비밀번호, 액세스 토큰은 기록하지 않습니다.

## 1. 만드는 것과 현재 상태

Colab 노트북·강의 녹취 텍스트·필기를 Drive에 모으면 GitHub Actions가 읽고, Gemini가 한국어 공부 노트를 정리하는 봇입니다. 결과와 개념 기억은 Git 저장소에 보관합니다.

| 항목 | 확인한 상태 |
|---|---|
| 저장소 | `cjdwneo2021-netizen/sys`, 기본 브랜치 `main` |
| 공개 범위 | Public 유지에 사용자 동의. 필요할 때 비공개로 전환 |
| 기존 구현 | 로컬 확인 당시 `8520a9b`, 수집·정리·재개·출력 코드와 워크플로 존재 |
| Google 프로젝트 | `my-project-sys-1234`, 프로젝트 번호 `900393280126` |
| Drive | 전용 `StudyBotInbox` 폴더 생성, 봇 서비스 계정에 뷰어 공유 확인 |
| Google 인증 | WIF 풀·OIDC 제공업체 생성, 저장소에 한정한 서비스 계정 인증 권한 저장 |
| Gemini | AI Studio에서 해당 프로젝트의 무료 등급 확인 |
| API 키 | 사용자가 GitHub Actions Repository Secret `GEMINI_API_KEY`에 등록, 이름 존재 확인 |
| 모델 | GitHub Variable `MODEL_NAME=gemini-3.1-flash-lite` 등록 |
| 자동 실행 | `STUDYBOT_ENABLED=true` 저장 확인. `main` 첫 수동 실행 성공 |
| 학습 자료 | 연결 시점 전용 폴더는 비어 있음. 실제 공부 노트 생성은 아직 미검증 |

클라우드 Codex 대화의 공유 링크 두 개는 `Shared chat not found`로 열리지 않았습니다. 이후 로컬에 클론된 코드와 `README.md`, `docs/SETUP.md`, `docs/PLAN.md`를 읽어 작업 맥락을 이어받았습니다. 이전 대화 전체가 이 세션에 자동으로 가져와진 것은 아닙니다.

## 2. 어디서 무엇을 사용하는가

```text
Colab / 직접 작성한 노트북·텍스트
                ↓ Drive에 저장
StudyBotInbox/과목_주차/자료
                ↓ 읽기 전용 Drive API
GitHub Actions의 일시적인 Ubuntu 러너
                ↓ Python StudyBot → Gemini API
원본 스냅샷 + 공부 노트 + 개념 기억 + 질문 + ZIP
                ↓ 봇 커밋
GitHub 저장소 / README 목록
```

| 서비스·도구 | 역할 | 필요한 이유 |
|---|---|---|
| Colab | 강의 실습과 노트북 작성 | 학습 자료를 만드는 작업 공간. 설정용·강의용 템플릿 제공 |
| Google Drive | 입력 자료 보관 | Colab에서 저장한 자료와 녹취·필기를 모으는 곳 |
| Google Cloud 프로젝트 | API와 인증 리소스 관리 | 비공개 Drive에 봇이 접근하도록 API·서비스 계정·신뢰 설정을 관리 |
| 서비스 계정 | 봇의 Google 사용자 역할 | 개인 계정 전체 대신 공유한 학습 폴더를 읽는 별도 ID |
| WIF / OIDC | GitHub와 Google 사이의 인증 | 장기 서비스 계정 JSON 키 없이 단기 토큰으로 인증 |
| Google AI Studio | Gemini 키·티어·한도 관리 | API 키 생성 및 무료 등급과 모델별 할당량 확인 |
| Gemini API | 공부 노트·개념·질문 정리 | 텍스트를 모델에 보내 JSON 형태의 결과를 받음 |
| GitHub Actions | 예약 실행과 처리 | 개인 PC가 꺼져 있어도 러너가 코드 실행 |
| GitHub Git 저장소 | 코드·원본·결과·체크포인트 저장 | 변경 이력과 중간 결과를 유지해 다음 실행에서 재개 |
| 로컬 Codex | 코드 확인·문서 작성·설정 보조 | 현재 Windows 작업 공간에서 후속 개발과 운영 지원 |

Google Cloud에 이 봇용 VM이나 상시 서버는 만들지 않았습니다. 실행 장소는 GitHub Actions입니다. Drive 접근 인증과 Gemini 키는 별개입니다. Gemini 키만으로 비공개 Drive를 읽을 수 없습니다.

## 3. 실제 리소스와 인증 범위

### Google / Drive

| 설정 | 값 |
|---|---|
| 프로젝트 ID | `my-project-sys-1234` |
| 프로젝트 번호 | `900393280126` |
| 서비스 계정 | `studybot-drive@my-project-sys-1234.iam.gserviceaccount.com` |
| Workload Identity Pool | `studybot` |
| OIDC 제공업체 | `repo-1406542384` |
| 발급자 | `https://token.actions.githubusercontent.com` |
| 저장소 숫자 ID | `1406542384` |
| 소유자 숫자 ID | `326789085` |
| Drive 폴더 ID | `1CecUt48DH4jqMoKT38yiWGKSKI8WOxtj` |

[학습 자료 폴더 열기](https://drive.google.com/drive/folders/1CecUt48DH4jqMoKT38yiWGKSKI8WOxtj) · [Google 프로젝트](https://console.cloud.google.com/home/dashboard?project=my-project-sys-1234)

제공업체의 속성 매핑은 다음과 같습니다.

```text
google.subject                = assertion.sub
attribute.repository_id       = assertion.repository_id
attribute.repository_owner_id = assertion.repository_owner_id
attribute.ref                 = assertion.ref
```

인증 조건:

```text
assertion.repository_id == '1406542384' &&
assertion.repository_owner_id == '326789085' &&
assertion.ref == 'refs/heads/main'
```

풀 전체 대신 `attribute.repository_id/1406542384`에 해당하는 ID를 봇 서비스 계정에 연결했습니다. 구성 코드는 `roles/iam.workloadIdentityUser`를 사용하며, 콘솔에서 정책 업데이트 완료를 확인했습니다. 프로젝트 Owner·Editor 권한이나 서비스 계정 private key는 봇에 부여하지 않았습니다.

Drive 폴더 공유는 **뷰어**, 일반 액세스는 **제한됨**입니다. 봇은 `drive.readonly` 범위의 단기 토큰을 요청합니다. 워크플로의 토큰 유효기간 설정은 3,600초입니다. Drive API는 이번에 활성화했고, IAM Service Account Credentials API와 Security Token Service API는 사용 설정 상태를 확인했습니다.

저장소 이전·소유자 변경·기본 브랜치 변경 시 인증 조건과 숫자 ID를 다시 확인해야 합니다. IAM 정책 변경은 활성화까지 몇 분 걸릴 수 있습니다. [Google OIDC 연동 안내](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-google-cloud-platform)

### GitHub에 넣은 값

등록 위치: 저장소 **Settings → Secrets and variables → Actions**. Secrets와 Variables는 서로 다른 탭입니다.

| 이름 | 위치 | 값 / 상태 |
|---|---|---|
| `GEMINI_API_KEY` | Repository Secret | 등록 존재 확인. 키 원문은 문서·코드에 넣지 않음 |
| `DRIVE_FOLDER_ID` | Repository Variable | `1CecUt48DH4jqMoKT38yiWGKSKI8WOxtj` |
| `GCP_SERVICE_ACCOUNT` | Repository Variable | `studybot-drive@my-project-sys-1234.iam.gserviceaccount.com` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Repository Variable | `projects/900393280126/locations/global/workloadIdentityPools/studybot/providers/repo-1406542384` |
| `MODEL_PROVIDER` | Repository Variable | `gemini` |
| `MODEL_NAME` | Repository Variable | `gemini-3.1-flash-lite` |
| `STUDYBOT_ENABLED` | Repository Variable | `true` 저장 확인. 예약 수집 활성화 |
| `MAX_MODEL_CALLS` | 선택 Variable | 별도 등록하지 않음. 코드·워크플로 기본값 8 |
| `MAX_DAILY_MODEL_CALLS` | 선택 Variable | 별도 등록하지 않음. 기본값 32 |
| `MODEL_BASE_URL` / `MODEL_API_KEY` | Variable / Secret | 현재 Gemini 사용이므로 등록하지 않음 |
| `GITHUB_TOKEN` | Actions 자동 발급 | 사용자가 키를 만들거나 Colab에 입력할 필요 없음 |

[Secrets 관리](https://github.com/cjdwneo2021-netizen/sys/settings/secrets/actions) · [Variables 관리](https://github.com/cjdwneo2021-netizen/sys/settings/variables/actions)

워크플로에는 `${{ secrets.GEMINI_API_KEY }}`라는 참조만 있고, 실행 시 환경 변수로 전달됩니다. 키를 Python 코드·노트북·README·채팅에 붙여넣지 않습니다. [GitHub Secrets 동작](https://docs.github.com/en/actions/concepts/security/secrets)

## 4. 무료 사용과 호출 제한

AI Studio에서 `SYS Gemini API Key`가 `my-project-sys-1234`에 속하고 **무료 등급**으로 표시되는 것을 확인했습니다. GitHub에 등록한 Secret의 원문은 다시 읽을 수 없으므로, 그 키와 실제 일치하는지는 API 호출 성공으로 최종 검증해야 합니다.

2026-10-07 이 프로젝트의 AI Studio 한도 화면에 표시된 `Gemini 3.1 Flash Lite` 값:

| 항목 | 확인값 | 의미 |
|---|---|---|
| RPM | 15 | 분당 요청 한도 |
| TPM | 250,000 | 분당 입력 토큰 한도 |
| RPD | 500 | 하루 요청 한도 |
| 프로그램 실행당 제한 | 8회 | 외부 한도와 별개인 자체 호출 시도 제한 |
| 프로그램 하루 제한 | 32회 | UTC 날짜 기준, 체크포인트로 여러 실행 간 공유 |
| 모델 출력 설정 | 최대 4,096토큰 | 호출당 결과 길이 설정 |
| 모델 처리 시간 제한 | 기본 1,500초 | 한 실행에서 모델 처리에 사용하는 시간 제한 |

이 수치는 계정·프로젝트·모델별 확인값이며 영구 보장이나 모든 사용자 공통 한도가 아닙니다. 다른 앱이 같은 프로젝트를 쓰면 프로젝트 한도도 함께 소비할 수 있습니다. 한 강의를 여러 묶음으로 정리하므로 요청 1회가 강의 1개를 의미하지 않습니다.

무료 티어에서 무료 지원 모델을 사용하면 입력·출력 비용은 무료입니다. 결제를 연결하고 유료 티어로 전환하면 같은 키·모델의 호출도 과금될 수 있습니다. 자체 호출 횟수 제한은 무료 티어를 강제하는 기능이 아닙니다. 코드는 한도 오류(429)를 받으면 진행을 저장하고 이후 실행에서 재개하며, 더 비싼 모델로 자동 전환하지 않습니다. 무료 서비스의 입력·출력은 Google 제품 개선에 사용될 수 있으므로 개인·민감 자료를 넣기 전에 해당 약관을 확인하세요. [가격·무료 조건](https://ai.google.dev/gemini-api/docs/pricing) · [사용량 제한](https://ai.google.dev/gemini-api/docs/rate-limits) · [약관](https://ai.google.dev/gemini-api/terms)

키는 **[Google AI Studio API Keys](https://aistudio.google.com/api-keys)**에서 프로젝트를 선택해 생성하고 GitHub Secret에 등록하는 방식입니다. 이미 프로젝트가 있다면 AI Studio에서 가져오기를 사용할 수 있습니다. [공식 키 생성 안내](https://ai.google.dev/gemini-api/docs/api-key)

GitHub 실행 비용은 모델 API 비용과 별개입니다. 현재 공개 저장소의 표준 `ubuntu-latest` 러너는 무료입니다. 비공개로 바꾸면 계정 요금제의 무료 실행량·스토리지 범위와 초과 비용을 확인하세요. [GitHub Actions 비용](https://docs.github.com/en/billing/concepts/product-billing/github-actions)

## 5. 사용 방법과 실행 흐름

```text
StudyBotInbox/
  파이썬기초_3주차/
    실습.ipynb
    강의녹취.txt
    질문.md
  파이썬기초_4주차/
    실습.ipynb
```

폴더 바로 아래의 **하위 폴더 하나가 강의 하나**입니다. 그 안의 하위 폴더는 재귀적으로 읽습니다. 이번 예시 검증을 위해 루트 파일도 파일 하나를 강의 하나로 처리하도록 확장했습니다. 관련 자료 여러 개를 묶으려면 하위 폴더를 사용하세요.

1. Colab 노트북 자체를 강의 폴더에 저장합니다.
2. 생성한 텍스트·결과 파일도 Drive 강의 폴더에 저장합니다. Colab `/content`에만 있는 파일은 수집되지 않습니다.
3. 긴 편집 중에는 강의 폴더에 `.studybot-busy`를 두고, 종료 후 제거합니다.
4. Actions → StudyBot → Run workflow에서 `main`을 실행하거나 예약을 기다립니다.
5. 처음에는 지문을 관찰합니다. 두 번의 관찰과 수정 후 45분의 안정 기간을 통과해야 원본을 내려받습니다.
6. 원본 추출 → 묶음 정리 → 병합 → 공부 노트·기억·질문·ZIP·README 생성 → 커밋 순서로 처리합니다.

예약식은 `17 * * * *`(UTC)이며 매시간 실행을 요청합니다. 실행 시각은 GitHub 대기열에 따라 늦어질 수 있습니다. 작업 전체 제한은 45분, 수집 단계 제한은 15분입니다. `studybot-main` concurrency 그룹으로 자동화 실행을 직렬화합니다.

자료가 같으면 모델을 다시 호출하지 않고, 완료된 중간 결과도 재사용합니다. Drive 원본을 수정하거나 삭제하지 않으며, Drive에서 폴더를 지워도 Git 기록은 자동 삭제하지 않습니다.

## 6. 코드·출력·로컬 작업 공간

| 경로 | 내용 |
|---|---|
| `studybot/drive.py` | 폴더 조회, 안정성 관찰, 원본 수집 |
| `studybot/extract.py` | 노트북·텍스트 자료 추출 |
| `studybot/model.py` | Gemini / OpenAI 호환 API, 응답 검증, 호출 예산 |
| `studybot/pipeline.py` | 묶음 정리, 병합, 체크포인트와 기억 문맥 |
| `studybot/render.py` | README 목록, Markdown 및 ZIP 출력 |
| `studybot/storage.py` | 파일 저장·지문 등 공통 처리 |
| `studybot/config.py`, `cli.py` | 환경 설정과 CLI 명령 |
| `colab/` | 설정·강의 템플릿 노트북 |
| `setup_gcp.py` | 인증 리소스 설정 코드. 이번에는 브라우저 콘솔에서 설정 |
| `tests/` | 외부 API를 쓰지 않는 unittest 테스트 |
| `.github/workflows/check.yml` | 설치, 구문 검사, 단위 테스트 |
| `.github/workflows/studybot.yml` | 예약 수집·모델 호출·결과 저장 |
| `materials/` | 불변 원본 스냅샷과 manifest |
| `notes/`, `memory/` | 강의 노트, 개념 문서와 질문 기록 |
| `state/` | 관찰 상태, 부분 결과, 예산 등 재개 정보 |
| `downloads/` | 공부 노트와 출처 목록 ZIP |

Windows 작업 공간은 `C:\Y\study\coding\sys`, 실제 Git checkout은 그 안의 `sys\`입니다. 명령은 `C:\Y\study\coding\sys\sys`에서 실행합니다. 사용자 요청에 따라 작업 공간 루트에 만든 `AGENTS.md`는 Git checkout 밖에 있어 현재 저장소 커밋에 포함되지 않습니다.

```bash
python -m pip install .
python -m compileall -q studybot tests setup_gcp.py
python -m unittest discover -s tests -v
studybot sync
studybot build
studybot render
studybot models
```

Python 3.11 이상이 필요하고 CI는 3.12를 사용합니다. `sync`는 Drive 인증, `build`는 자료와 모델 설정, `models`는 Gemini 키가 필요합니다. `render`는 기존 결과를 다시 출력합니다. 로컬에서 Secrets가 자동으로 내려오지는 않습니다.

## 7. MCP와 이번 작업에 사용한 도구

**StudyBot 실행 자체에는 MCP 서버를 연결하지 않았습니다.** Python이 Drive·Gemini API를 직접 호출합니다. MCP·브라우저 도구는 이번 설정을 진행한 Codex 세션의 작업 도구이며 GitHub Actions의 실행 의존성이 아닙니다.

| 이번 세션의 도구 | 사용 목적 | 범위 |
|---|---|---|
| `mcp__cua_repl` / `cua` | 브라우저 연결 목록, 화면 읽기, 입력·클릭 | 로그인된 Chrome에서 GitHub·Google Cloud·Drive·AI Studio 설정 |
| `functions.exec` / `exec_command` | 로컬 PowerShell 명령 | 저장소·Git 이력·코드 읽기, 테스트 실행 |
| `apply_patch` | 파일 편집 | contributor guide와 이번 운영 문서 작성 |
| `web.run` | 공식 문서 확인 | API 키, 무료 티어, 한도, GitHub 비용·Secrets 안내 |

처음에는 다른 Chrome 프로필에 연결돼 GitHub가 로그아웃으로 보였습니다. 사용자가 원하는 계정 창에도 ChatGPT 브라우저 확장 프로그램을 연결한 뒤, 해당 프로필의 GitHub·Google 로그인 세션을 통해 설정했습니다. 확장 프로그램 연결은 프로필별이며 다른 창이 자동으로 보이는 것은 아닙니다. 브라우저의 로그인 권한은 API 키·GitHub Actions의 OIDC 권한과도 별개입니다.

이 세션에서는 GitHub·Google Drive 전용 MCP 커넥터로 설정한 것이 아닙니다. 로컬 `gh`, `gcloud` CLI가 검색되지 않아 브라우저 UI를 사용했습니다. 다른 세션에서 MCP나 확장이 연결되지 않아도 배포된 Actions 봇은 등록된 Secrets·Variables와 OIDC로 동작합니다.

## 8. 검증 기록과 아직 확인하지 않은 것

### 확인 완료

- 저장소 구현·설정 문서·워크플로 및 기본값 확인.
- Google 프로젝트·서비스 계정·WIF 제공업체 생성 상태 확인.
- 인증 조건을 저장소 숫자 ID·소유자 ID·`main`으로 제한.
- 서비스 계정 인증 정책 업데이트 완료 메시지 확인.
- Drive 공유 목록에서 봇의 뷰어 권한과 일반 액세스 제한 확인.
- Drive API 활성화, IAM Credentials·STS API 사용 설정 확인.
- GitHub Secret 이름과 Variables 값 확인.
- AI Studio의 프로젝트 무료 티어 및 모델별 할당량 확인.
- 공개 저장소 유지 및 자료 공개에 사용자 동의.
- `STUDYBOT_ENABLED=true` 저장 및 첫 실제 Actions job 성공 확인.

### 첫 실행 기록

[첫 수동 실행 결과](https://github.com/cjdwneo2021-netizen/sys/actions/runs/37627535829) · [단계별 로그](https://github.com/cjdwneo2021-netizen/sys/actions/runs/37627535829/job/112813094833)

2026-10-07 22:19 KST, `main`의 `8520a9b`를 대상으로 실행했고 워크플로 전체 28초, `organize` job 20초로 **성공**했습니다.

| 실행 단계 | 확인 결과 |
|---|---|
| 패키지 설치 | 성공 |
| Authenticate read-only Drive access | 성공. GitHub OIDC → Google 단기 인증 실제 통과 |
| Import stable lecture snapshots | 성공. 로그 `Imported 0 lecture(s)` |
| Build notes and memory | 성공. 로그 `Generated 0 note(s)` |
| Save results and resumable checkpoints | 성공. 봇 커밋 `b7fc1a6`, 제목 `studybot: update lecture notes and checkpoints` |

Drive 폴더가 비어 있어 강의와 공부 노트는 0건이었습니다. 첫 실행에서는 Gemini API 호출을 수행하지 않았습니다. 이 성공을 Gemini 키·응답 품질까지 검증한 것으로 해석하지 않습니다.

이번 빈 폴더 실행으로 검증된 것은 OIDC·Drive 조회·기본 빌드·결과 저장 경로입니다. 실제 Gemini 키의 유효성, 모델 응답 형식과 정리 품질은 강의 자료를 넣고 모델 호출이 수행돼야 검증됩니다. 원격에는 위 봇 커밋이 추가됐으며 로컬 checkout은 별도로 갱신해야 합니다.

### 로컬 테스트 기록

초기 16개 unittest는 Windows 임시 폴더 권한 때문에 대부분 완료하지 못했습니다. 이후 승인된 실행 환경에서 Excel·루트 파일 회귀 테스트를 포함해 재검증하여 **19개 전체 통과**했습니다. 한국어 README를 읽는 기존 테스트의 기본 cp949 인코딩 오류는 명시적인 UTF-8 읽기로 수정했습니다. 구문 검사도 통과했습니다.

## 9. 운영하면서 고려할 점

- **공개 범위:** 원본·노트·개념 기억·체크포인트 일부가 Git에 남습니다. 나중에 비공개로 바꿔도 이미 내려받은 복사본까지 회수되지는 않습니다. 현재는 공개 유지에 동의한 상태입니다.
- **모델 전송:** 정리 대상 원문과 일부 기존 개념 기억은 Gemini로 전송됩니다. Drive 뷰어 공유와 모델 제공업체로의 자료 전송은 서로 다른 과정입니다.
- **지원 형식:** 노트북, 텍스트, Markdown, Python, Google Docs 텍스트와 Excel `.xlsx`를 읽습니다. Excel 수식은 실행하지 않고 저장된 결과를 구분해 표시합니다. 표·셀 텍스트를 추출하며 차트·이미지는 분석하지 않습니다. PDF·이미지·음성 본문 추출, OCR, 음성 전사는 현재 구현되지 않았습니다. 녹취는 텍스트로 준비합니다.
- **수집 크기:** 파일당 10 MiB, 강의당 30 MiB. 큰 파일은 링크로 남습니다. 강의가 크면 폴더를 나눕니다.
- **정확성:** 모델 보충 설명을 정답으로 확정하지 말고 원본 출처와 비교합니다. 기억 연결은 개념명·단어 기반이며 고급 의미 검색이나 자동 동의어 통합은 아닙니다.
- **코드 실행:** 입력 노트북의 코드를 실행하지 않습니다. 실습 실행·검증은 Colab에서 별도로 합니다.
- **재개 상태:** `state/`를 임의로 지우면 관찰·호출 예산·완료된 중간 결과를 잃고 재처리될 수 있습니다. 원본과 체크포인트의 장기 보존 정책은 아직 없습니다.
- **키 관리:** 무료 티어와 결제 상태를 주기적으로 확인합니다. 노출된 키는 새 키를 등록·검증한 뒤 기존 키를 폐기합니다. API 키를 Git에 커밋하지 않습니다.
- **브랜치 규칙:** Actions는 결과를 기본 브랜치에 직접 push합니다. 보호 규칙이나 다른 커밋 때문에 실패할 수 있고 강제 push하지 않습니다. 비공개 전환 후에는 Actions 비용·권한도 재확인합니다.
- **중지 방법:** `STUDYBOT_ENABLED=false`로 바꾸면 이후 job을 건너뜁니다. 이미 실행 중인 작업은 Actions에서 별도로 취소합니다. 파일·기록이 자동 삭제되는 설정은 아닙니다.

## 10. 다음 실제 사용 단계

1. 첫 Actions 실행의 인증·Drive 조회는 성공했습니다. 이후 예약 실행도 Actions에서 관찰합니다.
2. `StudyBotInbox/테스트강의/`에 공개 가능한 짧은 `.txt` 또는 `.ipynb` 자료를 넣습니다.
3. 첫 관찰 후 안정 기간과 두 번째 관찰을 거쳐 정리를 실행합니다.
4. Gemini 호출 성공, JSON·출처 검증, `notes/`·`memory/`·ZIP·README 생성과 봇 커밋을 확인합니다.
5. 실제 강의 자료를 넣고 정리 품질과 하루 호출량을 관찰합니다.

상세 초기 설정은 [SETUP.md](SETUP.md), 구현 설계는 [PLAN.md](PLAN.md)를 참고하세요. 이 문서의 확인 시점 이후 설정을 바꾸면 상태표·한도·검증 기록도 갱신합니다.
