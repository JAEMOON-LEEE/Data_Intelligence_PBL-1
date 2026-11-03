# K-POP 국내 vs 해외 언론 보도 분석

데이터인텔리전스 PBL 모듈 #1 팀 프로젝트입니다.
한국어 뉴스와 해외 영어 뉴스 기사를 수집·전처리하고, LDA 토픽 모델링으로 국내와 해외 언론이 각 그룹을 어떤 주제로 다루는지 비교합니다.

## 설치 및 실행 환경

기준 환경은 **Python 3.12**입니다. 아래 명령은 저장소 최상위 폴더에서 실행합니다.
수집·전처리·분석·시각화에 필요한 패키지는 루트의 [requirements.txt](requirements.txt) 하나로 설치합니다.

```powershell
# Windows PowerShell: Python 3.12로 가상환경 생성 및 활성화
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python3.12 -m venv .venv
source .venv/bin/activate
```

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m pip check
python -m jupyterlab
```

PowerShell에서 활성화가 차단되면 위 명령의 `python` 대신 `.\.venv\Scripts\python.exe`를 사용합니다.
spaCy 영어 모델 다운로드는 영어 전처리를 다시 수행할 때 필요합니다.
NumPy와 pyLDAvis의 호환 범위는 requirements에 반영되어 있으므로 해당 파일을 기준으로 설치합니다.

이미 수록된 전처리 CSV로 분석할 때는 수집·전처리를 다시 실행할 필요가 없습니다.
Jupyter에서 [한국어 LDA](Topic_Modeling_ko.ipynb) 또는 [영어 LDA](Topic_Modeling_en.ipynb)를 열고
가상환경의 Python 커널로 위에서 아래로 실행합니다. 노트북의 작업 폴더는 저장소 루트로 맞춥니다.
하위 폴더의 노트북에서는 첫 셀에 `%cd "저장소의 실제 절대 경로"`를 실행한 뒤 아래 경로 안내를 적용합니다.

라이브러리·언어 모델 버전이나 수집 시점이 달라지면 과거 출력과 토큰·토픽·수치가 달라질 수 있습니다.

## 분석 대상 및 범위

| 항목 | 기준 |
| --- | --- |
| 분석 그룹 | 방탄소년단, 블랙핑크, 세븐틴, 트와이스, 베이비몬스터, 코르티스 |
| 언어 | 한국어(`ko`), 영어(`en`) |
| 자료 유형 | 뉴스 기사 (유튜브 댓글은 팀 결정으로 제외) |
| 수록 데이터의 기간 | 2017년 1월 ~ 2026년 10월 (그룹별 범위는 다름) |
| 목표 건수 | 한국어: 그룹당 200건 / 영어: 베이비몬스터·코르티스를 제외한 4개 그룹, 그룹당 200건 |

## 폴더 구조

```text
.
├── collection/           # 데이터 수집 코드
│   ├── ko/               #   한국어 (뉴스엔 크롤링)
│   └── en/               #   영어 (GDELT + 본문 크롤링)
├── data/
│   ├── raw/{ko,en}/      # 수집한 원본 데이터
│   ├── processed/{ko,en}/# 전처리가 끝난 데이터
│   └── data_cards/       # 데이터 카드 보관 예정 (.gitkeep만 있음)
├── preprocessing/        # 전처리 코드
│   ├── ko/
│   └── en/
├── topic_modeling/       # 토픽 모델링 설명
├── visualization/        # 한국어·영어 빈도/TF-IDF/워드클라우드 노트북
├── k초기값 시각자료/        # k 선정용 그래프·pyLDAvis 캡처
├── requirements.txt      # 전체 실행 환경의 패키지 목록
├── Topic_Modeling_ko.ipynb  # 한국어 토픽 모델링 노트북
└── Topic_Modeling_en.ipynb  # 영어 토픽 모델링 노트북
```

세부 설명: [수집](collection/README.md), [전처리](preprocessing/README.md),
[데이터](data/README.md), [토픽 모델링](topic_modeling/README.md).
설치와 현재 저장소 배치에서의 실행 위치는 이 루트 README를 기준으로 합니다.

## 데이터

### 컬럼

```text
id, group, language, source, source_url, query, title, text, text_type, published_at, collected_at
```

| 컬럼 | 설명 |
| --- | --- |
| `id` | 문서의 고유 ID |
| `group` | 분석 대상 그룹명 |
| `language` | 본문 언어: `ko` 또는 `en` |
| `source` | 뉴스 매체명 |
| `source_url` | 원본 기사 링크 |
| `query` | 수집에 사용한 검색어 |
| `title` | 기사 제목 |
| `text` | 기사 본문 |
| `text_type` | 한국어 원본 `news`, 한국어 전처리본 `full`, 영어 원본·전처리본 `news` |
| `published_at` | 기사 작성일 |
| `collected_at` | 데이터 수집일 |

현재 수록된 전처리 CSV에는 아래 컬럼이 추가되어 있습니다.

| 컬럼 | 한국어 | 영어 |
| --- | --- | --- |
| `tokens` | JSON 리스트 (`["힘", "시기", ...]`) | 공백 구분 문자열 |
| `clean_text` | 없음 | 정제된 본문 |
| `n_tokens` | 없음 | 토큰 수 |

### 최종 데이터

| 언어 | 원본 | 전처리 | 문서 수 (원본 → 전처리) | 전처리본 그룹별 |
| --- | --- | --- | --- | --- |
| 한국어 | `data/raw/ko/raw_ko.csv` | `data/processed/ko/processed_ko.csv` | 1,200 → 1,086 | bts 199, 세븐틴 198, 트와이스 197, 블랙핑크 196, 베이비몬스터 153, 코르티스 143 |
| 영어 | `data/raw/en/raw_en.csv` | `data/processed/en/processed_en.csv` | 800 → 800 | bts, 블랙핑크, 세븐틴, 트와이스 각 200 |

한국어 원본은 6개 그룹 각 200건입니다. 현재 한국어 전처리 노트북은 추가 정제 컬럼을 저장하고
`text_type`을 변경하지 않으므로, 재실행 결과가 수록 전처리본과 같은 스키마·건수라고 가정하지 않습니다.

## 1. 데이터 수집 (`collection/`)

### 한국어 (`collection/ko/crawling_ko.py`)

- 출처: 뉴스엔(newsen.com) 기사 제목 검색
- 그룹당 200건, 확인된 후보 기사에서 연도별로 균등 배분
- 그룹명(한글·영문)이 제목 또는 본문에 있는 기사만 사용
- API 키 없이 실행하며, 수집 범위는 2017년부터 실행 시점까지임

```bash
python collection/ko/crawling_ko.py --help
# 새 이름으로 수집 결과 저장 (같은 이름의 결과·로그가 있으면 중단)
python collection/ko/crawling_ko.py --output data/raw/ko/raw_ko_new.csv
```

기본 출력은 현재 작업 폴더의 `데이터크롤링.csv`이며, 같은 위치에 `.audit.jsonl`, `.coverage.csv`도 생성됩니다.
`--output`의 부모 폴더는 미리 있어야 합니다. 수집 후 건수와 커버리지를 확인해 전처리 입력을 선택합니다.

### 영어 (`collection/en/`)

- GDELT DOC 2.0(전 세계 영어 뉴스 색인)으로 헤드라인을 찾고, trafilatura로 언론사 페이지에서 본문 추출
- 한국 언론사와 그 영어판은 제외 → 해외 보도만 포함 (GDELT 색인이 2017년부터 시작, 시간은 UTC)
- 실행 순서

| 단계 | 스크립트 | 내용 |
| --- | --- | --- |
| 1 | `collection/en/collect_news_en_trial.py` | 헤드라인 수집, 그룹당 최대 1,000개, 연도별 균등 |
| 2 | `collection/en/collect_fulltext_en.py` | 헤드라인 URL을 방문해 본문 크롤링 |
| 3 | `collection/en/clean_fulltext_en.py` | 광고·리다이렉트·중복 페이지, 그룹 이름이 없는 본문 제거 |
| 4 | `collection/en/merge.py` → `preprocessing/en/preprocess_en.py` → `preprocessing/en/check_data.py` | 병합, 전처리, 확인 |
| 5 | `collection/en/make_subset_en.py` | 그룹당 200개, 연도별 균등 추출 (시드 42) |

- 저장소 루트에서 `python <표의 스크립트 경로>`로 실행합니다. 설정 파일은 `collection/en/`에 있으며 전처리 스크립트가 자동으로 찾으므로 파일을 한 폴더로 옮길 필요가 없습니다.
- 기본 `EN_SOURCES=['gdelt_news']` 경로에는 API 키가 필요 없습니다. Guardian을 사용하려면 `EN_SOURCES`에 `guardian`을 포함하고 `GUARDIAN_API_KEY`를 설정합니다.
- `collect_news_en_trial.py`는 종료일로 현재 날짜를 사용합니다. `config.END_DATE`는 별도 수집기 `collect_news_gdelt.py`에만 적용됩니다.
- 4단계 전에 `data/raw/news_en_headlines.csv`는 별도 보관하고, 정제 결과 `data/extra/news_en_fulltext_clean.csv`를 `data/raw/news_en_fulltext.csv`로 복사합니다. `merge.py`는 `data/raw/` 직하위 CSV를 모두 읽으며 자신의 출력 `all_raw.csv`는 제외합니다. 다른 중간 CSV가 섞이지 않았는지 확인합니다.
- 병합·전처리 출력은 `data/raw/all_raw.csv`, `data/processed/en_processed.csv`입니다. 5단계는 `data/raw_subset/all_raw_200.csv`, `data/processed/en_processed_200.csv`를 생성합니다.
- 위 중간 파일은 수록 배포본 `data/raw/en/raw_en.csv`, `data/processed/en/processed_en.csv`와 경로·그룹명·출처 형식이 다릅니다. `make_repo_export.py`는 이전 단일 폴더 배치를 전제로 하므로 현재 저장소 루트에서 바로 실행하는 단계에 포함하지 않습니다.

수집 결과 (2026-10-13 실행 기록; 재수집 시 달라질 수 있음)

| 단계 | 개수 |
| --- | --- |
| GDELT 헤드라인 (필터 적용) | 고유 URL 3,998개 |
| 본문 크롤링 성공 | 1,777개 (44%) |
| 정제 후 | 1,502개 |
| 그룹당 200개 추출 (최종) | 800개 |

헤드라인 필터

- 헤드라인에 그룹 이름이 있어야 함. "TWICE", "BTS"는 대문자로 쓰였거나 K-pop 관련 단어·멤버 이름과 함께 나와야 함 ("twice as", 방콕 BTS 스카이트레인 등 일반 용법 제거). "Seventeen"은 잡지·나이·인도네시아 밴드 관련 기사 제거
- 두 개 이상의 그룹을 언급한 헤드라인은 제외 (기사 1개 = 그룹 1개)
- 스팸 제거: APK/MP3/배경화면 다운로드, 가사/코드 페이지, 퀴즈, 청원

당시 수집 통계·필터·한계는 [영어 수집 기록](collection/en/README.md) 참고.

## 2. 전처리 (`preprocessing/`)

### 공통

- 중복 데이터와 빈 본문 제거
- HTML 태그, URL, 광고 문구 등 불필요한 내용 제거
- 연속된 공백과 줄바꿈 정리

### 한국어

- 노트북: [preporcess_ko.ipynb](preprocessing/ko/preporcess_ko.ipynb) (현재 저장소의 실제 파일명)
- Kiwi 형태소 분석과 사용자 사전, 그룹·멤버·소속사 등 표기 정규화
- Kiwi 기본·뉴스·그룹명 불용어 제거 후 일반명사·고유명사 및 지정한 외국어 변환 사용
- 서로 다른 문서 3개 이상에 등장한 단어만 유지하고 빈 토큰 문서 제거
- 첫 셀의 `csv_path`, 마지막 셀의 `output_path`는 작성자의 바탕화면 절대 경로입니다. 작업 폴더를 저장소 루트로 맞추고 `csv_path = Path('data/raw/ko/raw_ko.csv')`, `output_path = Path('data/processed/ko/processed_ko_new.csv')`로 변경한 뒤 실행합니다.
- 현재 노트북 출력에는 수록 CSV의 `tokens` 외에 `clean_text`, `normalized_text`, `group_normalized`, `processed_text`, `token_count`도 포함됩니다. 새 결과의 건수·컬럼을 확인한 뒤 분석에 사용합니다.

### 영어 (`preprocessing/en/preprocess_en.py`)

1. 정제: HTML 엔티티·태그, URL, @멘션, `#`, 이모지, 숫자 제거
2. 소문자 변환, spaCy 표제어 추출
3. 명사·고유명사·형용사·동사만 사용
4. 불용어 제거: spaCy 기본 + 도메인 불용어(song, video, music, member, girl, band 등) + 그룹명
5. 2글자 미만 토큰 제거, 토큰 3개 미만 문서 제거, 그룹 안에서 중복 문서 제거
6. 헤드라인 끝의 언론사 이름 제거

