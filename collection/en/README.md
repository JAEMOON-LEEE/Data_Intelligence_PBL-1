# 영어 뉴스 수집 및 표본 생성

BTS·BLACKPINK·SEVENTEEN·TWICE의 해외 영어 기사를 GDELT로 검색하고 본문을 추출합니다.
아래 명령은 **저장소 루트**에서 실행합니다. 수집·전처리 파일을 옮길 필요가 없습니다.

## 설치

Python 3.12 가상환경을 만든 뒤 실행합니다.

```bash
python -m pip install -r collection/en/requirements.txt -r preprocessing/en/requirements.txt
python -m spacy download en_core_web_sm
```

GDELT 경로에는 API 키가 필요 없습니다. `config.py`의 `GROUPS`, `NEWS_PER_LANG=1000`,
`EN_SOURCES=['gdelt_news']`, `RANDOM_SEED=42`가 실행 설정입니다.
`collect_news_en_trial.py`는 종료일로 현재 날짜를 사용합니다. `config.END_DATE`는
별도 수집기 `collect_news_gdelt.py`에서만 적용되므로 trial 종료일 설정으로 사용하지 마세요.
Guardian을 별도로 시험할 때만 `.env.example`을 이 폴더의 `.env`로 복사해
`GUARDIAN_API_KEY`를 설정하고 `EN_SOURCES`에 `guardian`을 포함합니다.
기본 `EN_SOURCES=['gdelt_news']`에서는 Guardian을 조회하지 않습니다.
YouTube/Naver 수집 스크립트는 포함되어 있지 않습니다.

## 실행 순서

```bash
# 1. 헤드라인 검색
python collection/en/collect_news_en_trial.py
# 2. 기사 본문 수집 (캐시로 재개 가능)
python collection/en/collect_fulltext_en.py
# 3. 반복 본문·그룹명 없는 본문 제거
python collection/en/clean_fulltext_en.py
```

2단계를 먼저 작게 확인하려면 `--limit 40`을 사용합니다. 이후 전체 명령을 다시 실행하면
캐시를 재사용하고 결과 CSV를 다시 작성합니다. 기사 수와 접근 상태에 따라 소요 시간은 달라집니다.

`merge.py`는 `data/raw/` **직하위의 모든 CSV**를 합칩니다(하위 `en/`, `ko/`는 읽지 않음).
헤드라인과 본문을 섞지 않도록 4단계 전에 아래 Python 코드를 저장소 루트의 Python/Jupyter에서 실행합니다.
기존 중간 CSV가 있으면 먼저 확인해 별도 보관하세요.

```python
from pathlib import Path
import shutil

raw = Path('data/raw')
other = [p for p in raw.glob('*.csv') if p.name not in
         {'news_en_headlines.csv', 'news_en_fulltext.csv', 'all_raw.csv'}]
if other:
    raise RuntimeError(f'병합 전에 다른 CSV를 별도 보관하세요: {other}')
archive = Path('data/headline_version')
archive.mkdir(parents=True, exist_ok=True)
headline = raw / 'news_en_headlines.csv'
if headline.exists():
    destination = archive / headline.name
    if destination.exists():
        raise FileExistsError(f'기존 헤드라인 기록을 먼저 확인하세요: {destination}')
    shutil.move(str(headline), str(destination))
shutil.copyfile('data/extra/news_en_fulltext_clean.csv', raw / 'news_en_fulltext.csv')
```

```bash
# 4. 병합 → 전처리 → 품질 확인
python collection/en/merge.py
python preprocessing/en/preprocess_en.py
python preprocessing/en/check_data.py
# 5. 그룹당 200건 표본 (다른 크기는 --n 300 등)
python collection/en/make_subset_en.py --n 200
```

