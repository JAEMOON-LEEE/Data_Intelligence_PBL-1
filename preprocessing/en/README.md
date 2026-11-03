# 영어 전처리 (spaCy)

Python 3.12 가상환경에서 아래 명령을 **저장소 루트** 기준으로 실행합니다.

```bash
python -m pip install -r preprocessing/en/requirements.txt
python -m spacy download en_core_web_sm
```

`config.py`는 `collection/en/`에서 자동으로 찾습니다. 파일을 복사할 필요가 없습니다.

## 수집 중간 데이터 전처리

[영어 수집 순서](../../collection/en/README.md)를 통해 `data/raw/all_raw.csv`를 생성한 후 실행합니다.

```bash
python preprocessing/en/preprocess_en.py
python preprocessing/en/check_data.py
```

`preprocess_en.py [input_csv]`는 입력을 지정할 수 있지만 출력은 항상
현재 작업 폴더 기준 `data/processed/en_processed.csv`입니다.
`check_data.py [raw_csv] [processed_en_csv]`는 두 입력 경로를 지정할 수 있습니다.

중간 데이터는 `language=en`, `source=gdelt_news`, 대문자 영문 그룹명
(`BTS`, `BLACKPINK`, `SEVENTEEN`, `TWICE`)을 사용합니다.
기본 `config.EN_SOURCES=['gdelt_news']`는 다른 출처의 행을 제외합니다.

## 수록 배포 CSV 확인 및 재처리

검사만 할 때는 다음 명령으로 바로 읽을 수 있습니다.

```bash
python preprocessing/en/check_data.py data/raw/en/raw_en.csv data/processed/en/processed_en.csv
```

`data/raw/en/raw_en.csv`는 `source`가 언론사 도메인이고 그룹명이 `bts/블랙핑크/세븐틴/트와이스`라서
기본 전처리 명령에 그대로 넣으면 행이 모두 제거될 수 있습니다.
이 파일을 재처리하려면 아래 코드를 저장소 루트의 Python/Jupyter에서 실행합니다.
실행 환경은 위 requirements와 spaCy 모델이 필요하며, 결과는 원본과 별도 파일에 저장합니다.

```python
from pathlib import Path
import sys
import pandas as pd

sys.path.insert(0, str(Path('preprocessing/en').resolve()))
import preprocess_en as pipeline

df = pd.read_csv('data/raw/en/raw_en.csv', encoding='utf-8-sig')
original_groups = df.set_index('id')['group']
df['group'] = df['group'].replace({
    'bts': 'BTS', '블랙핑크': 'BLACKPINK', '세븐틴': 'SEVENTEEN', '트와이스': 'TWICE'
})
saved_sources = pipeline.config.EN_SOURCES
try:
    pipeline.config.EN_SOURCES = None  # 배포본의 언론사 도메인 값을 허용
    result = pipeline.preprocess(df, pipeline.load_nlp())
finally:
    pipeline.config.EN_SOURCES = saved_sources
result['group'] = result['id'].map(original_groups)
output = Path('work/preprocessing-en/processed_en.csv')
output.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(output, index=False, encoding='utf-8-sig')
```

## 처리 내용

- HTML·URL·숫자·기호 제거 → 소문자 → spaCy 표제어 추출.
- 명사·고유명사·형용사·동사만 유지, spaCy·도메인·그룹명 불용어 제거.
- 2글자 미만 토큰, 토큰 3개 미만 문서, 그룹 내 동일 정제 문서 제거.
- 멤버명 정규화: S.Coups → Scoups, J-Hope → Jhope, BTS의 V → Taehyung,
  SEVENTEEN의 The8 → Minghao, BLACKPINK의 Rose/Rosé → Roseanne.
- 출력은 기존 컬럼 + `clean_text`, 공백으로 연결한 `tokens`, `n_tokens`.

수록 분석 데이터는 [processed_en.csv](../../data/processed/en/processed_en.csv)입니다.
spaCy와 모델 버전이 달라지면 저장된 과거 토큰과 차이가 날 수 있습니다.
