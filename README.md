# IoT Recog Sleeping

## 프로젝트 구조

현재 프로젝트 구조는 초기 개발을 위한 최소 뼈대입니다.

```text
backend/   : FastAPI 서버
frontend/  : Streamlit 대시보드
vision/    : 카메라 및 인식 처리
```

추후 구현 방향이나 역할 분담에 따라 폴더 구조 및 파일명은 변경될 수 있습니다.

## 실행 방법

### 1. 가상환경 생성

```bash
python -m venv venv
```

### 2. 가상환경 활성화

#### Git Bash

```bash
source venv/Scripts/activate
```

#### CMD

```bash
venv\Scripts\activate
```

### 3. 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 4. 카메라 실행

```bash
python vision/camera.py
```

카메라 화면이 정상적으로 출력되면 성공입니다.

## Git 작업 규칙

- main 브랜치 직접 작업 금지
- 기능별 브랜치 생성 후 작업

예시:

```bash
git checkout -b feat/eye-detection
```
- 작업 완료 후 Pull Request(PR)를 생성하여 main 브랜치에 병합
