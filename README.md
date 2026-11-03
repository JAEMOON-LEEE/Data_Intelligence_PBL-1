# K-POP 국내 vs 해외 언론 보도 분석

데이터인텔리전스 PBL 모듈 #1 팀 프로젝트입니다.
한국어 뉴스와 해외 영어 뉴스 기사를 수집·전처리하고, LDA 토픽 모델링으로 국내와 해외 언론이 각 그룹을 어떤 주제로 다루는지 비교합니다.

## 실행 환경과 빠른 시작

로컬 기준 환경은 **Python 3.12 (64비트)** 입니다. 아래 명령은 별도 안내가 없으면
저장소 최상위 폴더에서 실행합니다. `.python-version`은 버전 선택용이며 Python을 설치하지는 않습니다.

Python 3.12가 설치된 상태에서 운영체제에 맞는 명령으로 가상환경을 만들고 활성화합니다.

```powershell
# Windows PowerShell
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

PowerShell에서 활성화가 차단되면 정책 변경 없이 `.\.venv\Scripts\python.exe`를
위 명령의 `python` 대신 사용할 수 있습니다. Jupyter에서는 이 가상환경의 Python 커널을 선택합니다.
spaCy 모델 다운로드는 영어 전처리에만 필요합니다.

전체 설치 대신 필요한 단계의 환경만 설치할 수 있습니다.

| 작업 | 저장소 루트에서 설치 | 실행 안내 |
| --- | --- | --- |
| 한국어 수집 | `python -m pip install -r collection/ko/requirements.txt` | [한국어 수집](collection/ko/README.md) |
| 영어 수집 | `python -m pip install -r collection/en/requirements.txt` | [영어 수집](collection/en/README.md) |
| 한국어 전처리 | `python -m pip install -r preprocessing/ko/requirements.txt` | [Kiwi 노트북](preprocessing/ko/README.md) |
| 영어 전처리 | `python -m pip install -r preprocessing/en/requirements.txt` | [spaCy 스크립트](preprocessing/en/README.md) |
| LDA 분석 | `python -m pip install -r topic_modeling/requirements.txt` | [토픽 모델링](topic_modeling/README.md) |
| 빈도·TF-IDF·워드클라우드 | `python -m pip install -r visualization/requirements.txt` | [시각화](visualization/README.md) |

이미 수록된 CSV로 분석할 때는 수집·전처리를 다시 실행할 필요가 없습니다.
루트의 두 `Topic_Modeling_*.ipynb`는 상대 경로가 맞춰져 있습니다.
한국어 전처리와 시각화 노트북은 개인 PC 경로 또는 Colab 설정이 남아 있으므로 각 README의
**실행 전 수정**을 먼저 적용하세요. 한글 폰트는 pip 패키지와 별도로 필요합니다.

requirements는 호환 범위를 지정한 실행 환경이며 과거 실험의 잠금 파일이 아닙니다.
라이브러리·언어 모델 버전과 수집 시점이 달라지면 토큰·토픽·수치도 달라질 수 있습니다.
공유할 실험은 `python -m pip freeze > requirements-lock.txt`로 실제 설치 버전도 기록하세요.

## 분석 대상 및 범위

| 항목 | 기준 |
| --- | --- |
| 분석 그룹 | 방탄소년단, 블랙핑크, 세븐틴, 트와이스, 베이비몬스터, 코르티스 |
| 언어 | 한국어(`ko`), 영어(`en`) |
| 자료 유형 | 뉴스 기사 (유튜브 댓글은 팀 결정으로 제외) |
| 수집 기간 | 2017년 1월 ~ 2026년 10월 |
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
│   └── data_cards/       # 데이터 카드
├── preprocessing/        # 전처리 코드
│   ├── ko/
│   └── en/
├── topic_modeling/       # 토픽 모델링 설명·실행 환경
├── visualization/        # 한국어·영어 빈도/TF-IDF/워드클라우드 노트북
├── k초기값 시각자료/        # k 선정용 그래프·pyLDAvis 캡처
├── Topic_Modeling_ko.ipynb  # 한국어 토픽 모델링 노트북
└── Topic_Modeling_en.ipynb  # 영어 토픽 모델링 노트북
```