- 멤버 이름은 분석 결과로 보고 **일부러 남김**. 정제 과정에서 깨지는 이름은 미리 통일: S.Coups → Scoups, J-Hope → Jhope, V → Taehyung (BTS 기사만), The8 → Minghao, Rose/Rosé → Roseanne
- `check_data.py`: 그룹·연도별 개수, 본문 길이, 그룹별 상위 단어 확인
- 기본 입력은 수집 중간 데이터 `data/raw/all_raw.csv`입니다. 배포본 `data/raw/en/raw_en.csv`는 `source`가 언론사 도메인이므로 기본 `EN_SOURCES=['gdelt_news']` 필터에서 모두 제외될 수 있습니다. 재처리할 때는 출처 필터와 그룹명(`bts/블랙핑크/세븐틴/트와이스` → `BTS/BLACKPINK/SEVENTEEN/TWICE`)을 함께 맞춰야 합니다.

수록 데이터의 현황만 확인할 때는 아래 명령을 사용합니다.

```bash
python preprocessing/en/check_data.py data/raw/en/raw_en.csv data/processed/en/processed_en.csv
```

## 3. 토픽 모델링

- 노트북: `Topic_Modeling_ko.ipynb`, `Topic_Modeling_en.ipynb` (레포 최상위)
- 라이브러리: Gensim (`LdaModel`, `CoherenceModel`), pyLDAvis
- 수업 실습 7-2 노트북의 셀 순서를 따름
- 언어별로 모델을 따로 학습 (한국어 k=7, 영어 k=9)
- 불용어는 전처리 결과를 그대로 사용
- 아래 결과 표는 전체 토픽의 초기 해석 기록이며, [토픽 모델링 문서](topic_modeling/README.md)는 대표 문서 확인 후 수정한 라벨과 노이즈 제외·재정규화 결과를 담음
- 노트북은 위에서 아래로 실행하며 결과는 셀 출력으로 표시됨. 그래프 셀의 `Malgun Gothic`은 Windows 폰트이므로 다른 운영체제에서는 설치된 한글 폰트로 변경

