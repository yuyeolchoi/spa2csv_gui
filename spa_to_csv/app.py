"""Tkinter desktop interface and independently testable file-list logic."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, ttk
from typing import Iterable

from .converter import convert_spa_to_csv
from .i18n import DEFAULT_LANG, LANGUAGES, translate


def worker_count(file_count: int) -> int:
    """Pick a thread-pool size for converting ``file_count`` files.

    Conversion is I/O bound (read SPA, write CSV), so a few workers per core
    helps, but never spawn more threads than there are files.
    """

    if file_count <= 1:
        return 1
    cores = os.cpu_count() or 4
    return max(1, min(file_count, cores * 2, 16))


def unique_spa_paths(current: Iterable[str | Path], additions: Iterable[str | Path]) -> list[Path]:
    """Return normalized, de-duplicated SPA paths, preserving input order."""

    result: list[Path] = []
    seen: set[str] = set()
    for raw in [*current, *additions]:
        path = Path(raw).expanduser().resolve()
        key = str(path).casefold()
        if path.suffix.casefold() == ".spa" and key not in seen:
            result.append(path)
            seen.add(key)
    return result


class SpaToCsvApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.minsize(760, 420)
        self.paths: list[Path] = []
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.running = False
        self._done = 0
        self._total = 0
        self._lang = DEFAULT_LANG
        # Remember the current status as a (key, kwargs) pair so it can be
        # re-rendered when the language changes.
        self._status: tuple[str, dict[str, object]] = ("status_ready", {})
        self.status = tk.StringVar()
        self.lang_var = tk.StringVar(value=self._lang)
        self._build()
        self._retranslate()

    def tr(self, key: str, **kwargs: object) -> str:
        return translate(self._lang, key, **kwargs)

    def _set_status(self, key: str, **kwargs: object) -> None:
        self._status = (key, kwargs)
        self.status.set(self.tr(key, **kwargs))

    def _build(self) -> None:
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        self._build_menu()

        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(1, weight=1)

        self.source_label = ttk.Label(frame)
        self.source_label.grid(row=0, column=0, sticky="w")
        self.result_label = ttk.Label(frame)
        self.result_label.grid(row=0, column=2, sticky="w")
        self.sources = self._list_panel(frame, 0)
        self.results = self._list_panel(frame, 2)

        controls = ttk.Frame(frame, padding=(14, 25))
        controls.grid(row=1, column=1, sticky="n")
        self.load_files_btn = ttk.Button(controls, command=self.load_files)
        self.load_files_btn.pack(fill="x", pady=4)
        self.load_folder_btn = ttk.Button(controls, command=self.load_folder)
        self.load_folder_btn.pack(fill="x", pady=4)
        self.start_button = ttk.Button(controls, command=self.start)
        self.start_button.pack(fill="x", pady=(18, 4))

        ttk.Separator(frame).grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 5))
        ttk.Label(frame, textvariable=self.status).grid(row=3, column=0, columnspan=3, sticky="w")

    def _build_menu(self) -> None:
        self.menubar.delete(0, "end")
        options = tk.Menu(self.menubar, tearoff=0)
        language = tk.Menu(options, tearoff=0)
        for label, code in LANGUAGES:
            language.add_radiobutton(
                label=label, value=code, variable=self.lang_var, command=self._on_language
            )
        options.add_cascade(label=self.tr("menu_language"), menu=language)
        self.menubar.add_cascade(label=self.tr("menu_options"), menu=options)

    def _on_language(self) -> None:
        self._lang = self.lang_var.get()
        self._retranslate()

    def _retranslate(self) -> None:
        self.root.title(self.tr("title"))
        self._build_menu()
        self.source_label.config(text=self.tr("source_label"))
        self.result_label.config(text=self.tr("result_label"))
        self.load_files_btn.config(text=self.tr("load_files"))
        self.load_folder_btn.config(text=self.tr("load_folder"))
        self.start_button.config(text=self.tr("start"))
        key, kwargs = self._status
        self.status.set(self.tr(key, **kwargs))

    @staticmethod
    def _list_panel(parent: ttk.Frame, column: int) -> tk.Listbox:
        panel = ttk.Frame(parent)
        panel.grid(row=1, column=column, sticky="nsew")
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)
        box = tk.Listbox(panel)
        scroll = ttk.Scrollbar(panel, orient="vertical", command=box.yview)
        box.configure(yscrollcommand=scroll.set)
        box.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        return box

    def _add(self, additions: Iterable[str | Path]) -> None:
        self.paths = unique_spa_paths(self.paths, additions)
        self.sources.delete(0, tk.END)
        for path in self.paths:
            self.sources.insert(tk.END, path.name)
        self._set_status("status_loaded", n=len(self.paths))

    def load_files(self) -> None:
        selected = filedialog.askopenfilenames(
            title=self.tr("dialog_files_title"),
            filetypes=[(self.tr("filetype_spa"), "*.spa"), (self.tr("filetype_all"), "*.*")],
        )
        self._add(selected)

    def load_folder(self) -> None:
        selected = filedialog.askdirectory(title=self.tr("dialog_folder_title"))
        if selected:
            self._add(sorted(Path(selected).glob("*.[sS][pP][aA]")))

    def start(self) -> None:
        if self.running:
            return
        if not self.paths:
            self._set_status("status_no_files")
            return
        self.running = True
        self._done = 0
        self._total = len(self.paths)
        self.results.delete(0, tk.END)
        self.start_button.configure(state="disabled")
        threading.Thread(target=self._worker, args=(tuple(self.paths),), daemon=True).start()
        self.root.after(50, self._poll)

    def _convert_one(self, path: Path) -> str:
        """Convert one file, returning the display text (never raises)."""

        try:
            return convert_spa_to_csv(path).name
        except Exception as exc:  # one malformed file must not stop the batch
            return f"{self.tr('fail_prefix')} {path.name}: {exc}"

    def _worker(self, paths: tuple[Path, ...]) -> None:
        total = len(paths)
        self.events.put(("total", total))
        # Files convert independently, so run them on a small thread pool.
        with ThreadPoolExecutor(max_workers=worker_count(total)) as pool:
            futures = [pool.submit(self._convert_one, path) for path in paths]
            for future in as_completed(futures):
                self.events.put(("result", future.result()))
        self.events.put(("done", total))

    def _poll(self) -> None:
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "total":
                    self._total = value  # type: ignore[assignment]
                    self._done = 0
                    self._set_status("status_progress", done=0, total=value)
                elif kind == "result":
                    self.results.insert(tk.END, value)
                    self._done += 1
                    self._set_status("status_progress", done=self._done, total=self._total)
                elif kind == "done":
                    self.running = False
                    self.start_button.configure(state="normal")
                    self._set_status("status_done", n=value)
        except queue.Empty:
            pass
        if self.running:
            self.root.after(50, self._poll)


def run() -> None:
    root = tk.Tk()
    SpaToCsvApp(root)
    root.mainloop()
