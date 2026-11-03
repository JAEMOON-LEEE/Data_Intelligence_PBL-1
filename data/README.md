# 데이터 파일과 형식

이 폴더는 수록 CSV와 데이터 설명을 보관합니다. 자체 실행 코드는 없어 별도 requirements는 필요 없습니다.
수집·전처리·분석 환경은 각 코드 폴더의 requirements를 사용합니다.

| 파일 | 행 수 | 그룹별 건수 | `text_type` |
| --- | --- | --- | --- |
| [raw/ko/raw_ko.csv](raw/ko/raw_ko.csv) | 1,200 | 6개 그룹 각 200 | `news` |
| [processed/ko/processed_ko.csv](processed/ko/processed_ko.csv) | 1,086 | bts 199, 블랙핑크 196, 세븐틴 198, 트와이스 197, 베이비몬스터 153, 코르티스 143 | `full` |
| [raw/en/raw_en.csv](raw/en/raw_en.csv) | 800 | bts·블랙핑크·세븐틴·트와이스 각 200 | `news` |
| [processed/en/processed_en.csv](processed/en/processed_en.csv) | 800 | 위 4개 그룹 각 200 | `news` |

위 건수는 현재 저장소의 CSV를 직접 확인한 값입니다. 수집 스크립트의 목표 건수와 구분하세요.
한국어 원본과 전처리본은 `text_type`도 다르며, 현재 전처리 노트북은 이 값을 바꾸지 않습니다.
따라서 현재 원본을 다시 처리하면 수록 전처리본과 완전히 같다고 보장할 수 없습니다.

## 컬럼

공통 11개: `id, group, language, source, source_url, query, title, text,
text_type, published_at, collected_at`.

| 컬럼 | 의미 |
| --- | --- |
| `id` / `group` / `language` | 문서 ID, 분석 그룹, 언어 |
| `source` / `source_url` / `query` | 매체 또는 출처, 원문 URL, 검색어 |
| `title` / `text` / `text_type` | 기사 제목, 본문, 자료 유형 |
| `published_at` / `collected_at` | 게시 시각, 수집 시각 |

한국어 전처리본은 `tokens`만 추가되며 JSON 리스트 문자열입니다(`json.loads`).
영어 전처리본은 `clean_text`, `tokens`(공백 구분 문자열, `.split()`), `n_tokens`가 추가됩니다.
CSV는 `encoding='utf-8-sig'`로 읽을 수 있습니다. 줄바꿈이 들어 있는 기사도 있으므로
텍스트 줄 수가 아니라 CSV 파서로 행 수를 계산하세요.

## 단계별 안내

- [원본](raw/README.md) · [전처리본](processed/README.md) · [데이터 카드](data_cards/README.md)
- [수집](../collection/README.md) · [전처리](../preprocessing/README.md) · [LDA](../topic_modeling/README.md) · [시각화](../visualization/README.md)

영어 재수집 과정의 `data/raw/*.csv`, `data/processed/*.csv`는 중간 파일입니다.
수록 `raw/en/`, `processed/en/`와 경로 및 스키마가 다르므로 혼용하지 마세요.
