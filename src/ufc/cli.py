import argparse
import sys
from pathlib import Path
from typing import List

import ufc.plugins  # Ensure plugins are registered
from ufc.core.engine import CoreEngine
from ufc.i18n.i18n import i18n


def convert_cmd(args: argparse.Namespace) -> None:
    i18n.set_locale(args.lang)

    out_dir = Path(args.output_dir) if args.output_dir else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    read_opts = {
        "include_headers": args.include_headers,
        "include_footers": args.include_footers,
        "keep_empty_paragraphs": args.keep_empty,
        "include_tables": args.include_tables,
    }
    write_opts = {
        "include_tables": args.include_tables,
        "table_format": args.table_format,
        "normalize_tables": args.normalize_tables,
        "utf8_bom": args.utf8_bom,
        "enable_chunk": args.enable_chunk,
        "chunk_size": args.chunk_size,
        "overlap": args.overlap,
    }

    in_ext = args.in_type if args.in_type.startswith(".") else f".{args.in_type}"
    out_ext = args.out_type if args.out_type.startswith(".") else f".{args.out_type}"

    chunk_root = None
    if args.enable_chunk:
        if out_dir:
            base_for_all = out_dir
        else:
            base_for_all = Path(args.files[0]).parent
        chunk_root = base_for_all / "ALL_CHUNKS"
        chunk_root.mkdir(parents=True, exist_ok=True)

    for f in args.files:
        fpath = Path(f)
        try:
            if args.enable_chunk:
                target = chunk_root / f"{fpath.stem}{out_ext}"
            else:
                if out_dir:
                    target = out_dir / f"{fpath.stem}{out_ext}"
                else:
                    target = fpath.with_suffix(out_ext)

            print(f"{i18n.t('log_start')}: {fpath.name}")
            CoreEngine.convert(str(fpath), str(target), read_opts, write_opts)
            print(i18n.t("log_success").format(file=fpath.name))
        except Exception as e:
            print(i18n.t("log_fail").format(file=fpath.name, err=str(e)), file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Universal File Converter CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_parser = subparsers.add_parser("convert", help="Convert files")
    convert_parser.add_argument("files", nargs="+", help="Input files")
    convert_parser.add_argument("--lang", default="en-US", help="Language for logs")
    convert_parser.add_argument("--in-type", default="docx", help="Input format (e.g. docx)")
    convert_parser.add_argument("--out-type", default="txt", help="Output format (e.g. txt)")
    convert_parser.add_argument("--output-dir", default="", help="Output directory")

    # Options
    convert_parser.add_argument("--no-tables", action="store_false", dest="include_tables")
    convert_parser.add_argument("--table-format", default="tsv", choices=["tsv", "pipe"])
    convert_parser.add_argument("--no-normalize-tables", action="store_false", dest="normalize_tables")
    convert_parser.add_argument("--include-headers", action="store_true")
    convert_parser.add_argument("--include-footers", action="store_true")
    convert_parser.add_argument("--keep-empty", action="store_true")
    convert_parser.add_argument("--utf8-bom", action="store_true")

    # Chunking
    convert_parser.add_argument("--enable-chunk", action="store_true")
    convert_parser.add_argument("--chunk-size", type=int, default=12000)
    convert_parser.add_argument("--overlap", type=int, default=300)

    args = parser.parse_args()

    if args.command == "convert":
        convert_cmd(args)

if __name__ == "__main__":
    main()
