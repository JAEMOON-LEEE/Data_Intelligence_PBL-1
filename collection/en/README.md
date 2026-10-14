# K-POP 국내 vs. 해외 반응: 영어 데이터 수집 및 전처리

> **GitHub 저장소 구조 안내**: 이 폴더(`collection/en/`)의 코드는 원래 한 폴더에서
> 실행하도록 만들어졌습니다. 다시 실행하려면 `collection/en/`과 `preprocessing/en/`의
> `.py` 파일을 한 폴더에 모아서 아래 순서대로 실행하세요.
> 최종 데이터: `data/raw/en/raw_en.csv`, `data/processed/en/processed_en.csv`
> (그룹당 200건, 한국어 데이터와 같은 컬럼 형식).


데이터 인텔리전스 PBL Module #1 (영어 파트).
BTS, SEVENTEEN, BLACKPINK, TWICE에 대한 **해외 영어 뉴스 기사 본문**을 수집하고
(GDELT + 본문 크롤링), 정제한 뒤 Count/TF-IDF 및 LDA 분석용으로 전처리합니다.
아래 **최종 파이프라인**부터 보면 됩니다. 영어 원문 README(`README.md`)의 뒷부분은
이전 계획(유튜브 댓글 등)으로, 참고용으로만 남겨 두었습니다.

## 설치

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

최종 파이프라인(GDELT + 크롤링)은 **API 키가 필요 없습니다.**
(YouTube / Guardian 키는 이전 계획에서만 사용)

## 최종 파이프라인: 4개 그룹, 영어 기사 본문 (확정, 2026-10-13)

그룹: **BTS, SEVENTEEN, BLACKPINK, TWICE** (보이그룹 2 + 걸그룹 2, HYBE / YG / JYP)
Colab에서 Google Drive 폴더 안에서 실행합니다. 연결이 끊겨도 캐시가 남아서 이어서 실행됩니다.

```bash
# 1단계  헤드라인 수집 (GDELT): 그룹당 최대 1,000개, 연도별로 균등하게 (2017~현재)
python collect_news_en_trial.py
#   -> data/raw/news_en_headlines.csv
#   -> data/check/spotcheck_kept.csv, rejected_<그룹>.csv   (필터 확인용, 꼭 읽어보기)

# 2단계  본문 크롤링: 모든 헤드라인 URL 방문 (중단돼도 이어서 실행 가능)
python collect_fulltext_en.py --limit 40      # 빠른 테스트
python collect_fulltext_en.py                 # 전체 (약 1~1.5시간)
#   -> data/extra/news_en_fulltext.csv, fetch_report.csv, fulltext_by_year.csv

# 3단계  정제: 광고/리다이렉트/중복 페이지, 그룹 이름이 없는 본문 제거
python clean_fulltext_en.py
#   -> data/extra/news_en_fulltext_clean.csv, site_list.csv

# 4단계  data/raw로 교체 (merge.py는 data/raw 안의 모든 csv를 합치므로 주의), 전처리
mkdir -p data/headline_version && mv data/raw/news_en_headlines.csv data/headline_version/
cp data/extra/news_en_fulltext_clean.csv data/raw/news_en_fulltext.csv
python merge.py && python preprocess_en.py && python check_data.py
#   -> data/raw/all_raw.csv, data/processed/en_processed.csv  (분석용 메인 파일)
```

### 5단계 (2026-10-14 팀 결정): 그룹당 200개, 연도별로 균등하게 추출
```bash
python make_subset_en.py            # 다른 개수는 --n 300
#   -> data/processed/en_processed_200.csv   (800개: 200 x 4그룹, 연도당 약 20개)
#   -> data/raw_subset/all_raw_200.csv
```
기사가 적은 연도는 있는 만큼 모두 사용하고 (SEVENTEEN 2017: 13, 2018: 7, 2026: 9,
TWICE 2018: 15), 남는 몫은 다른 연도로 넘어갑니다. 시드 고정(42)으로 재현 가능.

### 최종 영어 데이터셋 (2026-10-13 실행 결과)

| 단계 | 개수 |
|---|---|
| GDELT 헤드라인 (필터 적용, 그룹당 1,000개, 연도별 균등) | 고유 URL 3,998개 |
| 본문 크롤링 성공 (`ok`) | 1,777개 (44%) |
| 정제 후 (3단계) | **1,502개** |
| 전처리 후 | 1,502개 (너무 짧거나 중복된 문서 없음) |

그룹별: SEVENTEEN 412, BLACKPINK 377, BTS 364, TWICE 349. 본문 길이 중앙값 358단어.

연도별 기사 수:

| | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| BLACKPINK | 15 | 33 | 32 | 34 | 33 | 39 | 42 | 54 | 57 | 38 |
| BTS | 33 | 31 | 28 | 17 | 32 | 34 | 36 | 50 | 54 | 49 |
| SEVENTEEN | 13 | 7 | 22 | 21 | 53 | 70 | 53 | 90 | 74 | 9 |
| TWICE | 19 | 15 | 30 | 38 | 38 | 34 | 55 | 54 | 48 | 18 |

### 주요 파일

| 파일 | 내용 |
|---|---|
| `data/processed/en_processed.csv` | **분석용 메인 파일.** 기사 1,502개 + `clean_text`, `tokens`(TF-IDF/LDA에 바로 사용), `n_tokens` |
| `data/raw/all_raw.csv` | 전처리 전 원본 (헤드라인 = `title`, 본문 = `text`, URL, 날짜, 그룹) |
| `data/headline_version/news_en_headlines.csv` | 크롤링 전 헤드라인 4,000개 (수집 과정 기록용) |
| `data/extra/fetch_report.csv` | URL별 크롤링 결과 (ok, robots_disallowed, 404 등) |
| `data/extra/fulltext_by_year.csv` | 그룹 × 연도별 기사 수 |
| `data/extra/site_list.csv` | 출처 사이트 290개와 사이트별 기사 수 |
| `data/check/` | 헤드라인 필터 확인 샘플 (통과 / 제외된 헤드라인) |

## 데이터 카드 (영어 파트)

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
