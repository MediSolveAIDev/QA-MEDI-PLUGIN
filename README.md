# qa-medi-plugin

사내 QA 자동화를 위한 Claude Code 플러그인.

## 설치

### 1. 마켓플레이스 등록

```bash
/plugin marketplace add MediSolveAIDev/QA-MEDI-PLUGIN
```

### 2. 플러그인 설치

```bash
/plugin install qa-medi-plugin@qa-medi-plugin
```

### 프로젝트에 자동 설정 (선택)

`.claude/settings.json`에 추가하면 팀원이 프로젝트 폴더를 trust할 때 자동으로 마켓플레이스가 등록됩니다:

```json
{
  "extraKnownMarketplaces": {
    "qa-medi-plugin": {
      "source": {
        "source": "github",
        "repo": "MediSolveAIDev/QA-MEDI-PLUGIN"
      }
    }
  },
  "enabledPlugins": {
    "qa-medi-plugin@qa-medi-plugin": true
  }
}
```

## 구성 요소

| 타입 | 경로 | 설명 |
|------|------|------|
| Agent | `agents/qa-agent.md` | QA 검증 에이전트 |
| Command | `commands/qa.md` | `/qa` 슬래시 커맨드 |
| Skill | `skills/qa-skill/SKILL.md` | QA 검증 스킬 |
| Hook | `hooks/hooks.json` | 파일 수정 감지 훅 |
| MCP Server | `mcp/server.py` | QA 도구 서버 |
