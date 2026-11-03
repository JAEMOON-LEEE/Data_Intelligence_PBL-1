# 데이터 수집

한국어·영어 뉴스 수집 코드입니다. 실행 기준은 저장소 루트, Python 3.12입니다.

| 언어 | 코드 / 안내 | 수집 대상 | 설치 파일 |
| --- | --- | --- | --- |
| 한국어 | [crawling_ko.py](ko/crawling_ko.py) · [README](ko/README.md) | 뉴스엔, 6개 그룹 | [requirements](ko/requirements.txt) |
| 영어 | [README](en/README.md) | GDELT 검색 → 언론사 본문, 4개 그룹 | [requirements](en/requirements.txt) |

```bash
python -m pip install -r collection/requirements.txt
```

한국어는 BTS·블랙핑크·세븐틴·트와이스·베이비몬스터·코르티스 각 200건을 목표로 합니다.
영어는 앞의 4개 그룹을 수집한 뒤 최종 표본을 그룹당 200건으로 추출합니다.
수집 기간은 코드의 현재 날짜/설정에 따라 결정되므로 재실행 결과가 2026년 10월의 수록 데이터와 같지는 않습니다.

공통 컬럼은 `id, group, language, source, source_url, query, title, text,
text_type, published_at, collected_at`입니다. 댓글 수집 스크립트는 이 저장소에 없습니다.
수록 CSV의 실제 건수·스키마는 [데이터 안내](../data/README.md)를 확인하세요.
수집기의 기본 출력 위치와 팀 배포 파일 위치는 다릅니다. 각 언어 README의 경로를 따르세요.

수집 코드는 robots.txt와 요청 간격을 확인합니다. API·웹페이지 변경이나 접근 제한으로
목표 건수에 못 미칠 수 있으므로 수집 로그와 커버리지를 함께 확인합니다.