### 진행 순서

| 셀 | 내용 |
| --- | --- |
| 0 | 데이터 불러오기, `tokens`를 단어 리스트로 변환 (한국어 `json.loads`, 영어 `.str.split()`) |
| 1 | `Dictionary` 생성 → `filter_extremes` → `doc2bow`로 corpus 생성 |
| 2 | `LdaModel` 학습 (`passes=5`) |
| 3 | `print_topics`로 토픽별 상위 단어 확인 |
| 4 | `get_document_topics`로 문서별 토픽 분포 확인 |
| 5 | pyLDAvis 시각화 |
| 6 | `CoherenceModel`(u_mass)로 응집도 계산 |
| 8 | `show_coherence`로 k=2~15 혼란도·응집도 비교 |
| 9–10 | 문서별 토픽 비중을 `group`으로 묶어 평균 |
| 11–14 | 노이즈 토픽 제외·재정규화, 기간 확인, 막대그래프 |
| 15–17 | 공통 카테고리로 묶기, 토픽별 대표 문서 확인 |

`show_coherence`는 `passes`를 지정하지 않는다. 위에 적은 최종 모델은 `passes=5`로 다시 학습한 결과이다.

### 주요 설정값

| 항목 | 한국어 | 영어 | 설명 |
| --- | --- | --- | --- |
| `no_below` | 2 | 2 | 2개 미만 문서에만 나온 단어 제외 |
| `no_above` | 0.5 | 0.5 | 전체 문서의 50% 넘게 나온 단어 제외 |
| `keep_n` | None | None | 단어 수 상한 없음 |
| `num_topics` | 7 | 9 | 아래 k 선정 참고 |
| `passes` | 5 | 5 | 최종 모델 |
| `random_state` | 7 | 7 | 결과 재현용 |
| 어휘 수 | 3,369 → 3,368 | 11,596 → 6,355 | `filter_extremes` 전 → 후 |
| 문서 수 | 1,086 | 800 | 결측 `tokens` 제거 후 |

