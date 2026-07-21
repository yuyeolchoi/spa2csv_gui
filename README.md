# SPA to CSV Converter

Thermo OMNIC의 `.spa` FT-IR 스펙트럼을 OMNIC 설치 없이 CSV로 일괄 변환하는
Python/tkinter 데스크톱 도구입니다. 각 CSV는 원본과 같은 폴더에 같은 기본 이름으로
생성되며 기존 파일은 덮어씁니다.

## 설치 및 실행

Python 3.11 이상이 필요합니다. tkinter는 일반적인 Windows Python 설치에 포함됩니다.

```powershell
python -m pip install -r requirements.txt
python main.py
```

`파일 로드`로 여러 SPA 파일을 선택하거나 `폴더 로드`로 한 폴더의 SPA 파일을
추가한 뒤 `작업 시작`을 누릅니다. 왼쪽에는 원본 파일명, 오른쪽에는 완성된 CSV
파일명 또는 파일별 실패 사유가 표시됩니다. 변환은 별도 스레드에서 순차 실행됩니다.

CSV는 UTF-8이며 `Wavenumber (cm-1)`, `Intensity` 두 열을 가집니다. 파수 순서는
SPA 헤더에 기록된 시작값에서 끝값까지 그대로 유지합니다.

## 지원하는 SPA 구조

공개된 OMNIC SPA 리더 구현에서 널리 쓰이는 디렉터리 스캔 방식을 사용합니다.
바이트 294의 uint16 항목 수와 바이트 304부터 시작하는 16바이트 디렉터리를 읽습니다.
각 디렉터리 항목은 `+0`에 key(uint8), `+2`에 블록 위치(uint32), `+6`에 블록
길이(uint32)를 가집니다. **key 2는 헤더 블록**, **key 3은 float32 강도 데이터
블록**입니다. 헤더의 `+4`, `+16`, `+20`에는 각각 포인트 수, 시작 파수, 끝 파수가
little-endian 값으로 저장된다고 가정합니다. 다중 스펙트럼 파일에서는 첫 번째 기본
스펙트럼을 변환합니다.

## 테스트

실제 시료 없이 코드로 만든 합성 SPA fixture를 사용합니다.

```powershell
pytest -q
```

## 라이선스

이 프로젝트는 [MIT License](LICENSE)로 배포됩니다.

## 감사의 말 (Acknowledgment)

SPA 바이너리 포맷의 바이트 오프셋 정보는 아래 오픈소스 프로젝트의 포맷 문서에서
파생하여 상호 검증했습니다. 두 프로젝트의 소스 코드는 복사하지 않았습니다.

- [spectrochempy](https://github.com/spectrochempy/spectrochempy) (`read_omnic`, CeCILL-B) — OMNIC SPA 디렉터리/헤더 오프셋 문서
- [ne0dim/spa2csv](https://github.com/ne0dim/spa2csv) (GPL-3.0) — 강도 데이터 블록 식별 확인

SPA binary format offsets were derived from the file-format documentation in
these projects and cross-checked against each other. No source code from either
project was copied.
