# 빈도·TF-IDF·워드클라우드 시각화

| 노트북 | 입력 | 분석 대상 |
| --- | --- | --- |
| [한국자료_시각화.ipynb](한국자료_시각화.ipynb) | `data/processed/ko/processed_ko.csv` | 6개 그룹, JSON 리스트 tokens |
| [영문자료_시각화.ipynb](영문자료_시각화.ipynb) | `data/processed/en/processed_en.csv` | 4개 그룹, 공백 구분 tokens |

Python 3.12 가상환경에서 저장소 루트 기준으로 실행합니다.

```bash
python -m pip install -r visualization/requirements.txt
python -m jupyterlab
```

## 실행 전 수정

현재 두 노트북의 첫 셀은 Colab/Linux의 `apt-get`으로 나눔고딕을 설치합니다.
**Windows/macOS에서는 첫 셀 전체를 건너뛰고**, 다음 import 셀 앞에 `import os`를 추가하세요.
패키지는 위 requirements로 이미 설치합니다. Linux/Colab에서는 `fonts-nanum`을
OS 패키지 관리자로 설치할 수 있으며, 설치 권한이 없다면 사용 가능한 한글 폰트 경로를 지정합니다.

다음 import 셀의 `font_candidates`에는 나눔고딕, AppleGothic, Windows 맑은 고딕,
Noto Sans CJK 경로가 들어 있습니다. 하나도 없으면 `StopIteration`이 발생하므로
설치된 한글 폰트 파일의 절대 경로를 목록에 추가하세요.

데이터 셀의 `pd.read_csv('processed_ko.csv')` 또는 `pd.read_csv('processed_en.csv')`를
다음처럼 바꿉니다. 저장소 안에서 실행하는 경우 루트 및 `visualization/` 위치에 모두 대응합니다.

```python
from pathlib import Path
REPO = next(p for p in (Path.cwd(), *Path.cwd().parents)
            if (p / 'data/processed').is_dir())
# 한국어 노트북
df = pd.read_csv(REPO / 'data/processed/ko/processed_ko.csv')
# 영어 노트북에서는 위 한 줄 대신:
# df = pd.read_csv(REPO / 'data/processed/en/processed_en.csv')
```

나머지 토큰·날짜 변환은 기존 셀을 그대로 사용합니다. 한국어 노트북의
`from google.colab import drive` 셀은 Drive를 사용할 때만 실행하며 로컬에서는 건너뜁니다.
`google-colab`을 로컬 requirements에 추가할 필요는 없습니다.
Colab 파일 업로드 방식에서는 현재 작업 폴더에 해당 `processed_*.csv`를 올리면 기존 데이터 경로를 사용할 수 있습니다.

## 결과

- 그룹·연도별 기사 수, 상위 단어, 지프의 법칙, 전체·그룹별 워드클라우드.
- 평균 TF-IDF, 멤버명·소속사 제외 비교, Count/TF-IDF 코사인 유사도, 유사 기사, 연도별 키워드 비율.
- 영어는 추가로 베이비몬스터·코르티스 언급 기사를 제외하므로 입력 800건과 분석 건수가 다를 수 있음.

두 노트북은 전처리 토큰에 추가 불용어 필터를 적용합니다. LDA 결과와 같은 토큰 집합이라고 가정하지 마세요.
대부분의 그래프는 노트북 출력으로만 표시됩니다.
한국어의 선택적 `mask.png` 셀만 마스크가 있으면 현재 작업 폴더에
`kpop_wordcloud_mask.png`를 저장하며, 마스크가 없으면 건너뜁니다.
