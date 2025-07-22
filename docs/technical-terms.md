---
tags:
  - glossary
  - technical-terms
  - learning
  - backend
  - llm
created: 2025-07-22
updated: 2025-07-22
aliases:
  - 기술 용어 사전
  - Technical Glossary
  - 용어 설명
description: LLM Agent 백엔드 프로젝트에서 사용되는 기술 용어 설명
status: published
category: reference
---

# 기술 용어 설명

> [!info] 개요
> LLM Agent 백엔드 서버 프로젝트에서 사용되는 주요 기술 용어들을 설명합니다.
> POC 개발을 위한 필수 개념들을 이해하기 쉽게 정리했습니다.

## 📑 목차

- [[#🏗️ 아키텍처 관련 용어]]
- [[#🌐 웹 프레임워크 및 프로토콜]]
- [[#💾 데이터베이스 및 캐싱]]
- [[#🤖 LLM 및 Agent 관련]]
- [[#🔧 개발 도구 및 라이브러리]]
- [[#📡 통신 프로토콜]]

---

## 🏗️ 아키텍처 관련 용어

### POC (Proof of Concept)

> [!note] 개념 증명
> - **정의**: 아이디어나 방법의 실현 가능성을 증명하기 위한 시범 프로젝트
> - **목적**: 본격적인 개발 전에 기술적 타당성을 검증
> - **특징**: 
>   - 핵심 기능만 구현
>   - 빠른 프로토타이핑
>   - 리스크 최소화

### API Gateway

> [!tip] API 게이트웨이
> - **정의**: 모든 API 요청의 단일 진입점 역할을 하는 서버
> - **주요 기능**:
>   - 요청 라우팅
>   - 인증/인가
>   - 속도 제한
>   - 로드 밸런싱
> - **예시**: Kong, AWS API Gateway, Nginx

### Backend Server

> [!note] 백엔드 서버
> - **정의**: 클라이언트 요청을 처리하고 비즈니스 로직을 실행하는 서버
> - **역할**:
>   - 데이터 처리
>   - 데이터베이스 연동
>   - API 제공
>   - 보안 처리

---

## 🌐 웹 프레임워크 및 프로토콜

### FastAPI

> [!example] 현대적인 Python 웹 프레임워크
> ```python
> from fastapi import FastAPI
> app = FastAPI()
> 
> @app.get("/")
> async def root():
>     return {"message": "Hello World"}
> ```
> - **특징**:
>   - 높은 성능 (Starlette 기반)
>   - 자동 API 문서 생성
>   - 타입 힌트 지원
>   - 비동기 프로그래밍 지원

### ASGI (Asynchronous Server Gateway Interface)

> [!info] 비동기 서버 게이트웨이 인터페이스
> - **정의**: Python 웹 서버와 애플리케이션 간의 표준 인터페이스
> - **장점**: 동시에 많은 요청 처리 가능
> - **구현체**: Uvicorn, Hypercorn, Daphne

### Uvicorn

> [!note] ASGI 서버
> - **정의**: FastAPI 애플리케이션을 실행하는 고성능 ASGI 서버
> - **사용법**:
>   ```bash
>   uvicorn main:app --reload
>   ```
> - **특징**: 빠른 속도, 개발 모드 지원

### SSE (Server-Sent Events)

> [!tip] 서버 전송 이벤트
> - **정의**: 서버에서 클라이언트로 실시간 데이터를 전송하는 기술
> - **특징**:
>   - 단방향 통신 (서버 → 클라이언트)
>   - HTTP 기반
>   - 자동 재연결
> - **사용 예**: 실시간 알림, 진행 상황 업데이트

### CORS (Cross-Origin Resource Sharing)

> [!warning] 교차 출처 리소스 공유
> - **정의**: 다른 도메인에서의 리소스 접근을 허용하는 메커니즘
> - **필요성**: 브라우저 보안 정책으로 인해 필요
> - **설정 예**:
>   ```python
>   app.add_middleware(
>       CORSMiddleware,
>       allow_origins=["http://localhost:3000"],
>       allow_methods=["*"],
>       allow_headers=["*"],
>   )
>   ```

---

## 💾 데이터베이스 및 캐싱

### SQLite

> [!note] 경량 데이터베이스
> - **정의**: 서버가 필요 없는 파일 기반 데이터베이스
> - **장점**:
>   - 설치 불필요
>   - 단일 파일로 관리
>   - POC에 적합
> - **단점**: 동시 쓰기 제한

### SQLAlchemy

> [!example] Python ORM
> - **정의**: Object-Relational Mapping 라이브러리
> - **역할**: Python 객체와 데이터베이스 테이블 매핑
> - **예시**:
>   ```python
>   class User(Base):
>       __tablename__ = "users"
>       id = Column(Integer, primary_key=True)
>       name = Column(String)
>   ```

### Redis

> [!tip] 인메모리 데이터 저장소
> - **정의**: 메모리 기반의 키-값 저장소
> - **용도**:
>   - 캐싱
>   - 세션 관리
>   - 실시간 데이터 처리
> - **특징**: 매우 빠른 읽기/쓰기 속도

### aiosqlite / aioredis

> [!note] 비동기 데이터베이스 드라이버
> - **정의**: SQLite와 Redis의 비동기 Python 클라이언트
> - **장점**: 
>   - 논블로킹 I/O
>   - 더 나은 성능
>   - FastAPI와 완벽 호환

---

## 🤖 LLM 및 Agent 관련

### LLM (Large Language Model)

> [!info] 대규모 언어 모델
> - **정의**: 방대한 텍스트 데이터로 학습된 AI 모델
> - **예시**: GPT-4, Claude, Gemini
> - **능력**:
>   - 자연어 이해 및 생성
>   - 코드 작성
>   - 질문 답변

### Agent

> [!example] LLM 에이전트
> - **정의**: 특정 작업을 수행하도록 설계된 LLM 기반 시스템
> - **구성 요소**:
>   - 프롬프트 분석기
>   - Tool 선택기
>   - 계획 수립기
>   - 실행기
> - **예시**: 코드 작성 에이전트, 검색 에이전트

### OpenRouter

> [!tip] LLM 라우팅 서비스
> - **정의**: 다양한 LLM 모델에 통합 접근을 제공하는 서비스
> - **장점**:
>   - 여러 모델 쉽게 전환
>   - 통합 API
>   - 비용 최적화
> - **지원 모델**: Claude, GPT-4, Gemini 등

### Tool

> [!note] 에이전트 도구
> - **정의**: Agent가 특정 작업을 수행하기 위해 사용하는 기능
> - **예시**:
>   - 웹 검색 도구
>   - 코드 실행 도구
>   - 데이터베이스 쿼리 도구
>   - 파일 시스템 접근 도구

### Prompt

> [!info] 프롬프트
> - **정의**: LLM에게 전달하는 입력 텍스트
> - **구성**:
>   - 시스템 메시지
>   - 사용자 입력
>   - 컨텍스트
> - **중요성**: 프롬프트 품질이 응답 품질 결정

---

## 🔧 개발 도구 및 라이브러리

### Pydantic

> [!example] 데이터 검증 라이브러리
> ```python
> from pydantic import BaseModel
> 
> class User(BaseModel):
>     name: str
>     age: int
>     email: str
> ```
> - **역할**: 
>   - 타입 검증
>   - 데이터 직렬화
>   - 설정 관리

### python-dotenv

> [!note] 환경 변수 관리
> - **정의**: .env 파일에서 환경 변수를 로드하는 라이브러리
> - **사용법**:
>   ```python
>   from dotenv import load_dotenv
>   load_dotenv()
>   ```

### structlog

> [!tip] 구조화된 로깅
> - **정의**: JSON 형식의 구조화된 로그를 생성하는 라이브러리
> - **장점**:
>   - 로그 분석 용이
>   - 메타데이터 추가 가능
>   - 성능 우수

### httpx / aiohttp

> [!note] HTTP 클라이언트
> - **httpx**: 동기/비동기 지원 HTTP 클라이언트
> - **aiohttp**: 완전 비동기 HTTP 클라이언트/서버
> - **용도**: 외부 API 호출 (OpenRouter 등)

---

## 📡 통신 프로토콜

### JSON-RPC

> [!info] JSON 원격 프로시저 호출
> - **정의**: JSON을 사용한 원격 프로시저 호출 프로토콜
> - **구조**:
>   ```json
>   {
>     "jsonrpc": "2.0",
>     "method": "get_response",
>     "params": {"prompt": "Hello"},
>     "id": 1
>   }
>   ```
> - **장점**: 간단하고 명확한 구조

### HTTP

> [!note] HyperText Transfer Protocol
> - **정의**: 웹에서 데이터를 주고받는 프로토콜
> - **메서드**: GET, POST, PUT, DELETE 등
> - **상태 코드**: 200 (성공), 404 (찾을 수 없음), 500 (서버 오류)

### WebSocket

> [!tip] 양방향 통신 프로토콜
> - **정의**: 실시간 양방향 통신을 위한 프로토콜
> - **특징**:
>   - 지속적인 연결
>   - 낮은 지연시간
>   - 실시간 통신
> - **비교**: SSE는 단방향, WebSocket은 양방향

---

## 📚 추가 학습 자료

> [!success] 다음 단계
> - [[project-structure|프로젝트 구조 문서]]
> - [[architecture|아키텍처 설계 문서]]
> - [FastAPI 튜토리얼](https://fastapi.tiangolo.com/tutorial/)
> - [Python 비동기 프로그래밍](https://docs.python.org/3/library/asyncio.html)
> - [Redis 기초](https://redis.io/docs/getting-started/)

> [!quote]
> "복잡한 시스템도 기본 개념의 조합입니다. 하나씩 이해하면 전체가 보입니다."