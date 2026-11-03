# 영어 수집 통계

2026-10-13 전체 수집분의 기록입니다. 최종 800건 표본만의 통계가 아닙니다.

| 파일 | 내용 | 생성 코드 |
| --- | --- | --- |
| [fetch_report.csv](fetch_report.csv) | URL별 그룹·날짜·수집 상태 | `collect_fulltext_en.py` |
| [fulltext_by_year.csv](fulltext_by_year.csv) | 그룹·연도별 후보·시도·성공 건수 | `collect_fulltext_en.py` |
| [site_list.csv](site_list.csv) | 정제 후 출처 도메인별 기사 수 | `clean_fulltext_en.py` |

스크립트는 이 폴더가 아닌 저장소 루트의 `data/extra/`에 새 통계를 씁니다.
실행법과 환경은 [상위 README](../README.md) 및 [requirements.txt](../requirements.txt)를 사용합니다.
이 폴더는 CSV 기록만 보관하므로 별도 실행 환경 파일은 필요 없습니다.