세부 내용은 각 폴더의 README에 있습니다.

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
| `text_type` | 한국어 원본 `news`, 한국어 전처리본 `full`, 영어 `news` (파일별 차이는 data/README.md 참고) |
| `published_at` | 기사 작성일 |
| `collected_at` | 데이터 수집일 |

전처리 데이터에는 아래 컬럼이 추가됩니다.

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

## 1. 데이터 수집 (`collection/`)

### 한국어 (`collection/ko/crawling_ko.py`)

- 출처: 뉴스엔(newsen.com) 기사 제목 검색
- 그룹당 200건, 확인된 후보 기사에서 연도별로 균등 배분
- 그룹명(한글·영문)이 제목 또는 본문에 있는 기사만 사용

### 영어 (`collection/en/`)

- GDELT DOC 2.0(전 세계 영어 뉴스 색인)으로 헤드라인을 찾고, trafilatura로 언론사 페이지에서 본문 추출
- 한국 언론사와 그 영어판은 제외 → 해외 보도만 포함 (GDELT 색인이 2017년부터 시작, 시간은 UTC)
- 실행 순서

| 단계 | 스크립트 | 내용 |
| --- | --- | --- |
| 1 | `collect_news_en_trial.py` | 헤드라인 수집, 그룹당 최대 1,000개, 연도별 균등 |
| 2 | `collect_fulltext_en.py` | 헤드라인 URL을 방문해 본문 크롤링 |
| 3 | `clean_fulltext_en.py` | 광고·리다이렉트·중복 페이지, 그룹 이름이 없는 본문 제거 |
| 4 | `merge.py` → `preprocess_en.py` → `check_data.py` | 병합, 전처리, 확인 |
| 5 | `make_subset_en.py` | 그룹당 200개, 연도별 균등 추출 (시드 42) |

- 설정 파일(`config.py`, `common.py`)은 `collection/en/`에 있으며 전처리 스크립트가 자동으로 찾습니다. 저장소 루트에서 파일 경로를 지정해 실행합니다.
- 수집과 전처리의 설치 파일은 분리되어 있습니다. [영어 수집 README](collection/en/README.md)에 실제 실행 순서와 중간 파일 경로를 정리했습니다. GDELT 경로에는 API 키가 필요 없습니다.

수집 결과 (2026-10-13)

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

자세한 내용은 `collection/en/README.md` 참고.

## 2. 전처리 (`preprocessing/`)

### 공통

- 중복 데이터와 빈 본문 제거
- HTML 태그, URL, 광고 문구 등 불필요한 내용 제거
- 연속된 공백과 줄바꿈 정리

### 한국어

- 노트북: [preporcess_ko.ipynb](preprocessing/ko/preporcess_ko.ipynb) (현재 저장소 파일명)
- Kiwi 형태소 분석, 일반명사·고유명사 및 지정한 외국어 변환, 기본·뉴스·그룹명 불용어 제거
- 그룹·멤버·소속사 등 표기 정규화, 서로 다른 문서 3개 이상에 등장한 단어만 유지
- 개인 PC의 절대 경로를 입력·출력 경로로 사용하므로 [실행 안내](preprocessing/ko/README.md)를 먼저 확인

### 영어 (`preprocessing/en/preprocess_en.py`)

1. 정제: HTML 엔티티·태그, URL, @멘션, `#`, 이모지, 숫자 제거
2. 소문자 변환, spaCy 표제어 추출
3. 명사·고유명사·형용사·동사만 사용
4. 불용어 제거: spaCy 기본 + 도메인 불용어(song, video, music, member, girl, band 등) + 그룹명
5. 2글자 미만 토큰 제거, 토큰 3개 미만 문서 제거, 그룹 안에서 중복 문서 제거
6. 헤드라인 끝의 언론사 이름 제거

- 멤버 이름은 분석 결과로 보고 **일부러 남김**. 정제 과정에서 깨지는 이름은 미리 통일: S.Coups → Scoups, J-Hope → Jhope, V → Taehyung (BTS 기사만), The8 → Minghao, Rose/Rosé → Roseanne
- `check_data.py`: 그룹·연도별 개수, 본문 길이, 그룹별 상위 단어 확인

## 3. 토픽 모델링

