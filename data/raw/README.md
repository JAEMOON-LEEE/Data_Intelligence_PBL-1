# 수집 원본

- [한국어](ko/README.md): `ko/raw_ko.csv`, 1,200건.
- [영어](en/README.md): `en/raw_en.csv`, 800건.

스키마는 [데이터 안내](../README.md), 실행 환경은 [수집 폴더](../../collection/README.md)를 참고하세요.
이 폴더에는 코드가 없으므로 requirements를 두지 않습니다.
영어 `merge.py`는 이 폴더 직하위 CSV만 병합하며 `ko/`, `en/`는 재귀적으로 읽지 않습니다.