### 토픽 수(k) 선정

혼란도는 작을수록, 응집도는 클수록 좋음. gensim의 `log_perplexity`는 로그 값이라 클수록 좋음. 교재 기준에 따라 수치와 토픽 해석을 함께 봄.

- **한국어: k = 7**
  - 응집도: k=2~3이 가장 높지만 그룹 간 비교에는 토픽이 너무 뭉뚱그려짐. k=6 이후 구간에서는 7이 첫 번째 봉우리 (k=6 −3.363, k=7 −2.892, k=8 −3.488)
  - pyLDAvis: k=10에서는 토픽 여러 쌍이 거의 겹침
  - 그래프: `k초기값 시각자료/coherence_k2-6.png`, `perplexity_k2-6.png`, `k10_pyLDAvis.png`
- **영어: k = 9**
  - 응집도 최댓값은 k=2 (−1.009). 그다음 봉우리는 k=9 (−1.024). 이웃인 k=8은 −1.047, k=10은 −1.075
  - `log_perplexity`는 k가 커질수록 감소 (−7.756 → −8.336). 이 로그 값의 감소 자체를 성능 개선으로 해석하지 않음
  - 그룹 비교에 쓰도록 최종 모델은 k=9
  - 그래프: `coherence_en.png`, `perplexity_en.png`. `k7_pyLDAvis_en.png`는 비교용 k=7 화면 (원 7개)

