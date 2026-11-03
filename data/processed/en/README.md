# 영어 전처리본

`processed_en.csv`: 800건, 공통 11개 컬럼 + `clean_text`, `tokens`, `n_tokens`.
그룹당 200건이며 `tokens`는 공백 구분 문자열입니다.

```python
import pandas as pd
df = pd.read_csv('data/processed/en/processed_en.csv', encoding='utf-8-sig')  # 저장소 루트 기준
texts = df['tokens'].fillna('').str.split().tolist()
```

[영어 전처리](../../../preprocessing/en/README.md)의 기본 출력
`data/processed/en_processed.csv`는 표본 추출 전 중간 파일입니다.
설치는 [LDA](../../../topic_modeling/README.md) 또는 [시각화](../../../visualization/README.md)를 참고하며,
이 데이터 폴더의 별도 requirements는 필요 없습니다.