- 노트북: `Topic_Modeling_ko.ipynb`, `Topic_Modeling_en.ipynb` (레포 최상위)
- 라이브러리: Gensim (`LdaModel`, `CoherenceModel`), pyLDAvis
- 수업 실습 7-2 노트북의 셀 순서를 따름
- 언어별로 모델을 따로 학습 (한국어 k=7, 영어 k=9)
- LDA 노트북은 전처리 토큰을 사용하고, 시각화 노트북은 추가 불용어 필터를 적용함
- 아래 결과 표는 전체 토픽의 초기 해석이며, `topic_modeling/README.md`는 노이즈 토픽을 제외하고 다시 정규화한 비교 결과를 담음

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
| 9–17 | 그룹별 토픽 평균, 노이즈 제외·재정규화, 기간 확인, 그래프·공통 카테고리·대표 문서 |

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
  - `log_perplexity`는 k가 커질수록 감소 (−7.756 → −8.336). 로그 값의 감소 자체를 성능 개선으로 해석하지 않음
  - 그룹 비교에 쓰도록 최종 모델은 k=9
  - 그래프: `coherence_en.png`, `perplexity_en.png`. `k7_pyLDAvis_en.png`는 비교용 k=7 화면 (원 7개)

### 한국어 결과 (k = 7)

토픽 번호와 비중은 pyLDAvis 화면 기준이다. 노트북의 `Topic1`~`Topic7`은 gensim 토픽 번호(0부터)라 아래 번호와 순서가 다르다.

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

번호와 비중은 pyLDAvis 기준이다.

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

## 수집 윤리

- 모든 사이트의 robots.txt 확인, 크롤링을 금지하거나 robots.txt를 읽을 수 없는 사이트는 제외
- 수업 프로젝트임을 밝히는 User-Agent 사용, 요청 간격 유지 (한국어 2초 이상, 영어 같은 사이트 3초 이상)
- 개인정보(이메일, 전화번호, 아이디 등) 비식별화
- theguardian.com 제외 (Guardian 개발자 등록 시 "본문을 저장하지 않음"으로 신청했기 때문)
- 본문은 집계 분석에만 사용하고 재배포하지 않음

## 한계

- 영어 크롤링 56% 실패: robots.txt 금지(URL의 약 40%, 주로 K-pop 전문 사이트), 403 차단, 삭제된 기사, 본문 없음
- 영어 출처 편향: 사이트 290개, 상위는 Billboard, Pinkvilla, Times of India. K-pop 전문 사이트가 크롤링을 막아서 기사의 약 20%가 인도 언론사에서 나옴
- BTS의 영어 크롤링 성공률이 가장 낮음 (39%)
- 기사 수가 적은 연도: 영어는 모든 그룹의 2017~2018년, 세븐틴의 2021년 이전과 2026년. 연도별 결과는 신뢰도가 낮다고 표시
- GDELT가 헤드라인의 "BTS"를 "BT"로 기록하는 경우가 있어, 두 그룹을 언급한 헤드라인 일부가 필터를 통과함
- 한국어는 그룹마다 기사 기간이 다름 (BTS·블랙핑크 등 2017년~, 베이비몬스터 2023년~, 코르티스 2025년~)
- 토픽 모델링 결과에 주제와 무관한 기사 유형(브랜드평판 순위, 공항 출국 등)이 토픽으로 나타남. 한국어에서는 여러 그룹의 평균 비중 1위가 공항 출국 토픽임
- 영어 토픽은 멤버 이름(jin, lisa, jennie, scoups, mina 등)으로 갈라지는 경우가 많음

## 진행 상황

- [x] 데이터 수집 (한국어, 영어)
- [x] 전처리 (한국어, 영어)
- [x] 한국어 토픽 모델링 (k = 7)과 그룹별 토픽 비중
- [x] 영어 토픽 모델링 (k = 9)과 그룹별 토픽 비중
- [ ] 국내·해외 토픽 해석 비교 정리
- [x] 한국어 전처리 노트북 업로드 (`preprocessing/ko/preporcess_ko.ipynb`)

## 논의 필요

- 주제와 무관한 기사(브랜드평판, 공항 출국 등)를 걸러낼지
- 그룹 간 기사 기간 차이를 어떻게 맞출지