### 한국어 결과 (k = 7)

토픽 번호와 비중은 pyLDAvis 화면 기준이다. 노트북의 `Topic1`~`Topic7`은 gensim의 0~6번 토픽에 대응하며 아래 번호와 순서가 다르다. 다음 표는 노이즈 제외 전의 초기 해석 기록이다.

| 토픽 | 비중 | 주요 단어 | 해석 |
| --- | --- | --- | --- |
| 1 | 29.5% | 곡, 앨범, 차트, 뮤직비디오, 데뷔, 기록, 발매 | 음원·차트·뮤비 성과 |
| 2 | 17.4% | 앨범, 무대, 음악, 미국, 차트, 공연, 빌보드 | 글로벌 활동·수상 |
| 3 | 14.3% | 와이지엔터테인먼트, 제니, 공식, 모습, 매력 | 멤버 SNS·비주얼 |
| 4 | 14.2% | 브랜드, 지수, 분석, 평판, 아티스트, 소속사 | 브랜드평판 (노이즈) |
| 5 | 10.4% | 일본, 무대, 공연, 콘서트, 투어, 관객, 현지 | 일본 공연·투어 |
| 6 | 8.7% | 일정, 인천국제공항, 출국, 입국, 패션 | 공항 출국 (노이즈) |
| 7 | 5.6% | 서울, 로라, 아현, 파리타, 아사, 치키타 | 베이비몬스터 멤버 |

