# 비개발자를 위한 해커톤 작업 사이클

요구사항 확인 → 계획 → 구현 → 검증 → 쉬운 설명 → 다음 작업을 반복하는 준비 도구입니다. 주 담당 AI와 설명 담당 subagent를 기본으로 사용하고, 중요한 기능에는 검토 담당을 호출합니다.

이 README는 **준비 도구의 안내**입니다. 시험에서 제공한 README는 과제 원문으로 보존합니다. 공식 시험 도구나 채점 기준이 아니며 실제 과제의 기능은 시작 후 요구사항에 맞춰 구현합니다.

## 처음 사용하기

1. 이 저장소 폴더를 Codex에서 엽니다.
2. `python tools/check_kit.py`로 양식과 에이전트 정의를 확인합니다.
3. `prompts/START_CYCLE.md`의 요청문을 대화에 붙여 넣습니다.
4. AI가 `explainer` subagent를 실제로 호출하는지 확인합니다. 파일 존재만으로 실행된 것은 아닙니다.
5. 간단한 연습은 `practice/CYCLE_TRIAL.md`로 시작하고, 경험은 `docs/FEEDBACK.md`에 남깁니다.

이 저장소에는 문서와 작업 절차, 빈 코드·데이터 폴더가 있습니다. 실행할 서비스와 자동 테스트는 과제를 선택한 뒤 만듭니다. 키트 검사 성공은 서비스 동작이나 subagent 호출 성공을 의미하지 않습니다.

## 기존 과제 폴더에 가져오기

저장소는 기존 과제 폴더 **밖에** clone합니다. 아래의 `/path/to/task`를 실제 과제 폴더로 바꿉니다. Windows에서도 따옴표로 감싼 절대 경로를 사용할 수 있습니다.

```sh
git clone https://github.com/hjjang3472-a11y/hackathon-starter.git
cd hackathon-starter
python tools/install_kit.py --target "/path/to/task"
python tools/install_kit.py --target "/path/to/task" --apply
```

첫 명령은 미리보기입니다. `--apply`를 붙여야 파일을 추가합니다. 기존 파일은 덮어쓰지 않습니다. 과제 README·코드·데이터·실행 설정을 복사하거나 교체하지 않습니다.

- 기존 `AGENTS.md`가 없으면 새 지침을 추가합니다.
- 기존 `AGENTS.md`가 있으면 별도 `AGENTS.practice.md`로 추가합니다. 자동으로 읽힌다고 가정하지 말고, 시작 프롬프트에서 읽고 적용 가능한 지침을 통합하도록 요청합니다.
- 기존 문서·에이전트 정의가 있으면 건너뜁니다. 출력의 `EXISTS` 항목은 주 담당이 확인합니다.
- 설치 후에는 **대상 과제 폴더**를 Codex에서 열고, 그곳의 `prompts/START_CYCLE.md`로 시작합니다.

## 역할과 기록

| 담당 | 하는 일 | 파일 담당 |
|---|---|---|
| 주 담당 | 요구사항·계획·구현·검증·사용자 대화 | 코드·테스트·SPEC·PLAN·VERIFY·RUN |
| explainer | 근거를 확인하고 쉬운 설명 작성 | docs/EXPLAIN.md |
| reviewer | 중요한 기능의 결함·검증 누락 검토 | 읽기·보고만 |

설명 담당은 주요 결정, 기능 검증, 중요한 수정, 최종 정리 시 호출합니다. 상시 감시 프로세스가 아닙니다. 같은 파일을 동시에 수정하지 않고, 작업 중인 코드는 변경이 끝난 시점에 검토합니다.

## 호환성과 도구

`.codex/agents/*.toml`은 프로젝트 범위의 사용자 정의 에이전트입니다. 모델·권한·MCP·개인 인증 설정은 고정하지 않습니다. 설치된 Codex 버전에 따라 사용자 정의 에이전트 인식 여부를 확인해야 합니다. 인식되지 않으면 `prompts/ROLE_FALLBACK.md`의 역할 지침을 일반 subagent에게 전달합니다. subagent 자체를 사용할 수 없으면 주 담당이 설명까지 수행하고 실제 운영 방식을 기록합니다.

별도 MCP·플러그인·Skill 설치는 이 사이클의 필수 조건이 아닙니다. 필요하면 `references/TOOLS.md`에 출처·권한·설치·동작 검증·대안을 기록한 뒤 연결합니다. 이 저장소의 역할 제한은 행동 지침이며 별도 보안 권한을 강제하는 장치가 아닙니다.

## 공개와 시험 사용

사용자가 공유한 기존 운영팀 안내는 시험 전 공개 저장소 준비, 과제 시작 후 clone, 2차 예선 결과 통지 전까지 공개 유지를 안내했습니다. 재시험 공지가 변경되면 최신 안내를 따릅니다. 시험 문제 원문·제공 데이터·개인정보·비밀키·비공개 코드를 이 공개 저장소에 올리지 않습니다. 서술형 평가 단계에는 AI 사용을 중지합니다.

이 저장소의 기본 코드·문서는 새로 작성한 범용 준비 자료입니다. 출처와 변경 이력은 `references/SOURCES.md`와 Git 이력으로 관리합니다.

공식 기능 참고: [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [커스터마이징](https://learn.chatgpt.com/docs/customization/overview).
