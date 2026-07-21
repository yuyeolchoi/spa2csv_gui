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
        self.root.title("SPA to CSV Converter")
        self.root.minsize(760, 420)
        self.paths: list[Path] = []
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.running = False
        self._done = 0
        self._total = 0
        self.status = tk.StringVar(value="준비")
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text="SPA 파일 목록").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text="CSV 결과 목록").grid(row=0, column=2, sticky="w")
        self.sources = self._list_panel(frame, 0)
        self.results = self._list_panel(frame, 2)

        controls = ttk.Frame(frame, padding=(14, 25))
        controls.grid(row=1, column=1, sticky="n")
        ttk.Button(controls, text="파일 로드", command=self.load_files).pack(fill="x", pady=4)
        ttk.Button(controls, text="폴더 로드", command=self.load_folder).pack(fill="x", pady=4)
        self.start_button = ttk.Button(controls, text="작업 시작", command=self.start)
        self.start_button.pack(fill="x", pady=(18, 4))

        ttk.Separator(frame).grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 5))
        ttk.Label(frame, textvariable=self.status).grid(row=3, column=0, columnspan=3, sticky="w")

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
        self.status.set(f"{len(self.paths)}개 파일 로드됨")

    def load_files(self) -> None:
        selected = filedialog.askopenfilenames(
            title="SPA 파일 선택", filetypes=[("OMNIC SPA", "*.spa"), ("모든 파일", "*.*")]
        )
        self._add(selected)

    def load_folder(self) -> None:
        selected = filedialog.askdirectory(title="SPA 폴더 선택")
        if selected:
            self._add(sorted(Path(selected).glob("*.[sS][pP][aA]")))

    def start(self) -> None:
        if self.running or not self.paths:
            self.status.set("변환할 SPA 파일을 먼저 로드하세요" if not self.paths else self.status.get())
            return
        self.running = True
        self._done = 0
        self._total = len(self.paths)
        self.results.delete(0, tk.END)
        self.start_button.configure(state="disabled")
        threading.Thread(target=self._worker, args=(tuple(self.paths),), daemon=True).start()
        self.root.after(50, self._poll)

    @staticmethod
    def _convert_one(path: Path) -> str:
        """Convert one file, returning the display text (never raises)."""

        try:
            return convert_spa_to_csv(path).name
        except Exception as exc:  # one malformed file must not stop the batch
            return f"[실패] {path.name}: {exc}"

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
                    self.status.set(f"0/{value} 처리됨")
                elif kind == "result":
                    self.results.insert(tk.END, value)
                    self._done += 1
                    self.status.set(f"{self._done}/{self._total} 처리됨")
                elif kind == "done":
                    self.running = False
                    self.start_button.configure(state="normal")
                    self.status.set(f"완료: {value}개 처리")
        except queue.Empty:
            pass
        if self.running:
            self.root.after(50, self._poll)


def run() -> None:
    root = tk.Tk()
    SpaToCsvApp(root)
    root.mainloop()