그룹별 평균 비중 상위 (문서-토픽 확률의 그룹 평균):

| 그룹 | 1위 | 2위 |
| --- | --- | --- |
| bts | 글로벌 활동 28.7% | 음원·차트 21.2% |
| 블랙핑크 | 공항 출국 30.1% | 멤버 SNS 27.2% |
| 세븐틴 | 공항 출국 34.0% | 음원·차트 14.3% |
| 트와이스 | 공항 출국 33.2% | 음원·차트 18.8% |
| 베이비몬스터 | 공항 출국 42.7% | 멤버 SNS 25.2% |
| 코르티스 | 음원·차트 48.3% | 공항 출국 20.2% |

### 영어 결과 (k = 9)

번호와 비중은 pyLDAvis 기준이며, 노이즈 제외 전의 초기 해석 기록이다.

| 토픽 | 비중 | 주요 단어 | 해석 |
| --- | --- | --- | --- |
| 1 | 18.4% | love, korean, track, performance, debut, scoups | 활동·퍼포먼스 |
| 2 | 14.3% | south, korea, military, jin, service, tour | BTS 군 복무 |
| 3 | 13.3% | solo, perform, lisa, tour, concert, stage, jihyo | 솔로·공연 |
| 4 | 11.1% | tour, ticket, award, concert, billboard | 투어·티켓·시상 |
| 5 | 10.8% | chart, billboard, debut, sale, ddu, du | 빌보드 차트·데뷔 |
| 6 | 10.8% | lisa, concert, jennie, roseanne, tour | 블랙핑크 멤버·공연 |
| 7 | 10.7% | post, entertainment, agency, statement, weverse | 소속사·공식 입장 |
| 8 | 6.8% | week, share, single, sale, chart, billboard | 음원 판매·차트 |
| 9 | 3.8% | mina, fashion, seungkwan, jeongyeon | 멤버·패션 |

| 그룹 | 1위 | 2위 |
| --- | --- | --- |
| bts | 군 복무 34.7% | 투어·티켓 17.9% |
| 블랙핑크 | 멤버·공연 23.5% | 빌보드 차트 23.4% |
| 세븐틴 | 활동·퍼포먼스 29.3% | 투어·티켓 17.3% |
| 트와이스 | 음원 판매 17.1% | 솔로·공연 17.0% |

## 4. 빈도·TF-IDF·워드클라우드 시각화

- 노트북: [한국자료_시각화.ipynb](visualization/한국자료_시각화.ipynb), [영문자료_시각화.ipynb](visualization/영문자료_시각화.ipynb)
- 그룹·연도별 기사 수, 단어 빈도, 워드클라우드, TF-IDF, 그룹 간 코사인 유사도, 유사 기사, 연도별 키워드 비율을 분석
- 입력은 `data/processed/ko/processed_ko.csv`, `data/processed/en/processed_en.csv`. 작업 폴더를 저장소 루트로 맞추고 데이터 셀의 `pd.read_csv('processed_*.csv')`를 해당 경로로 변경
- Windows/macOS에서는 첫 번째 설치 셀을 건너뛰고 다음 import 셀에 `import os`를 추가. 첫 셀의 `apt-get`은 Linux/Colab용이며 패키지는 루트 requirements로 설치
- 한글 폰트는 별도로 필요함. `font_candidates`에 실제 설치된 폰트 파일 경로가 있어야 하며, 하나도 없으면 `StopIteration` 오류가 발생
- 한국어 노트북의 `google.colab.drive` 셀은 Colab에서 Drive를 사용할 때만 실행
- 시각화 노트북은 전처리 토큰에 추가 불용어 필터를 적용함. 영어 노트북은 베이비몬스터·코르티스 언급 기사도 제외하므로 분석 건수가 입력 800건보다 줄어들 수 있음

