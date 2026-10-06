# 공식 자료 확인

조사 및 적용 버전 확인: 2026-10-06.
공식 GitHub 문서·SDK·API 정의를 직접 읽어 확인했다.

| 주제 | 확인한 내용 | 근거 |
|---|---|---|
| Colab Drive | mount, flush_and_unmount 동작 | [공식 구현](https://github.com/googlecolab/colabtools/blob/main/google/colab/drive.py) |
| Colab 로그인 | authenticate_user가 사용자 ADC를 설정 | [공식 구현](https://github.com/googlecolab/colabtools/blob/main/google/colab/auth.py) |
| Drive | drive.readonly, files.list/get/export, 내보내기 한도 | [API 정의](https://github.com/googleapis/google-api-python-client/blob/main/googleapiclient/discovery_cache/documents/drive.v3.json) |
| 다운로드 | 일반 파일과 Workspace 문서 내보내기 구분 | [Google 예제](https://github.com/googleworkspace/python-samples/tree/main/drive/snippets/drive-v3/file_snippet) |
| Google 인증 | WIF through service account, access_token_scopes, 1시간 토큰 | [공식 Action](https://github.com/google-github-actions/auth#readme) |
| IAM | Pool/Provider 생성, 조건식과 서비스 계정 정책 | [API 정의](https://github.com/googleapis/google-api-python-client/blob/main/googleapiclient/discovery_cache/documents/iam.v1.json) |
| GitHub 토큰 | GITHUB_TOKEN push가 다른 push 워크플로를 연쇄 호출하지 않음 | [공식 문서](https://github.com/github/docs/blob/main/data/reusables/actions/actions-do-not-trigger-workflows.md) |
| 예약 | 기본 브랜치, 지연 가능, 공개 저장소 비활성 조건 | [공식 문서](https://github.com/github/docs/blob/main/content/actions/reference/workflows-and-actions/events-that-trigger-workflows.md#schedule) |
| Actions 한도 | GitHub-hosted job 최대 6시간 | [공식 문서](https://github.com/github/docs/blob/main/content/actions/reference/limits.md) |
| 포함 사용량 | Free 월 2,000분 등의 표. 계정·러너별 적용 확인 필요 | [공식 표](https://github.com/github/docs/blob/main/data/reusables/billing/actions-included-quotas.md) |
| Gemini | API key, models.list, generate_content, JSON schema | [공식 SDK](https://github.com/googleapis/python-genai#readme) |
| Gemini 재시도 | attempts=1은 자동 재시도 없음, timeout은 밀리초 | [고정 버전 타입 정의](https://github.com/googleapis/python-genai/blob/v2.27.0/google/genai/types.py) |
| GitHub Models | 공식 문서상 2026-07-30 종료, 구현 후보에서 제외 | [공식 안내](https://github.com/github/docs/blob/main/content/github-models/index.md) |

[Gemini 공식 요금표](https://ai.google.dev/gemini-api/docs/pricing)를 확인했다.
현재 일부 모델에 무료 입력·출력 구간이 있지만, 접근 가능 모델과 실제 한도는 프로젝트별로 확인해야 한다.
무료 구간의 자료 이용 조건도 유료 구간과 다르다.
[공식 한도 안내](https://ai.google.dev/gemini-api/docs/rate-limits)와 AI Studio에서 실제 프로젝트 한도를 확인한다.
모델 이름을 하드코딩하지 않고 사용자가 명시하도록 했다.

고정한 Actions refs:

- checkout v7: 3d3c42e5aac5ba805825da76410c181273ba90b1
- setup-python v6: ece7cb06caefa5fff74198d8649806c4678c61a1
- google-github-actions/auth v3: 7c6bc770dae815cd3e89ee6cdf493a5fab2cc093
- google-genai: 2.27.0

GitHub 앱 연결의 계정 권한과 앱 설치 권한은 구분된다.
사용자에게 push 권한이 있어도 앱 설치·저장소 허용이 없으면 API 쓰기는 403으로 실패한다.

GitHub 앱 설정: [OpenAI 공식 안내](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt), [설치 대상 선택](https://github.com/apps/chatgpt-codex-connector/installations/select_target), [GitHub 설치·권한 관리](https://docs.github.com/en/apps/using-github-apps/reviewing-and-modifying-installed-github-apps).
계정의 Applications → Installed GitHub Apps → ChatGPT Codex Connector → Configure → Repository access에서 sys를 선택하고 저장한다.
