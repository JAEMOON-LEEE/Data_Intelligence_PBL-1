# 영어 원본 (팀 배포 형식)

`raw_en.csv`: BTS·블랙핑크·세븐틴·트와이스 각 200건, 총 800건, 공통 11개 컬럼.
그룹 값은 `bts/블랙핑크/세븐틴/트와이스`, `source`는 언론사 도메인, `text_type=news`입니다.
날짜는 한국 시간으로 변환된 배포본입니다. CSV 읽기 인코딩은 `utf-8-sig`입니다.

[영어 수집](../../../collection/en/README.md)의 중간 `all_raw.csv`와 형식이 다릅니다.
기본 전처리에 바로 넣으면 출처 필터로 제거될 수 있으므로
[배포본 재처리 안내](../../../preprocessing/en/README.md)를 따르세요.
데이터 보관 폴더이므로 별도 requirements는 필요 없습니다.