| 단계 | 생성 경로 (저장소 루트 기준) |
| --- | --- |
| 헤드라인 | `data/raw/news_en_headlines.csv`, `data/news_en_headlines_coverage.csv`, `data/check/` |
| 크롤링 | `data/extra/news_en_fulltext.csv`, `news_en_summary.csv`, `fetch_report.csv`, `fulltext_by_year.csv` (모두 `data/extra/`) |
| 캐시 | `data/cache_gdelt/`, `data/cache_fulltext/` |
| 정제 | `data/extra/news_en_fulltext_clean.csv`, `data/extra/site_list.csv` |
| 병합·전처리 | `data/raw/all_raw.csv`, `data/processed/en_processed.csv` |
| 표본 | `data/raw_subset/all_raw_200.csv`, `data/processed/en_processed_200.csv` |

수집 시점과 웹페이지 상태가 달라져 과거 건수와 같지 않을 수 있습니다.
그룹당 200건 미만이면 `make_subset_en.py`가 경고하고 확보된 만큼만 저장합니다.
`collect_news_gdelt.py`는 별도 날짜별 헤드라인 수집기이며 위 순서에 추가 실행할 필요가 없습니다.

## 배포 CSV와의 차이

수록 파일은 `data/raw/en/raw_en.csv`, `data/processed/en/processed_en.csv`(각 800건)입니다.
위 중간 파일과 경로·그룹명·출처·날짜 형식이 다릅니다. 중간 데이터는 대문자 영문 그룹명,
`source=gdelt_news`, UTC 날짜를 사용합니다. 팀 배포본은 `bts/블랙핑크/세븐틴/트와이스`,
출처 도메인, 한국 시간, `text_type=news`를 사용합니다.
배포본을 `preprocess_en.py`에 바로 입력하면 `EN_SOURCES` 필터에 의해 모두 제외될 수 있습니다.
배포본 재처리 방법은 [영어 전처리 안내](../../preprocessing/en/README.md)를 보세요.

`make_repo_export.py`는 **이전 단일 폴더 배치용** 도구입니다. 현재 저장소 루트에서 직접 실행하면
같은 폴더의 `preprocess_en.py` 등을 찾지 못합니다. 필요한 경우 별도 작업 폴더에
`collection/en/*.py`, `preprocessing/en/*.py`, 영어 수집 `requirements.txt`와 위 중간 `data/`를
모은 다음 실행하세요. 출력은 그 폴더의 `repo_export/`이며 기존 `repo_export/`를 삭제 후 재생성합니다.
이 도구가 생성하는 README와 환경 파일은 과거 템플릿이므로 현재 문서 위에 통째로 덮어쓰지 마세요.
`--no-text`는 `text`와 `clean_text`만 비우며 제목·URL·tokens는 유지합니다.

## 과거 실행 기록 (2026-10-13, 전체 수집분)

헤드라인 3,998개 → 본문 1,777개 → 정제·전처리 1,502개 → 이후 200개씩 추출해 800개.
이 수치는 재실행 보장값이 아닙니다. [stats](stats/README.md)는 전체 수집분의 기록입니다.

당시 정제 후 그룹별 건수는 SEVENTEEN 412, BLACKPINK 377, BTS 364, TWICE 349였으며
본문 길이 중앙값은 358단어였습니다. 아래는 기존 실험 문서의 연도별 기록입니다.

| 그룹 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BLACKPINK | 15 | 33 | 32 | 34 | 33 | 39 | 42 | 54 | 57 | 38 |
| BTS | 33 | 31 | 28 | 17 | 32 | 34 | 36 | 50 | 54 | 49 |
| SEVENTEEN | 13 | 7 | 22 | 21 | 53 | 70 | 53 | 90 | 74 | 9 |
| TWICE | 19 | 15 | 30 | 38 | 38 | 34 | 55 | 54 | 48 | 18 |

## 데이터 카드 (영어 파트, 당시 기록)

아래는 기존 실험의 방법·한계를 보존한 기록입니다. 상대 경로는 당시 중간 데이터 기준입니다.


