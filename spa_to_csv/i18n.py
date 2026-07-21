"""UI string tables and translation lookup.

English is the default language; Korean is available from the Language menu.
Add a language by extending ``STRINGS`` and ``LANGUAGES``.
"""

from __future__ import annotations

DEFAULT_LANG = "en"

# (menu label, language code) in display order. Menu labels use each
# language's native name and are intentionally not themselves translated.
LANGUAGES: list[tuple[str, str]] = [
    ("English", "en"),
    ("한국어", "ko"),
]

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "title": "SPA to CSV Converter",
        "source_label": "SPA Files",
        "result_label": "CSV Results",
        "load_files": "Load Files",
        "load_folder": "Load Folder",
        "start": "Start",
        "menu_options": "Options",
        "menu_language": "Language",
        "menu_about": "About",
        "about_title": "About",
        "about_version": "Version {version}",
        "about_made_by": "Made by {author}",
        "about_close": "Close",
        "status_ready": "Ready",
        "status_loaded": "{n} file(s) loaded",
        "status_no_files": "Load SPA files first",
        "status_progress": "{done}/{total} processed",
        "status_done": "Done: {n} processed",
        "dialog_files_title": "Select SPA files",
        "dialog_folder_title": "Select SPA folder",
        "filetype_spa": "OMNIC SPA",
        "filetype_all": "All files",
        "fail_prefix": "[FAILED]",
    },
    "ko": {
        "title": "SPA to CSV 변환기",
        "source_label": "SPA 파일 목록",
        "result_label": "CSV 결과 목록",
        "load_files": "파일 로드",
        "load_folder": "폴더 로드",
        "start": "작업 시작",
        "menu_options": "옵션",
        "menu_language": "언어",
        "menu_about": "정보",
        "about_title": "정보",
        "about_version": "버전 {version}",
        "about_made_by": "제작: {author}",
        "about_close": "닫기",
        "status_ready": "준비",
        "status_loaded": "{n}개 파일 로드됨",
        "status_no_files": "변환할 SPA 파일을 먼저 로드하세요",
        "status_progress": "{done}/{total} 처리됨",
        "status_done": "완료: {n}개 처리",
        "dialog_files_title": "SPA 파일 선택",
        "dialog_folder_title": "SPA 폴더 선택",
        "filetype_spa": "OMNIC SPA",
        "filetype_all": "모든 파일",
        "fail_prefix": "[실패]",
    },
}


def translate(lang: str, key: str, **kwargs: object) -> str:
    """Return the localized string for ``key``, falling back to English.

    Missing languages or keys degrade to the English table so the UI never
    shows a raw key.
    """

    table = STRINGS.get(lang, STRINGS[DEFAULT_LANG])
    text = table.get(key) or STRINGS[DEFAULT_LANG].get(key, key)
    return text.format(**kwargs) if kwargs else text
