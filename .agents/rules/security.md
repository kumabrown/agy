# 보안 가이드라인 (Security Guidelines)

## 1. 핵심 원칙 (Core Principles)
1. **자격 증명 및 기밀 정보 보호 (Secrets Protection)**:
   - API Key, 비밀번호, 인증 토큰(Credentials, Private Tokens), 개인 키(Private Key) 등 민감한 정보를 소스 코드에 하드코딩하거나 Git 저장소에 커밋하지 않습니다.
   - 환경 변수(`.env`), 시크릿 관리자(Secret Manager), 또는 별도의 로컬 설정 파일을 활용하고, 해당 파일들은 반드시 `.gitignore`에 등록하여 형상 관리에서 제외합니다.

2. **외부 입력값 검증 및 정제 (Input Validation & Sanitization)**:
   - 사용자 입력값, URL 파라미터, 외부 파일, 네트워크 응답 등 모든 외부 입력(External Inputs)은 처리 전에 반드시 유효성을 검증(Validation)하고 정제(Sanitization)합니다.
   - SQL Injection, XSS(Cross-Site Scripting), Path Traversal, 커맨드 인젝션(Command Injection) 등의 취약점을 예방하도록 방어적 프로그래밍을 적용합니다.

3. **신뢰할 수 없는 원격 스크립트 실행 방지 (Remote Script Execution)**:
   - 출처가 불분명하거나 검증되지 않은 원격 스크립트(Remote Scripts), 바이너리 실행 파일 및 임의 명령어를 실행하지 않습니다.
   - 외부 의존성 라이브러리(Dependencies)는 신뢰할 수 있는 공식 레지스트리(PyPI, npm 등)를 통해서만 도입하고, 버전을 명시하여 관리합니다.

## 2. 작업 환경 보안 수칙 (Workspace Security)
- 로컬 환경에서 실행되는 백그라운드 프로세스 및 임시 스크립트는 작업 완료 후 안전하게 종료하고 정리합니다.
- 민감한 데이터나 개인정보(PII)가 포함된 테스트 데이터는 마스킹(Masking)하거나 더미(Mock/Dummy) 데이터를 사용합니다.