# 한국어 전처리본

`processed_ko.csv`: 1,086건, 공통 11개 컬럼 + `tokens`, `text_type=full`.
`tokens`를 읽을 때는 `json.loads`를 사용합니다.

```python
import json
import pandas as pd
df = pd.read_csv('data/processed/ko/processed_ko.csv', encoding='utf-8-sig')  # 저장소 루트 기준
texts = df['tokens'].apply(json.loads).tolist()
```

현재 [Kiwi 노트북](../../../preprocessing/ko/README.md)의 출력에는 추가 정제 컬럼이 있어
수록본과 스키마가 다릅니다. 다시 실행한 결과는 별도 파일로 검토하세요.
설치는 [LDA](../../../topic_modeling/README.md) 또는 [시각화](../../../visualization/README.md)를 참고하며,
이 데이터 폴더의 별도 requirements는 필요 없습니다.
