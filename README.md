# qa-medi-plugin

사내 QA 자동화를 위한 Claude Code 플러그인.

## 설치

Claude Code 마켓플레이스에서 설치:

```bash
claude plugin install qa-medi-plugin
```

또는 GitHub URL로 직접 설치:

```bash
claude plugin install github:k984530/qa-medi-plugin
```

## 구성 요소

| 타입 | 경로 | 설명 |
|------|------|------|
| Agent | `agents/qa-agent.md` | QA 검증 에이전트 |
| Command | `commands/qa.md` | `/qa` 슬래시 커맨드 |
| Skill | `skills/qa-skill/SKILL.md` | QA 검증 스킬 |
| Hook | `hooks/hooks.json` | 파일 수정 감지 훅 |
| MCP Server | `mcp/server.py` | QA 도구 서버 |

## 사용법

설치 후 Claude Code에서 `/qa` 커맨드로 QA 검증을 실행할 수 있습니다.

```
/qa [대상 파일 또는 디렉토리]
```
