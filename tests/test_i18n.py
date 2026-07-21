from spa_to_csv.i18n import DEFAULT_LANG, LANGUAGES, STRINGS, translate


def test_default_language_is_english() -> None:
    assert DEFAULT_LANG == "en"


def test_all_languages_define_the_same_keys() -> None:
    en_keys = set(STRINGS["en"])
    for _label, code in LANGUAGES:
        assert set(STRINGS[code]) == en_keys, f"{code} keys differ from en"


def test_translate_formats_placeholders() -> None:
    assert translate("en", "status_progress", done=3, total=10) == "3/10 processed"
    assert translate("ko", "status_done", n=5) == "완료: 5개 처리"


def test_translate_falls_back_to_english_for_unknown_language() -> None:
    assert translate("fr", "start") == STRINGS["en"]["start"]


def test_translate_returns_key_for_unknown_key() -> None:
    assert translate("en", "no_such_key") == "no_such_key"
