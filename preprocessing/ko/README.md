# 한국어 전처리 (Kiwi)

실제 파일명은 [`preporcess_ko.ipynb`](preporcess_ko.ipynb)입니다.
Python 3.12를 사용하며 Java/KoNLPy는 필요하지 않습니다.

```bash
# 저장소 루트에서
python -m pip install -r preprocessing/ko/requirements.txt
python -m jupyterlab preprocessing/ko/preporcess_ko.ipynb
```

## 실행 전 수정

현재 노트북의 첫 셀 `csv_path`와 마지막 셀 `output_path`에는 작성자의 Windows 바탕화면 절대 경로가
들어 있습니다. 아래처럼 바꾼 뒤 위에서 아래로 실행합니다. `Path.cwd()`가 저장소 루트 또는
`preprocessing/ko/`일 때 모두 동작하며, 다른 위치라면 `REPO`에 저장소 절대 경로를 지정합니다.

첫 셀의 `csv_path` 대입을 다음으로 바꿉니다(`Path`는 기존 셀에서 import함).

```python
REPO = next(p for p in (Path.cwd(), *Path.cwd().parents)
            if (p / 'data/raw/ko/raw_ko.csv').is_file())
csv_path = REPO / 'data/raw/ko/raw_ko.csv'
```

마지막 셀의 `output_path` 대입을 다음으로 바꿉니다. 재실행 결과는 검토용 새 파일로 저장합니다.

```python
output_path = REPO / 'work/preprocessing-ko/processed_ko.csv'
output_path.parent.mkdir(parents=True, exist_ok=True)
```

## 처리 순서와 출력

1. HTML·URL·기자 표시 정리, 본문 및 정제 본문 중복 제거.
2. 그룹·멤버·팬덤·소속사·앨범·곡명 표기 통일.
3. Kiwi 사용자 사전 등록 및 형태소 분석.
4. Kiwi 기본·뉴스·그룹명 불용어 제거.
5. 일반명사(`NNG`)·고유명사(`NNP`)와 지정한 외국어(`SL`)만 선택.
6. 서로 다른 문서 3개 이상에 등장한 단어만 유지하고 빈 토큰 문서 제거.

출력 `tokens`는 JSON 리스트 문자열입니다. `json.loads`로 읽습니다.
현재 노트북은 `clean_text`, `normalized_text`, `group_normalized`, `processed_text`,
`token_count` 등도 저장하지만, 수록 `data/processed/ko/processed_ko.csv`는
공통 11개 컬럼과 `tokens`만 가진 이전 결과입니다.
현재 원본은 1,200건, 수록 전처리본은 1,086건이며 원본의 `text_type=news`와
전처리본의 `full`도 다릅니다. 이 노트북은 `text_type`을 바꾸지 않으므로
수록본과 동일한 이력을 재현한다고 볼 수 없습니다. 새 결과의 건수·스키마를 확인한 후 사용하세요.
