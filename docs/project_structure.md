# FastAPI vs NestJS 프로젝트 구조 비교

## FastAPI 일반적인 구조

```
project/
├── src/
│   ├── api/            # 라우터/컨트롤러 (NestJS의 controllers)
│   │   ├── v1/
│   │   │   ├── agents.py
│   │   │   └── chat.py
│   │   └── dependencies.py  # 의존성 주입
│   ├── core/           # 핵심 설정 및 공통 모듈
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   ├── models/         # Pydantic 모델 (NestJS의 DTOs)
│   │   ├── agent.py
│   │   └── chat.py
│   ├── schemas/        # DB 스키마 (NestJS의 entities)
│   │   └── agent.py
│   ├── services/       # 비즈니스 로직 (NestJS의 services)
│   │   ├── agent_service.py
│   │   └── openrouter_service.py
│   ├── db/            # 데이터베이스 관련
│   │   ├── base.py
│   │   └── session.py
│   └── utils/         # 유틸리티 함수
├── tests/
├── main.py            # 앱 진입점 (NestJS의 main.ts)
├── requirements.txt
└── .env

## NestJS vs FastAPI 개념 매핑

| NestJS | FastAPI |
|--------|---------|
| Controllers | Routers (api/) |
| Services | Services |
| Modules | Python Packages |
| DTOs | Pydantic Models |
| Entities | SQLAlchemy Models |
| Decorators | Depends() for DI |
| Guards | Dependencies |
| Interceptors | Middleware |
| Pipes | Pydantic Validation |

## 주요 차이점

1. **의존성 주입**: FastAPI는 `Depends()`를 사용
2. **모듈 시스템**: Python의 패키지/모듈 시스템 사용
3. **타입 체크**: Pydantic으로 런타임 검증
4. **데코레이터**: 더 간단하고 적음
```