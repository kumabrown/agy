# 파이썬 코드 스타일 및 품질 가이드라인 (Python Code Style & Quality Guidelines)

## 1. 명명 규칙 (Naming Conventions - PEP 8)
- **변수, 함수, 메서드, 모듈명**: `snake_case` (예: `calculate_total`, `user_id`, `process_data`)
- **클래스명 및 커스텀 예외**: `PascalCase` (예: `UserProfile`, `DatabaseConnectionError`)
- **상수명**: `UPPER_SNAKE_CASE` (예: `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`)
- **내부 사용/비공개 멤버**: 단일 밑줄 접두사 `_leading_underscore` (예: `_internal_cache`)

## 2. 타입 힌트 (Type Annotations - Python 3.10+)
- 함수의 파라미터와 반환값에는 항상 명시적인 타입 힌트를 작성합니다.
- 파이썬 3.10+ 유니온 구문(`|`)을 적극 활용합니다 (`Optional[str]` 대신 `str | None`, `Union[int, float]` 대신 `int | float`).
- `typing.List`, `typing.Dict` 대신 내장 제네릭(`list[str]`, `dict[str, Any]`, `tuple[int, ...]`)을 사용합니다.

## 3. 파이썬스러운 관용구 (Pythonic Idioms)
- **객체 지향 경로 처리 (`pathlib.Path`)**: 문자열 기반 `os.path` 대신 `pathlib.Path`를 의무적으로 사용합니다.
- **정형 데이터 구조화 (`@dataclass`)**: 단순 딕셔너리 남용 대신 `@dataclass`를 사용하여 데이터 필드를 명확히 정의합니다.
- **안전한 자원 관리 (`with` 컨텍스트 매니저)**: 파일, 네트워크 소켓, DB 커넥션, 락(Lock) 등 자원 해제가 필요한 모든 작업에는 반드시 `with` 구문을 사용합니다.
- **직관적인 순회 (Iteration)**: 인덱스로 요소에 접근(`range(len(...))`)하지 않고, 요소를 직접 순회하거나 인덱스가 필요할 땐 `enumerate()`를 사용합니다. 둘 이상의 리스트는 `zip()`을 활용합니다.
- **컴프리헨션(Comprehension)의 절제된 활용**: 리스트/딕셔너리 생성 시 컴프리헨션을 활용하되, 가독성을 해치는 2단계 이상의 중첩 컴프리헨션은 피합니다.
- **EAFP 원칙 적용**: 사전 검사(`if key in dict:`)를 남발하기보다, 딕셔너리 `.get()` 메서드를 활용하거나 직접 시도하고 예외를 명확히 처리(`try-except`)하는 방식을 지향합니다.

## 4. 견고한 예외 처리 (Error Handling)
- 예외 유형이 없는 `bare except:`나 모든 오류를 무시하는 `except Exception: pass`는 절대 금지합니다.
- 구체적인 예외 클래스를 명시하여 포착합니다 (`except (KeyError, ValueError) as e:`).
- 상위 호출자에게 예외를 전파할 때는 원본 컨텍스트를 유지하기 위해 `raise ... from e`를 고려합니다.

## 5. 주석 및 문서화 (Documentation)
- 공개 모듈, 클래스, 함수에는 명확한 설명(Docstring)을 작성합니다.
- 주석은 코드 자체가 무엇(What)을 하는지가 아니라, '왜(Why)' 그렇게 구현했는지 배경과 의도를 설명해야 합니다.