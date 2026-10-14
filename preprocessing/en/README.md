# 영어 전처리 코드

- `preprocess_en.py`: 정제(HTML, URL, 숫자, 기호 제거) → 소문자 → spaCy 표제어 추출 →
  명사/고유명사/형용사/동사만 사용 → 불용어 제거(spaCy + 도메인 불용어, 그룹명).
  멤버 이름은 정제 전에 통일: S.Coups → Scoups, J-Hope → Jhope, V → Taehyung(BTS),
  The8 → Minghao, Rose/Rosé → Roseanne.
- `check_data.py`: 그룹/연도별 개수, 본문 길이, 그룹별 상위 단어 확인.

설정 파일(`config.py`, `common.py`)은 `collection/en/`에 있습니다 (자동으로 찾음).
전체 실행 순서와 데이터 카드는 `collection/en/README.md` 참고.
