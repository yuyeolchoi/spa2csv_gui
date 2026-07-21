# SPA to CSV Converter

[English](README.md) | **한국어**

Thermo OMNIC의 `.spa` FT-IR 스펙트럼을 OMNIC 설치 없이 CSV로 일괄 변환하는
Python/tkinter 데스크톱 도구입니다. 각 CSV는 원본과 같은 폴더에 같은 기본 이름으로
생성되며 기존 파일은 덮어씁니다.

## 다운로드 (실행 파일)

Python 설치 없이 바로 쓰려면 [Releases](../../releases) 페이지에서 시스템에 맞는
실행 파일을 내려받아 더블클릭하세요. 두 빌드 모두 Windows 7 이상에서 동작합니다.

- **`SPA_to_CSV_x64.exe`** — 64비트 Windows
- **`SPA_to_CSV_x86.exe`** — 32비트 Windows (64비트에서도 실행됨. 잘 모르겠거나
  구형 기기 제어용 PC라면 이걸 받으세요)

시스템 종류 확인: `설정 → 시스템 → 정보 → 시스템 종류` (또는 `내 PC → 속성`)

> 서명되지 않은 실행 파일이라 첫 실행 시 Windows SmartScreen 경고가 뜰 수 있습니다.
> `추가 정보 → 실행`을 누르면 됩니다.

소스에서 직접 실행하려면 아래를 참고하세요.

## 설치 및 실행

Python 3.11 이상이 필요합니다. tkinter는 일반적인 Windows Python 설치에 포함됩니다.

```powershell
python -m pip install -r requirements.txt
python main.py
```

UI 기본 언어는 **영어**입니다. 상단 메뉴 `Options → Language`에서 English와
한국어를 전환할 수 있으며, 창 제목·버튼·상태 메시지가 즉시 바뀝니다.
`Options → About`에는 버전·제작자·GitHub 링크가 표시됩니다.

`Load Files`로 여러 SPA 파일을 선택하거나 `Load Folder`로 한 폴더의 SPA 파일을
추가한 뒤 `Start`를 누릅니다. 왼쪽에는 원본 파일명, 오른쪽에는 완성된 CSV
파일명 또는 파일별 실패 사유가 표시됩니다. 변환은 스레드 풀에서 여러 파일을
동시에 처리하므로 대량 파일도 빠르게 변환됩니다.

### In-situ 시리즈(`.srs`)

in-situ 시리즈 파일(`.srs`)은 먼저 OMNIC에서 split 하세요(1번 작업). OMNIC이 각
스펙트럼을 `sample0000`, `sample0001` … 처럼 **확장자 없는 SPA 파일**로 한 폴더에
저장합니다. 그 폴더를 `Load Folder`로 불러오면, 이 툴이 확장자 없는 파일들을
인식해 한 번에 전부 변환합니다. (`.srs`를 직접 읽지 않는 이유는, OMNIC이 split할
때 원시 단일빔 데이터를 흡광도로 재처리하기 때문입니다.)

출력 CSV는 OMNIC이 직접 내보내는 CSV와 동일한 형식을 따릅니다: 헤더 행 없이
두 열(파수, 강도)을 콤마로 구분하고, 파수 오름차순으로 정렬하며, 값은 지수 표기
(`6.499040e+002`), 줄바꿈은 CRLF입니다. 기존 OMNIC CSV를 쓰던 분석 스크립트에
그대로 결합(drop-in)할 수 있습니다.

## 단독 실행 파일(.exe) 만들기

cmd 창 없이 더블클릭으로 실행되는 단일 exe를 만들 수 있습니다. `build_exe.bat`을
더블클릭하거나 아래 명령을 실행하세요.

```powershell
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed --name SPA_to_CSV --noconfirm main.py
```

빌드가 끝나면 `dist\SPA_to_CSV.exe`가 생성됩니다. 이 파일만 있으면 Python 설치
없이도 실행되며, `--windowed` 옵션 덕분에 콘솔 창이 뜨지 않습니다. exe를 바탕화면
등으로 복사해 두고 더블클릭하면 됩니다.

## 지원하는 SPA 구조

공개된 OMNIC SPA 리더 구현에서 널리 쓰이는 디렉터리 스캔 방식을 사용합니다.
바이트 294의 uint16 항목 수와 바이트 304부터 시작하는 16바이트 디렉터리를 읽습니다.
각 디렉터리 항목은 `+0`에 key(uint8), `+2`에 블록 위치(uint32), `+6`에 블록
길이(uint32)를 가집니다. **key 2는 헤더 블록**, **key 3은 float32 강도 데이터
블록**입니다. 헤더의 `+4`, `+16`, `+20`에는 각각 포인트 수, 시작 파수, 끝 파수가
little-endian 값으로 저장된다고 가정합니다. 다중 스펙트럼 파일에서는 첫 번째 기본
스펙트럼을 변환합니다.

## 검증 (Validation)

실제 기기에서 측정한 SPA 파일로 OMNIC의 CSV 내보내기 결과와 직접 비교했습니다.

- **분광기**: Thermo Scientific Nicolet iS50 FTIR
- **소프트웨어**: OMNIC 9.8.372
- 측정 스펙트럼 3종(각 6,950 포인트)에 대해, 이 툴의 출력과 OMNIC이 직접
  내보낸 CSV를 비교한 결과:
  - **강도(intensity) 값: 6,950 포인트 전부 완전 일치** (음수 포함)
  - **파수(wavenumber): 6,950개 중 5개만** 6번째 유효숫자에서 0.001 cm⁻¹ 차이
    (분광 분해능보다 수천 배 작은 값으로, OMNIC 내부 단정밀도 x축 재구성에서
    비롯된 것이며 실질적 영향 없음)
  - 행 순서·숫자 표기·줄바꿈까지 OMNIC 형식과 동일

## 테스트

코드로 만든 합성 SPA fixture로 파서·변환기·언어 처리를 검증합니다.

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