**출처와 방법**
- GDELT DOC 2.0(전 세계 영어 뉴스 색인)으로 기사를 찾음. 한국 언론사와 그 영어판은
  제외 → 해외 보도만 포함. 기간 2017~현재 (GDELT 색인이 2017년부터 시작). 시간은 UTC.
- 언론사 페이지에서 trafilatura로 기사 본문 추출.

**책임 있는 수집**
- 모든 사이트의 robots.txt 확인. 크롤링을 금지하거나 robots.txt를 읽을 수 없는 사이트는 제외.
- 수업 프로젝트임을 밝히는 User-Agent 사용. 같은 사이트에는 최소 3초 간격으로 요청.
- theguardian.com 제외 (Guardian 개발자 등록 시 "본문을 저장하지 않음"으로 신청했기 때문).
- 본문은 집계 분석에만 사용하고 재배포하지 않음
  (`all_raw.csv`, `en_processed.csv`는 공개 저장소에 올리지 않기).

**필터**
- 헤드라인에 그룹 이름이 있어야 함. 일반 단어와 겹치는 이름 처리:
  "TWICE"/"BTS"는 대문자로 쓰였거나 K-pop 관련 단어/멤버 이름과 함께 나와야 함.
  일반적인 용법은 제거 ("twice as", "won twice", 방콕 BTS 스카이트레인, "behind the scenes").
  "Seventeen"은 잡지, 나이, 인도네시아 밴드 관련 기사 제거.
- 두 개 이상의 후보 그룹을 언급한 헤드라인은 제외 (기사 1개 = 그룹 1개).
- 스팸 제거: APK/MP3/배경화면 다운로드, 가사/코드 페이지, 퀴즈, 청원.
- 3단계 정제: 광고·리다이렉트·중복 배포(같은 기사가 여러 사이트에 게재) 페이지 263개,
  본문에 그룹 이름이 없는 12개 제거.

**전처리** (`preprocess_en.py`)
- spaCy 표제어 추출, 명사/고유명사/형용사/동사만 사용, 불용어 제거
  (spaCy 기본 + 도메인 불용어), 그룹 이름은 불용어로 제거, 헤드라인 끝의 언론사 이름 제거.
- 정제 과정에서 깨지는 멤버 이름은 미리 통일: S.Coups → Scoups, J-Hope → Jhope,
  V → Taehyung (BTS 기사만), The8 → Minghao, Rose/Rosé → Roseanne.

**한계 (보고서에 꼭 명시)**
- 크롤링 56% 실패: robots.txt 금지 (URL의 약 40%, 주로 K-pop 전문 사이트),
  403 차단, 404/410 삭제된 기사, 본문 없음.
- 출처 편향: 사이트 290개, 상위는 Billboard, Pinkvilla, Times of India.
  K-pop 전문 사이트가 크롤링을 막아서 기사의 약 20%가 인도 언론사에서 나옴.
- BTS의 크롤링 성공률이 가장 낮음 (39%).
- 기사 수가 적은 연도: 모든 그룹의 2017~2018년, SEVENTEEN의 2021년 이전과 2026년(올해는 진행 중).
  그룹 간 비교는 전체 기간으로 하고, 기사 수가 적은 연도의 연도별 결과는 신뢰도가 낮다고 표시.
- GDELT가 헤드라인의 "BTS"를 "BT"로 기록하는 경우가 있어, 두 그룹을 언급한 헤드라인
  일부가 필터를 통과함.
- K-pop 관련 단어 없이 첫 글자만 대문자인 TWICE 헤드라인("Twice tops chart")은
  일부러 제외함 (정확도 우선). `data/check/rejected_TWICE.csv` 참고.

## 참고: 이전 계획

- 유튜브 댓글 분석은 팀 결정으로 제외됨. 최종 비교는 한국어 뉴스 vs 영어 뉴스.
- BLACKPINK + SEVENTEEN 2개 그룹, 헤드라인 500개씩 버전(`make_final_subset.py`)은
  4개 그룹 본문 버전으로 대체됨.
