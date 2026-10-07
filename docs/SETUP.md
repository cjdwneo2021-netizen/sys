# 계정 연결과 실행

## 등록할 값

[Variables](https://github.com/cjdwneo2021-netizen/sys/settings/variables/actions)와 [Secrets](https://github.com/cjdwneo2021-netizen/sys/settings/secrets/actions)는 다릅니다.

| 이름 | 위치 | 내용 |
|---|---|---|
| DRIVE_FOLDER_ID | Variable | 학습 자료 전용 Drive 폴더 ID |
| GCP_WORKLOAD_IDENTITY_PROVIDER | Variable | 설정 노트북이 출력하는 전체 Provider 경로 |
| GCP_SERVICE_ACCOUNT | Variable | 설정 노트북이 출력하는 서비스 계정 이메일 |
| MODEL_PROVIDER | Variable | gemini 또는 openai-compatible |
| MODEL_NAME | Variable | 실제 계정에서 사용 가능한 명시적 모델 ID |
| GEMINI_API_KEY | Secret | Gemini 선택 시 API 키 |
| MODEL_BASE_URL | Variable | 다른 모델 서버를 선택할 때 /v1까지 포함한 주소 |
| MODEL_API_KEY | Secret | 다른 모델 서버가 요구할 때 |
| STUDYBOT_ENABLED | Variable | 연결 완료 후 true |
| MAX_MODEL_CALLS | Variable, 선택 | 실행당 호출 시도, 기본 8 |
| MAX_DAILY_MODEL_CALLS | Variable, 선택 | UTC 하루 호출 시도, 기본 32 |

GITHUB_TOKEN은 Actions가 자동 발급합니다. 직접 생성하거나 Colab에 넣지 않습니다.
Google API key만으로 비공개 Drive 파일에 접근할 수는 없습니다.
본 구성에는 서비스 계정 JSON private key나 사용자 refresh token이 필요하지 않습니다.

## 1. Google Cloud 설정

Google Cloud Console에서 프로젝트를 만들거나 기존 프로젝트를 선택합니다.
[Colab 설정 노트북](https://colab.research.google.com/github/cjdwneo2021-netizen/sys/blob/main/colab/setup.ipynb)을 열어 PROJECT_ID를 입력합니다.
저장소 ID 1406542384와 소유자 ID 326789085는 이미 입력돼 있습니다.

Google 사용자 로그인 후 설정 셀을 실행합니다.
설정에는 API 활성화, 서비스 계정 생성·정책 변경, Workload Identity Pool 관리 권한이 필요합니다.

설정 코드는 다음을 구성합니다.

1. Drive API, IAM API, IAM Service Account Credentials API, Security Token Service API 활성화.
2. studybot-drive 서비스 계정 생성. 프로젝트 Editor·Owner 역할은 부여하지 않음.
3. studybot Workload Identity Pool과 GitHub OIDC Provider 생성.
4. 저장소 숫자 ID·소유자 숫자 ID·기본 브랜치 조건으로 인증 제한.
5. 해당 GitHub identity에 서비스 계정의 roles/iam.workloadIdentityUser 부여.

기본 브랜치를 바꾸거나 저장소를 이전하면 WIF 조건도 갱신해야 합니다.
IAM 설정 전파에는 약 5분이 걸릴 수 있습니다.
Colab에 gcloud가 없거나 조직 정책으로 제한되면 같은 설정을 Cloud Console에서 구성합니다.

Google Cloud 프로젝트의 IAM은 Drive 폴더 접근 권한을 부여하지 않습니다.
다음 단계의 폴더 공유가 별도로 필요합니다.
이 과정에서 VM이나 상시 서버를 생성하지 않습니다.

## 2. Drive 공유

My Drive에 StudyBotInbox 폴더를 만듭니다.
폴더를 GCP_SERVICE_ACCOUNT 이메일 주소에 **뷰어**로 공유합니다.
URL의 /folders/ 뒤 ID를 DRIVE_FOLDER_ID로 등록합니다.

    StudyBotInbox/
      파이썬기초_3주차/
        실습.ipynb
        강의녹취.txt
        질문.md
      파이썬기초_4주차/
        실습.ipynb

바로 아래의 폴더 하나가 강의 하나이며, 그 안의 하위 폴더는 재귀적으로 읽습니다.
StudyBotInbox 바로 아래의 파일은 파일 하나를 강의 하나로 처리합니다.
여러 자료를 하나의 강의로 묶으려면 하위 폴더에 함께 저장하세요.
Excel `.xlsx`는 시트별 행과 셀 좌표, 수식 및 저장된 계산 결과를 추출합니다.
수식·외부 링크를 실행하거나 재계산하지 않으며, 저장된 결과가 없는 수식은 그렇게 표시합니다.
서비스 계정은 뷰어 권한과 drive.readonly 범위만 사용합니다.
개인 My Drive에서 이 구조를 쓰는 데 Domain-Wide Delegation은 필요하지 않습니다.

## 3. Colab 저장

노트북 자체를 Drive 강의 폴더에 저장합니다.
파일에서 생성한 결과도 /content/drive/MyDrive/StudyBotInbox/강의폴더/ 경로로 저장합니다.
/content의 파일은 자동 수집되지 않습니다.

[강의 템플릿](https://colab.research.google.com/github/cjdwneo2021-netizen/sys/blob/main/colab/lecture-template.ipynb)에 마운트·저장 예시가 있습니다.
노트북 저장과 마운트 파일 쓰기는 다른 경로입니다.
작업 종료 전 노트북 저장을 확인하고, 필요하면 drive.flush_and_unmount()로 마운트 쓰기를 마칩니다.

긴 작업 도중 수집을 미루려면 강의 폴더에 .studybot-busy를 만들고 종료 시 삭제합니다.
표시 파일이 남아 있으면 수집을 계속 미룹니다.
표시를 사용하지 않으면 긴 작업 중 중간 자료가 정리될 수 있으며 나중에 변경된 자료로 다시 정리됩니다.

## 4. 모델

Google AI Studio에서 현재 제공되는 모델과 무료 이용 조건을 확인합니다.
키를 GEMINI_API_KEY Secret으로 등록하고 MODEL_NAME을 명시합니다.
명령 studybot models로 접근 가능한 모델 이름을 조회할 수 있지만, 모델 목록은 무료 사용 보장이 아닙니다.

프로그램은 유료 모델로 자동 전환하지 않습니다.
유료 프로젝트의 키를 사용하면 설정한 호출 수 안에서도 과금될 수 있습니다.
429 응답이면 러너를 오래 대기시키지 않고 중간 결과를 저장해 다음 실행으로 넘깁니다.
무료 이용 한도와 자료 이용 조건은 AI Studio 및 현재 약관에서 확인합니다.

OpenAI 호환 모델 서버로 옮길 때는 MODEL_PROVIDER=openai-compatible과 MODEL_BASE_URL을 설정합니다.
서버가 chat/completions와 JSON 응답 형식을 지원해야 합니다.
Actions에서 localhost는 Actions 러너를 가리키며 개인 PC를 가리키지 않습니다.
작은 CPU 모델의 다운로드·서버 실행은 선택할 모델과 러너를 정한 뒤 추가할 수 있습니다.

## 5. 첫 실행

이 저장소가 Public이면 가져오는 원본·기억·공부 노트도 공개됩니다.
비공개 학습 자료라면 활성화 전에 저장소를 Private으로 전환하세요.

STUDYBOT_ENABLED=true로 설정하고 Actions → StudyBot → Run workflow를 실행합니다.
첫 실행은 지문만 기록합니다. 45분 이후 수동 실행하거나 다음 예약 실행을 기다립니다.
이미 저장이 끝난 예시를 검증할 때는 Run workflow의 `idle_seconds`에 `1`을 지정해 두 번 실행할 수 있습니다.
첫 실행의 관찰은 그대로 필요하며, 예약 실행과 기본 수동 실행은 2700초(45분)를 유지합니다.
설정 완료 전에는 StudyBot job이 건너뛰어집니다.

예약은 기본 브랜치에서만 실행됩니다. 수집과 노트 생성은 동일한 워크플로 안에서 이어집니다.
기본 브랜치의 보호 규칙이 직접 push를 금지하면 결과 저장도 실패합니다.
개인 전용 저장소에서 봇 갱신을 허용하거나 출력 브랜치를 분리하도록 변경해야 합니다.
원격 브랜치가 작업 중 바뀌면 push가 실패하며 강제 push하지 않습니다.

## 확인할 오류

- OIDC 실패: Provider 경로, 저장소·소유자 ID, 기본 브랜치 조건, IAM 전파 시간.
- Drive 403/404: 서비스 계정 뷰어 공유, 폴더 ID, Drive API 활성화.
- 모델 실패: 실제 모델 ID, 키·프로젝트 접근 권한.
- 계속 대기: busy 표시, 변경이 계속되는지, 안정 시간, 호출 한도.
- Git push 실패: contents:write 또는 브랜치 규칙, 다른 작업의 새 커밋.
- 자료가 너무 큼: 강의 폴더를 나누거나 제한값을 조정.

단위 테스트는 실제 계정 인증이나 모델의 학습 정리 품질까지 검증하지 않습니다.