대부분의 그래프는 셀 출력으로 표시됩니다. 한국어 노트북의 선택적 마스크 셀은
현재 작업 폴더에 `mask.png`가 있을 때만 `kpop_wordcloud_mask.png`를 저장합니다.

## 수집 윤리

- 수집 코드에서 robots.txt 확인 및 접근 제한 처리
- 수집용 User-Agent 사용, 요청 간격 유지 (한국어 2초 이상, 영어 같은 사이트 3초 이상)
- 한국어 수집 코드에서 개인정보(이메일, 전화번호, 아이디 등) 비식별화
- theguardian.com 제외 (Guardian 개발자 등록 시 "본문을 저장하지 않음"으로 신청했기 때문)
- 기사 본문의 활용 목적은 집계 분석이며, 현재 수록 CSV에는 본문이 포함되어 있음

## 한계

- 영어 크롤링 56% 실패: robots.txt 금지(URL의 약 40%, 주로 K-pop 전문 사이트), 403 차단, 삭제된 기사, 본문 없음
- 영어 출처 편향: 사이트 290개, 상위는 Billboard, Pinkvilla, Times of India. K-pop 전문 사이트가 크롤링을 막아서 기사의 약 20%가 인도 언론사에서 나옴
- BTS의 영어 크롤링 성공률이 가장 낮음 (39%)
- 기사 수가 적은 연도: 영어는 모든 그룹의 2017~2018년, 세븐틴의 2021년 이전과 2026년. 연도별 결과는 신뢰도가 낮다고 표시
- GDELT가 헤드라인의 "BTS"를 "BT"로 기록하는 경우가 있어, 두 그룹을 언급한 헤드라인 일부가 필터를 통과함
- 한국어는 그룹마다 기사 기간이 다름 (BTS·블랙핑크 등 2017년~, 베이비몬스터 2023년~, 코르티스 2025년~)
- 토픽 모델링 결과에 주제와 무관한 기사 유형(브랜드평판 순위, 공항 출국 등)이 토픽으로 나타남. 노이즈 제외 전 한국어 결과에서는 여러 그룹의 평균 비중 1위가 공항 출국 토픽임
- 현재 노트북은 그룹 비교 시 한국어 Topic1·Topic4, 영어 Topic3·Topic4·Topic6을 제외하고 남은 비중을 다시 정규화함. 이 결과에는 제외된 비중이 직접 반영되지 않음
- 영어 토픽은 멤버 이름(jin, lisa, jennie, scoups, mina 등)으로 갈라지는 경우가 많음

## 진행 상황

- [x] 데이터 수집 (한국어, 영어)
- [x] 전처리 (한국어, 영어)
- [x] 한국어 토픽 모델링 (k = 7)과 그룹별 토픽 비중
- [x] 영어 토픽 모델링 (k = 9)과 그룹별 토픽 비중
- [x] 노이즈 토픽 제외 후 공통 카테고리 비교 및 빈도·TF-IDF 시각화
- [ ] 국내·해외 토픽 해석 비교 정리
- [x] 한국어 전처리 노트북 업로드 (`preprocessing/ko/preporcess_ko.ipynb`)

## 논의 필요

- 현재 적용한 노이즈 토픽 제외 기준이 비교 목적에 적절한지
- 그룹 간 기사 기간 차이를 어떻게 맞출지
