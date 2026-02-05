from pathlib import Path
import os
import shutil
import threading
import queue
import fnmatch
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
from ttkbootstrap import Style


class DirectoryNavigator:
    def __init__(self):
        # Setup style & root
        self.style = Style(theme='cyborg')
        self.root = self.style.master
        self.root.title("NAVVI - Directory Navigator")
        self.root.geometry("780x540")
        self.root.minsize(700, 420)

        # Worker queue for thread -> GUI messages
        self._queue = queue.Queue()

        self._build_ui()
        self._periodic_check_queue()

    def _build_ui(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Tab 1: Directories (list & stats) ---
        tab_dir = ttk.Frame(nb)
        nb.add(tab_dir, text="Directories")

        top_frame = ttk.Frame(tab_dir)
        top_frame.pack(fill="x", padx=10, pady=(6, 4))

        self.dir_entry = ttk.Entry(top_frame, width=60)
        self.dir_entry.pack(side="left", padx=(0, 6))

        browse_btn = ttk.Button(top_frame, text="Browse...", command=self._browse_directory)
        browse_btn.pack(side="left", padx=(0, 6))

        list_btn = ttk.Button(top_frame, text="List", command=self._list_directory)
        list_btn.pack(side="left")

        # Middle: results + extension counts
        mid_frame = ttk.Frame(tab_dir)
        mid_frame.pack(fill="both", expand=True, padx=10, pady=6)

        # Scrollable text for file list
        files_frame = ttk.LabelFrame(mid_frame, text="Files")
        files_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.files_text = tk.Text(files_frame, wrap="none", height=22)
        self.files_text.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_text.yview)
        vsb.pack(side="right", fill="y")
        self.files_text['yscrollcommand'] = vsb.set

        # Extension counts and summary
        stats_frame = ttk.LabelFrame(mid_frame, text="Summary", width=260)
        stats_frame.pack(side="left", fill="y")

        self.count_label = ttk.Label(stats_frame, text="Number of items: 0", anchor="w")
        self.count_label.pack(fill="x", padx=6, pady=(6, 2))

        self.ext_counts_box = tk.Listbox(stats_frame, height=14)
        self.ext_counts_box.pack(fill="both", expand=True, padx=6, pady=4)

        clear_btn = ttk.Button(stats_frame, text="Clear", command=self._clear_dir_view)
        clear_btn.pack(padx=6, pady=6)

        # --- Tab 2: Move/Copy/Delete/Find ---
        tab_ops = ttk.Frame(nb)
        nb.add(tab_ops, text="Operations")

        ops_top = ttk.Frame(tab_ops)
        ops_top.pack(fill="x", padx=10, pady=6)

        # Source
        ttk.Label(ops_top, text="Source:").grid(row=0, column=0, sticky="w")
        self.src_entry = ttk.Entry(ops_top, width=60)
        self.src_entry.grid(row=0, column=1, padx=(6, 6))
        ttk.Button(ops_top, text="Browse", command=lambda: self._choose_dir(self.src_entry)).grid(row=0, column=2)

        # Destination
        ttk.Label(ops_top, text="Destination:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.dst_entry = ttk.Entry(ops_top, width=60)
        self.dst_entry.grid(row=1, column=1, padx=(6, 6), pady=(6, 0))
        ttk.Button(ops_top, text="Browse", command=lambda: self._choose_dir(self.dst_entry)).grid(row=1, column=2, pady=(6, 0))

        # Patterns, mode and options
        ttk.Label(ops_top, text="Patterns:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.patterns_entry = ttk.Entry(ops_top, width=40)
        self.patterns_entry.grid(row=2, column=1, sticky="w", padx=(6, 0), pady=(6, 0))
        ttk.Label(ops_top, text="(comma-separated, e.g. *.py, *.md). Leave empty to match all").grid(row=2, column=1, sticky="w", padx=(360, 0))

        self.mode_var = tk.StringVar(value="copy")
        ttk.Radiobutton(ops_top, text="Copy", variable=self.mode_var, value="copy").grid(row=3, column=1, sticky="w")
        ttk.Radiobutton(ops_top, text="Move", variable=self.mode_var, value="move").grid(row=3, column=1, sticky="w", padx=(80, 0))

        # Preserve structure and case-insensitive options
        self.preserve_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ops_top, text="Preserve directory structure", variable=self.preserve_var).grid(row=4, column=1, sticky="w", pady=(6, 0))

        self.case_insensitive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(ops_top, text="Case-insensitive match", variable=self.case_insensitive_var).grid(row=5, column=1, sticky="w")

        self.transfer_btn = ttk.Button(ops_top, text="Start", command=self._start_transfer)
        self.transfer_btn.grid(row=6, column=1, pady=(8, 0), sticky="w")

        # Progress and status
        prog_frame = ttk.Frame(tab_ops)
        prog_frame.pack(fill="x", padx=10, pady=6)
        self.progress = ttk.Progressbar(prog_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=4)
        self.status_label = ttk.Label(prog_frame, text="Idle")
        self.status_label.pack(anchor="w", padx=4, pady=(4, 0))

        # Delete section
        del_frame = ttk.LabelFrame(tab_ops, text="Delete (file or directory)")
        del_frame.pack(fill="x", padx=10, pady=6)

        self.del_entry = ttk.Entry(del_frame, width=70)
        self.del_entry.pack(side="left", padx=(6, 4), pady=6)
        ttk.Button(del_frame, text="Browse", command=lambda: self._choose_path(self.del_entry)).pack(side="left", padx=(0, 4))
        ttk.Button(del_frame, text="Delete", command=self._confirm_delete).pack(side="left", padx=(0, 4))

        # Find file section
        find_frame = ttk.LabelFrame(tab_ops, text="Find file by name")
        find_frame.pack(fill="both", expand=True, padx=10, pady=6)

        top_find = ttk.Frame(find_frame)
        top_find.pack(fill="x", padx=6, pady=(6, 4))
        ttk.Label(top_find, text="Filename:").pack(side="left")
        self.find_entry = ttk.Entry(top_find, width=36)
        self.find_entry.pack(side="left", padx=(6, 6))
        ttk.Button(top_find, text="Search root...", command=self._choose_root_for_find).pack(side="left")
        ttk.Button(top_find, text="Find", command=self._start_find).pack(side="left", padx=(6, 0))

        # Results
        self.find_results = tk.Listbox(find_frame)
        self.find_results.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    # ---------- Directory tab helpers ----------
    def _browse_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, path)
            self._list_directory()

    def _list_directory(self):
        path_text = self.dir_entry.get().strip()
        if not path_text:
            messagebox.showinfo("No path", "Please enter or choose a directory to list.")
            return
        p = Path(path_text)
        if not p.exists() or not p.is_dir():
            messagebox.showerror("Not found", f"Directory not found: {p}")
            return

        try:
            entries = list(p.iterdir())
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to list directory: {exc}")
            return

        # Clear previous view
        self.files_text.delete("1.0", tk.END)
        self.ext_counts_box.delete(0, tk.END)

        files = [e.name for e in entries if e.is_file()]
        dirs = [e.name + "/" for e in entries if e.is_dir()]

        # Show directory contents
        for name in sorted(dirs) + sorted(files):
            self.files_text.insert(tk.END, name + "\n")

        # Count and extension stats
        self.count_label.config(text=f"Number of items: {len(entries)}")
        ext_counter = {}
        for fname in files:
            _, ext = os.path.splitext(fname)
            ext = ext.lower() or "<no ext>"
            ext_counter[ext] = ext_counter.get(ext, 0) + 1
        for ext, cnt in sorted(ext_counter.items(), key=lambda t: (-t[1], t[0])):
            self.ext_counts_box.insert(tk.END, f"{ext} : {cnt}")

    def _clear_dir_view(self):
        self.dir_entry.delete(0, tk.END)
        self.files_text.delete("1.0", tk.END)
        self.ext_counts_box.delete(0, tk.END)
        self.count_label.config(text="Number of items: 0")

    # ---------- Operations tab helpers ----------
    def _choose_dir(self, entry_widget):
        path = filedialog.askdirectory()
        if path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, path)

    def _choose_path(self, entry_widget):
        # allow file or directory
        path = filedialog.askopenfilename()
        if not path:
            # fallback to directory
            path = filedialog.askdirectory()
        if path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, path)

    def _confirm_delete(self):
        target = self.del_entry.get().strip()
        if not target:
            messagebox.showinfo("No path", "Enter or choose a file or directory to delete.")
            return
        p = Path(target)
        if not p.exists():
            messagebox.showerror("Not found", f"Target does not exist: {p}")
            return

        if p.is_dir():
            desc = f"Directory and all contents: {p}"
        else:
            desc = f"File: {p}"

        if messagebox.askyesno("Confirm delete", f"Are you sure you want to delete?\n{desc}"): 
            # run in background
            threading.Thread(target=self._delete_worker, args=(p,), daemon=True).start()
            self.status_label.config(text="Deleting...")

    def _delete_worker(self, path: Path):
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            self._queue.put(("info", f"Deleted: {path}"))
        except Exception as exc:
            self._queue.put(("error", f"Failed to delete {path}: {exc}"))
        finally:
            self._queue.put(("done", None))

    def _start_transfer(self):
        src = self.src_entry.get().strip()
        dst = self.dst_entry.get().strip()
        patterns_raw = self.patterns_entry.get().strip()
        mode = self.mode_var.get()
        preserve = self.preserve_var.get()
        case_insensitive = self.case_insensitive_var.get()

        if not src or not dst:
            messagebox.showinfo("Missing paths", "Please set both source and destination directories.")
            return
        src_p = Path(src)
        dst_p = Path(dst)
        if not src_p.exists() or not src_p.is_dir():
            messagebox.showerror("Invalid source", f"Source directory not found: {src_p}")
            return
        try:
            dst_p.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            messagebox.showerror("Destination error", f"Cannot create destination: {exc}")
            return

        # parse patterns
        patterns = [p.strip() for p in patterns_raw.split(",") if p.strip()]

        # disable UI controls while running
        self.transfer_btn.config(state="disabled")
        self.progress.config(mode="indeterminate")
        self.progress.start(10)
        self.status_label.config(text=f"{mode.title()} in progress...")

        threading.Thread(
            target=self._transfer_worker,
            args=(src_p, dst_p, patterns, mode, preserve, case_insensitive),
            daemon=True,
        ).start()

    def _file_matches(self, filename: str, patterns: list, case_insensitive: bool) -> bool:
        if not patterns:
            return True
        if case_insensitive:
            name = filename.lower()
            for pat in patterns:
                if fnmatch.fnmatch(name, pat.lower()):
                    return True
        else:
            for pat in patterns:
                if fnmatch.fnmatch(filename, pat):
                    return True
        return False

    def _transfer_worker(self, src: Path, dst: Path, patterns: list, mode: str, preserve: bool, case_insensitive: bool):
        try:
            matches = []
            for root, _, files in os.walk(src):
                for f in files:
                    if self._file_matches(f, patterns, case_insensitive):
                        matches.append(Path(root) / f)

            total = len(matches)
            if total == 0:
                self._queue.put(("info", "No matching files found."))
                return

            self._queue.put(("progress_start", total))

            processed = 0
            for p in matches:
                try:
                    if preserve:
                        rel = p.relative_to(src)
                        dest_path = dst / rel
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                    else:
                        dest_path = dst / p.name
                    if mode == "copy":
                        shutil.copy2(p, dest_path)
                    else:
                        # move preserves structure by moving the file
                        if preserve:
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(p), str(dest_path))
                        else:
                            shutil.move(str(p), str(dest_path))
                    processed += 1
                    self._queue.put(("progress_update", processed))
                except Exception as exc:
                    self._queue.put(("error", f"Failed to {mode} {p}: {exc}"))

            self._queue.put(("info", f"{mode.title()} complete: {processed}/{total} files"))
        finally:
            self._queue.put(("done_transfer", None))

    # ---------- Find feature ----------
    def _choose_root_for_find(self):
        path = filedialog.askdirectory()
        if path:
            self.find_root = Path(path)
            messagebox.showinfo("Search root set", f"Search root set to: {path}")

    def _start_find(self):
        fname = self.find_entry.get().strip()
        if not fname:
            messagebox.showinfo("No filename", "Please enter a filename to find.")
            return
        root = getattr(self, "find_root", None)
        if not root:
            messagebox.showinfo("No root", "Choose a search root with 'Search root...' first.")
            return
        # clear results
        self.find_results.delete(0, tk.END)
        self.status_label.config(text="Finding...")
        threading.Thread(target=self._find_worker, args=(root, fname), daemon=True).start()

    def _find_worker(self, root: Path, fname: str):
        found = 0
        try:
            for dirpath, _, files in os.walk(root):
                for f in files:
                    if f == fname:
                        found_path = Path(dirpath) / f
                        self._queue.put(("find_result", str(found_path)))
                        found += 1
            if found == 0:
                self._queue.put(("info", "No files found."))
            else:
                self._queue.put(("info", f"Found {found} result(s)."))
        except Exception as exc:
            self._queue.put(("error", f"Error searching: {exc}"))
        finally:
            self._queue.put(("done", None))

    # ---------- Queue processing ----------
    def _periodic_check_queue(self):
        try:
            while True:
                item = self._queue.get_nowait()
                kind, data = item
                if kind == "info":
                    self.status_label.config(text=data)
                    messagebox.showinfo("Info", data)
                elif kind == "error":
                    self.status_label.config(text="Error")
                    messagebox.showerror("Error", data)
                elif kind == "progress_start":
                    total = data or 0
                    self.progress.stop()
                    self.progress.config(mode="determinate", maximum=total, value=0)
                elif kind == "progress_update":
                    self.progress.config(value=data)
                    self.status_label.config(text=f"Progress: {int(self.progress['value'])}/{int(self.progress['maximum'])}")
                elif kind == "done_transfer":
                    self.transfer_btn.config(state="normal")
                    self.progress.config(mode="determinate", value=self.progress['maximum'])
                    self.status_label.config(text="Transfer finished")
                elif kind == "done":
                    self.progress.config(mode="determinate", value=0)
                elif kind == "find_result":
                    self.find_results.insert(tk.END, data)
                else:
                    self.status_label.config(text=str(data or ""))
        except queue.Empty:
            pass
        # call again after 200ms
        self.root.after(200, self._periodic_check_queue)


def main():
    app = DirectoryNavigator()
    app.root.mainloop()


if __name__ == "__main__":
    main()
