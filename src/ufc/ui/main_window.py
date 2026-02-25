import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import ufc.plugins
from ufc.plugins.registry import PluginRegistry
from ufc.core.engine import CoreEngine
from ufc.i18n.i18n import i18n
from ufc.utils.paths import open_folder


CONFIG_PATH = Path.home() / ".universal_file_converter.json"

@dataclass
class AppConfig:
    lang: str = "en-US"
    last_dir: str = str(Path.home())
    out_dir: str = ""
    in_type: str = ".docx"
    out_type: str = ".txt"

    def save(self) -> None:
        try:
            CONFIG_PATH.write_text(json.dumps(self.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    @staticmethod
    def load() -> "AppConfig":
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return AppConfig(
                lang=data.get("lang", "en-US"),
                last_dir=data.get("last_dir", str(Path.home())),
                out_dir=data.get("out_dir", ""),
                in_type=data.get("in_type", ".docx"),
                out_type=data.get("out_type", ".txt"),
            )
        except Exception:
            return AppConfig()


class MainWindow:
    def __init__(self, root: tk.Tk, cfg: AppConfig):
        self.root = root
        self.cfg = cfg
        
        i18n.set_locale(cfg.lang)

        self.lang = tk.StringVar(value=cfg.lang)
        self.in_type = tk.StringVar(value=cfg.in_type)
        self.out_type = tk.StringVar(value=cfg.out_type)

        self.files: List[str] = []

        self.output_mode = tk.StringVar(value="same")
        self.out_dir = tk.StringVar(value=cfg.out_dir)

        # Options
        self.include_tables = tk.BooleanVar(value=True)
        self.table_format = tk.StringVar(value="tsv")
        self.normalize_tables = tk.BooleanVar(value=True)
        self.include_headers = tk.BooleanVar(value=False)
        self.include_footers = tk.BooleanVar(value=False)
        self.keep_empty = tk.BooleanVar(value=False)
        self.utf8_bom = tk.BooleanVar(value=False)

        # Chunking
        self.enable_chunk = tk.BooleanVar(value=False)
        self.chunk_size = tk.IntVar(value=12000)
        self.overlap = tk.IntVar(value=300)

        self.status = tk.StringVar(value="")
        self.progress = tk.IntVar(value=0)
        self._is_converting = False

        self._build_ui()
        self._apply_i18n()

    def _build_ui(self) -> None:
        self.root.title("Universal File Converter")
        self.root.geometry("850x600")
        self.root.minsize(800, 500)

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        # Top row: combos
        top = ttk.Frame(main)
        top.pack(fill="x", pady=(0, 10))

        # Language
        self.lang_label = ttk.Label(top, text="Language:")
        self.lang_label.pack(side="left")
        self.lang_box = ttk.Combobox(
            top, textvariable=self.lang, values=i18n.get_available_locales(), state="readonly", width=10
        )
        self.lang_box.pack(side="left", padx=(4, 16))
        self.lang_box.bind("<<ComboboxSelected>>", lambda e: self._on_lang_changed())

        # In Type
        self.in_label = ttk.Label(top, text="Input Type:")
        self.in_label.pack(side="left")
        in_exts = PluginRegistry.available_inputs()
        self.in_box = ttk.Combobox(
            top, textvariable=self.in_type, values=in_exts, state="readonly", width=8
        )
        self.in_box.pack(side="left", padx=(4, 16))
        if self.in_type.get() not in in_exts and in_exts:
            self.in_type.set(in_exts[0])
            self.cfg.in_type = in_exts[0]

        # Out Type
        self.out_label = ttk.Label(top, text="Output Type:")
        self.out_label.pack(side="left")
        out_exts = PluginRegistry.available_outputs()
        self.out_box = ttk.Combobox(
            top, textvariable=self.out_type, values=out_exts, state="readonly", width=8
        )
        self.out_box.pack(side="left", padx=4)
        if self.out_type.get() not in out_exts and out_exts:
            self.out_type.set(out_exts[0])
            self.cfg.out_type = out_exts[0]

        # Config bindings to update cfg on change
        self.in_box.bind("<<ComboboxSelected>>", lambda e: self._save_cfg())
        self.out_box.bind("<<ComboboxSelected>>", lambda e: self._save_cfg())

        # Inputs section
        self.inp_frame = ttk.LabelFrame(main, text="Input files")
        self.inp_frame.pack(fill="both", expand=True, pady=5)

        self.files_list = tk.Listbox(self.inp_frame, height=8, selectmode=tk.EXTENDED)
        self.files_list.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        right_btns = ttk.Frame(self.inp_frame)
        right_btns.pack(side="right", fill="y", padx=8, pady=8)

        self.add_btn = ttk.Button(right_btns, text="Add files...", command=self.add_files)
        self.add_btn.pack(fill="x", pady=(0, 6))

        self.remove_btn = ttk.Button(right_btns, text="Remove selected", command=self.remove_selected)
        self.remove_btn.pack(fill="x", pady=6)

        self.clear_btn = ttk.Button(right_btns, text="Clear", command=self.clear_files)
        self.clear_btn.pack(fill="x", pady=6)

        # Output section
        self.out_frame = ttk.LabelFrame(main, text="Output")
        self.out_frame.pack(fill="x", pady=5)

        mode_row = ttk.Frame(self.out_frame)
        mode_row.pack(fill="x", padx=8, pady=(8, 4))

        self.same_radio = ttk.Radiobutton(
            mode_row, variable=self.output_mode, value="same", text="Same folder", command=self._toggle_outdir
        )
        self.same_radio.pack(side="left")

        self.folder_radio = ttk.Radiobutton(
            mode_row, variable=self.output_mode, value="folder", text="Choose a folder", command=self._toggle_outdir
        )
        self.folder_radio.pack(side="left", padx=12)

        dir_row = ttk.Frame(self.out_frame)
        dir_row.pack(fill="x", padx=8, pady=(0, 8))

        self.dir_entry = ttk.Entry(dir_row, textvariable=self.out_dir)
        self.dir_entry.pack(side="left", fill="x", expand=True)

        self.dir_btn = ttk.Button(dir_row, text="Browse folder...", command=self.pick_outdir)
        self.dir_btn.pack(side="left", padx=8)

        # Options pane (Tabbed or grid)
        self.opt_frame = ttk.LabelFrame(main, text="Options")
        self.opt_frame.pack(fill="x", pady=5)

        # Left options
        opt_left = ttk.Frame(self.opt_frame)
        opt_left.grid(row=0, column=0, sticky="nw", padx=8)
        
        self.tbl_chk = ttk.Checkbutton(opt_left, text="Include tables", variable=self.include_tables)
        self.tbl_chk.pack(anchor="w", pady=2)
        
        fmt_frame = ttk.Frame(opt_left)
        fmt_frame.pack(anchor="w", pady=2)
        self.fmt_label = ttk.Label(fmt_frame, text="Table format:")
        self.fmt_label.pack(side="left")
        self.fmt_tsv = ttk.Radiobutton(fmt_frame, text="TSV", value="tsv", variable=self.table_format)
        self.fmt_tsv.pack(side="left", padx=4)
        self.fmt_pipe = ttk.Radiobutton(fmt_frame, text="Pipe", value="pipe", variable=self.table_format)
        self.fmt_pipe.pack(side="left", padx=4)

        self.norm_chk = ttk.Checkbutton(opt_left, text="Normalize irregular tables", variable=self.normalize_tables)
        self.norm_chk.pack(anchor="w", pady=2)

        self.empty_chk = ttk.Checkbutton(opt_left, text="Keep empty paragraphs", variable=self.keep_empty)
        self.empty_chk.pack(anchor="w", pady=2)

        # Right options
        opt_right = ttk.Frame(self.opt_frame)
        opt_right.grid(row=0, column=1, sticky="nw", padx=30)

        self.hdr_chk = ttk.Checkbutton(opt_right, text="Include headers", variable=self.include_headers)
        self.hdr_chk.pack(anchor="w", pady=2)

        self.ftr_chk = ttk.Checkbutton(opt_right, text="Include footers", variable=self.include_footers)
        self.ftr_chk.pack(anchor="w", pady=2)

        self.bom_chk = ttk.Checkbutton(opt_right, text="Write UTF-8 with BOM", variable=self.utf8_bom)
        self.bom_chk.pack(anchor="w", pady=2)

        # Chunking
        chunk_frame = ttk.Frame(opt_right)
        chunk_frame.pack(anchor="w", pady=2)
        self.chunk_chk = ttk.Checkbutton(chunk_frame, text="Enable chunk output", variable=self.enable_chunk, command=self._toggle_chunk_inputs)
        self.chunk_chk.pack(anchor="w")

        chunk_sizes = ttk.Frame(opt_right)
        chunk_sizes.pack(anchor="w", padx=16, pady=2)
        self.chunk_size_label = ttk.Label(chunk_sizes, text="Chunk size:")
        self.chunk_size_label.pack(side="left")
        self.chunk_size_entry = ttk.Entry(chunk_sizes, textvariable=self.chunk_size, width=8)
        self.chunk_size_entry.pack(side="left", padx=4)
        
        self.overlap_label = ttk.Label(chunk_sizes, text="Overlap:")
        self.overlap_label.pack(side="left", padx=(8, 0))
        self.overlap_entry = ttk.Entry(chunk_sizes, textvariable=self.overlap, width=8)
        self.overlap_entry.pack(side="left", padx=4)

        # Logs
        log_frame = ttk.Frame(main)
        log_frame.pack(fill="both", expand=True, pady=5)
        self.log_text = tk.Text(log_frame, height=5, state="disabled")
        self.log_text.pack(fill="both", expand=True)

        # Actions
        actions = ttk.Frame(main)
        actions.pack(fill="x", pady=(5, 0))

        self.convert_btn = ttk.Button(actions, text="Convert", command=self.start_conversion)
        self.convert_btn.pack(side="left")

        self.open_btn = ttk.Button(actions, text="Open output folder", command=self.open_current_output)
        self.open_btn.pack(side="left", padx=10)

        self.pb = ttk.Progressbar(actions, variable=self.progress, maximum=100)
        self.pb.pack(side="right", fill="x", expand=True, padx=(10, 0))

        self.status_label = ttk.Label(main, textvariable=self.status)
        self.status_label.pack(anchor="e")

        self._toggle_outdir()
        self._toggle_chunk_inputs()

    def _on_lang_changed(self) -> None:
        self.cfg.lang = self.lang.get()
        self.cfg.save()
        i18n.set_locale(self.cfg.lang)
        self._apply_i18n()

    def _save_cfg(self) -> None:
        self.cfg.in_type = self.in_type.get()
        self.cfg.out_type = self.out_type.get()
        self.cfg.save()

    def _apply_i18n(self) -> None:
        self.root.title(i18n.t("app_title"))
        self.lang_label.config(text=i18n.t("language"))
        self.in_label.config(text=i18n.t("input_type"))
        self.out_label.config(text=i18n.t("output_type"))

        self.inp_frame.config(text=i18n.t("inputs"))
        self.add_btn.config(text=i18n.t("add_files"))
        self.remove_btn.config(text=i18n.t("remove_selected"))
        self.clear_btn.config(text=i18n.t("clear"))

        self.out_frame.config(text=i18n.t("output"))
        self.same_radio.config(text=i18n.t("same_folder"))
        self.folder_radio.config(text=i18n.t("choose_folder"))
        self.dir_btn.config(text=i18n.t("browse_folder"))

        self.opt_frame.config(text=i18n.t("options"))
        self.tbl_chk.config(text=i18n.t("include_tables"))
        self.fmt_label.config(text=i18n.t("table_format"))
        self.fmt_tsv.config(text=i18n.t("tsv"))
        self.fmt_pipe.config(text=i18n.t("pipe"))
        self.norm_chk.config(text=i18n.t("normalize_tables"))
        self.hdr_chk.config(text=i18n.t("include_headers"))
        self.ftr_chk.config(text=i18n.t("include_footers"))
        self.empty_chk.config(text=i18n.t("keep_empty"))
        self.bom_chk.config(text=i18n.t("utf8_bom"))

        self.chunk_chk.config(text=i18n.t("enable_chunk"))
        self.chunk_size_label.config(text=i18n.t("chunk_size"))
        self.overlap_label.config(text=i18n.t("overlap"))

        self.convert_btn.config(text=i18n.t("convert"))
        self.open_btn.config(text=i18n.t("open_output_folder"))

        if not self._is_converting:
            self.status.set(i18n.t("status_ready"))

    def log(self, text: str) -> None:
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _toggle_outdir(self) -> None:
        is_folder = (self.output_mode.get() == "folder")
        state = "normal" if is_folder else "disabled"
        self.dir_entry.config(state=state)
        self.dir_btn.config(state=state)

    def _toggle_chunk_inputs(self) -> None:
        st = "normal" if self.enable_chunk.get() else "disabled"
        self.chunk_size_entry.config(state=st)
        self.overlap_entry.config(state=st)

    def add_files(self) -> None:
        ext = self.in_type.get()
        paths = filedialog.askopenfilenames(
            title=i18n.t("inputs"),
            initialdir=self.cfg.last_dir,
            filetypes=[(f"{ext} Files", f"*{ext}"), ("All files", "*.*")],
        )
        if not paths:
            return
        self.cfg.last_dir = str(Path(paths[0]).parent)
        self.cfg.save()

        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.files_list.insert(tk.END, p)

    def remove_selected(self) -> None:
        sel = list(self.files_list.curselection())
        sel.reverse()
        for idx in sel:
            try:
                path = self.files_list.get(idx)
                if path in self.files:
                    self.files.remove(path)
                self.files_list.delete(idx)
            except Exception:
                pass

    def clear_files(self) -> None:
        self.files.clear()
        self.files_list.delete(0, tk.END)

    def pick_outdir(self) -> None:
        folder = filedialog.askdirectory(
            title=i18n.t("output"),
            initialdir=self.cfg.out_dir or self.cfg.last_dir,
        )
        if not folder:
            return
        self.out_dir.set(folder)
        self.cfg.out_dir = folder
        self.cfg.save()

    def start_conversion(self) -> None:
        if self._is_converting:
            return
        if not self.files:
            messagebox.showerror(i18n.t("status_error"), i18n.t("err_no_files"))
            return

        outdir_val = self.out_dir.get().strip()
        if self.output_mode.get() == "folder" and not outdir_val:
            messagebox.showerror(i18n.t("status_error"), i18n.t("err_pick_outdir"))
            return

        self._is_converting = True
        self.convert_btn.config(state="disabled")
        self.status.set(i18n.t("status_converting"))
        self.progress.set(0)
        
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")
        self.log(i18n.t("log_start"))

        read_opts = {
            "include_headers": self.include_headers.get(),
            "include_footers": self.include_footers.get(),
            "keep_empty_paragraphs": self.keep_empty.get(),
            "include_tables": self.include_tables.get(),
        }
        write_opts = {
            "include_tables": self.include_tables.get(),
            "table_format": self.table_format.get(),
            "normalize_tables": self.normalize_tables.get(),
            "utf8_bom": self.utf8_bom.get(),
            "enable_chunk": self.enable_chunk.get(),
            "chunk_size": self.chunk_size.get(),
            "overlap": self.overlap.get(),
        }

        # Snapshot parameters for thread
        files = list(self.files)
        output_mode = self.output_mode.get()
        out_ext = self.out_type.get()
        enable_chunk = self.enable_chunk.get()

        def worker():
            total = len(files)
            saved_any = None
            
            chunk_root = None
            if enable_chunk:
                if output_mode == "folder":
                    base_for_all = Path(outdir_val)
                else:
                    base_for_all = Path(files[0]).parent
                
                chunk_root = base_for_all / "ALL_CHUNKS"
                chunk_root.mkdir(parents=True, exist_ok=True)
                saved_any = chunk_root

            for i, f in enumerate(files, 1):
                try:
                    if enable_chunk:
                        # writer will handle part001 internally if given the base file path or target dir
                        # For chunk output logic in txt_writer, it writes to `output_path.parent / {stem}_part001.txt`
                        # So we give it an output path that puts it inside chunk_root.
                        stem = Path(f).stem
                        target = chunk_root / f"{stem}{out_ext}"
                    else:
                        if output_mode == "folder":
                            target = Path(outdir_val) / f"{Path(f).stem}{out_ext}"
                        else:
                            target = Path(f).with_suffix(out_ext)

                    CoreEngine.convert(f, str(target), read_opts, write_opts)
                    
                    if not enable_chunk:
                        saved_any = target.parent

                    self.root.after(0, self.log, i18n.t("log_success").format(file=Path(f).name))
                except Exception as e:
                    self.root.after(0, self.log, i18n.t("log_fail").format(file=Path(f).name, err=str(e)))
                
                # Update progress
                pct = int(i * 100 / total)
                self.root.after(0, self.progress.set, pct)
                self.root.after(0, self.status.set, f"{i}/{total}")

            self.root.after(0, self._finish_conversion, saved_any)

        threading.Thread(target=worker, daemon=True).start()

    def _finish_conversion(self, saved_anywhere: Optional[Path]) -> None:
        self._is_converting = False
        self.convert_btn.config(state="normal")
        self.status.set(i18n.t("status_done"))
        
        if saved_anywhere:
            messagebox.showinfo(i18n.t("status_done"), f"{i18n.t('ok_saved')}\n{saved_anywhere}")

    def open_current_output(self) -> None:
        try:
            if self.output_mode.get() == "folder":
                outdir = self.out_dir.get().strip()
                if outdir:
                    open_folder(outdir)
            else:
                if self.files:
                    open_folder(str(Path(self.files[0]).parent))
        except Exception:
            pass

