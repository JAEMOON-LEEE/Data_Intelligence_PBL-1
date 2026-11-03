# 한국어 뉴스 수집

`crawling_ko.py`는 뉴스엔 제목 검색으로 6개 그룹의 후보를 모으고,
제목·본문에 그룹명이 있는 기사를 2017년부터 실행 시점까지 연도별로 배분해 수집합니다.
API 키는 필요 없습니다. Python 3.12 가상환경에서 아래 명령을 저장소 루트 기준으로 실행합니다.

```bash
python -m pip install -r collection/ko/requirements.txt
python collection/ko/crawling_ko.py --help
python -c "from pathlib import Path; Path('work/collection-ko').mkdir(parents=True, exist_ok=True)"
python collection/ko/crawling_ko.py --output work/collection-ko/raw_ko.csv
```

| 옵션 | 기본값 | 의미 |
| --- | --- | --- |
| `--per-group` | `200` | 그룹별 목표 건수 |
| `--delay` | `3` | 요청 간격(초); 코드가 최소 2초 및 robots 규칙을 적용 |
| `--max-pages` | `0` | 검색어별 페이지 상한; 0은 목록 끝/반복까지 |
| `--output` | `데이터크롤링.csv` | 현재 작업 폴더 기준 CSV 경로 |

작게 확인하려면 새로운 출력 이름으로 `--per-group 2 --max-pages 1`을 추가합니다.
목표 미달은 종료 코드 2, 요청·파일 오류 등은 종료 코드 1입니다.

출력 CSV와 같은 위치에 `raw_ko.audit.jsonl`(수집 판단 기록),
`raw_ko.coverage.csv`(그룹·연도별 실적)가 생성됩니다. 출력 부모 폴더는 먼저 만들어야 하며,
세 파일 중 하나라도 이미 있으면 덮어쓰지 않고 중단합니다. 다른 `--output` 이름을 사용하세요.
완료 후 검토한 파일을 팀 배포 경로 `data/raw/ko/raw_ko.csv`로 반영합니다.

수집기 출력은 `source=뉴스엔`, `text_type=news`이며 11개 공통 컬럼을 가집니다.
수록 전처리본은 `text_type=full`로 저장되어 있어 원본과 차이가 있습니다.
현재 원본 1,200건과 전처리본 1,086건의 차이는 [데이터 안내](../../data/README.md)를 참고하세요.
