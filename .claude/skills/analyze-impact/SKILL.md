# /analyze-impact - Impact Analyzer

> 크로스 프로젝트 영향도를 분석합니다. SSO 등 공통 모듈 변경 시 어떤 프로젝트에 영향이 있는지 파악합니다.

---

## 1. 개요

- **역할**: 하나의 프로젝트 변경이 다른 프로젝트에 미치는 영향 분석
- **호출 시점**: Phase 4 (최종 보고) 중 크로스 프로젝트 해당 시, 또는 수동 요청
- **출력**: `data/reviews/{PROJECT}_{version}_{feature}_impact.json`

---

## 2. 실행

```
사용자: /analyze-impact SSO v2.0.0 로그인 정책 변경
사용자: SSO 변경 영향도 분석해줘
```

---

## 3. 분석 대상

### 3.1 크로스 프로젝트 매트릭스

| 변경 프로젝트 | 영향 가능 프로젝트 | 공통 영역 |
|---------------|-------------------|-----------|
| SSO | SAY, BAY | 인증, 세션, 권한 |
| SAY | BAY (공통 컴포넌트 시) | UI 컴포넌트, API |
| BAY | SAY (공통 컴포넌트 시) | UI 컴포넌트, API |

### 3.2 분석 항목

1. **인증/세션**: 로그인, 토큰 만료, 권한 체계 변경
2. **API 변경**: 엔드포인트 추가/삭제/수정, 응답 형식 변경
3. **공통 UI**: 공유 컴포넌트, 디자인 시스템 변경
4. **데이터 모델**: DB 스키마, 공통 코드값 변경
5. **인프라**: 배포 순서, 환경 설정 의존성

---

## 4. 출력 형식

```json
{
  "source": {
    "project": "SSO",
    "version": "v2.0.0",
    "feature": "로그인 정책 변경",
    "changes": [
      "세션 만료 시간 30분 → 15분 변경",
      "비밀번호 정책 강화 (특수문자 필수)"
    ]
  },
  "impact_analysis": [
    {
      "target_project": "SAY",
      "impact_level": "high",
      "affected_areas": [
        {
          "area": "세션 관리",
          "description": "세션 만료 시간 변경으로 장시간 상담 중 세션 끊김 가능",
          "affected_tc": ["Row 8 (URL 직접 접근)", "QA-010 (세션 만료)"],
          "action_required": "TC 수정 + 재테스트 필요"
        }
      ]
    },
    {
      "target_project": "BAY",
      "impact_level": "medium",
      "affected_areas": [
        {
          "area": "로그인 화면",
          "description": "비밀번호 정책 변경 안내 문구 추가 필요",
          "affected_tc": [],
          "action_required": "신규 TC 추가"
        }
      ]
    }
  ],
  "summary": {
    "total_affected_projects": 2,
    "high_impact": 1,
    "medium_impact": 1,
    "low_impact": 0,
    "tc_to_update": 2,
    "tc_to_add": 1
  },
  "recommendation": "SAY 프로젝트 세션 관련 TC 우선 재테스트 권장"
}
```

---

## 5. 영향도 레벨

| 레벨 | 기준 | 조치 |
|------|------|------|
| **high** | 핵심 기능 동작 변경, TC 수정 필수 | 즉시 TC 수정 + 재테스트 |
| **medium** | 부가 기능 영향, 신규 TC 필요 가능 | TC 추가 검토 |
| **low** | UI/문구 변경, 기능 영향 없음 | 모니터링 |
| **none** | 영향 없음 | 조치 불필요 |

---

## 6. 규칙

- `config/projects/*.json`에서 전체 프로젝트 목록 참조
- 기존 TC(`data/tc/`) 파일 스캔하여 영향받는 TC 행 번호 자동 매핑
- high 영향 1건 이상 시 **★ 승인 6** 트리거
- 분석 근거 명시 (추측 금지, 변경사항 기반으로만 판단)
