# 데이터 전처리

| 언어 | 실행 파일 | 실제 처리 | 실행 안내 |
| --- | --- | --- | --- |
| 한국어 | `ko/preporcess_ko.ipynb` | Kiwi 명사 추출, 표기 정규화, 불용어·문서 빈도 필터 | [README](ko/README.md) |
| 영어 | `en/preprocess_en.py` | spaCy 표제어·품사 필터, 불용어·짧은 문서·중복 필터 | [README](en/README.md) |

Python 3.12 가상환경에서 저장소 루트 기준으로 두 언어 환경을 설치합니다.

```bash
python -m pip install -r preprocessing/requirements.txt
python -m spacy download en_core_web_sm
```

한 언어만 필요하면 해당 하위 폴더의 `requirements.txt`를 설치합니다.
한국어 노트북에는 개인 PC 입력·출력 경로가, 영어 스크립트에는 수집 중간 형식용 필터가 있습니다.
각 README에서 입력 경로와 형식을 확인한 후 실행하세요.
최종 분석은 [data/processed](../data/processed/README.md)의 수록 CSV를 바로 사용할 수도 있습니다.
