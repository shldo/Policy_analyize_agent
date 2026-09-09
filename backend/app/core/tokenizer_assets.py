"""Explicit, checksum-verified setup of the default DeepSeek V4 tokenizer data.

Run before first use: python -m app.core.tokenizer_assets
No automatic network calls are made by the RAG request path.
"""

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

URL = "https://cdn.deepseek.com/api-docs/deepseek_v4_tokenizer.zip"
SHA256 = "89085f12ef79460ac5f66d1119325ddfc694b4ab209d80bbd81d35f081dc9614"


def install(target: Path, archive: bytes):
    with ZipFile(BytesIO(archive)) as zipped:
        data = zipped.read("deepseek_v4_tokenizer/tokenizer.json")
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("Tokenizer checksum mismatch; refusing installation")
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != SHA256:
            raise ValueError("Existing tokenizer differs; choose a new output path")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as handle:
        handle.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Use a previously downloaded zip offline")
    parser.add_argument(
        "--output", type=Path, default=Path("data/tokenizers/deepseek-v4/tokenizer.json")
    )
    args = parser.parse_args()
    if args.archive:
        data = args.archive.read_bytes()
    else:
        with urlopen(URL, timeout=60) as response:
            data = response.read()
    install(args.output, data)
    print(f"Verified tokenizer: {args.output}")


if __name__ == "__main__":
    main()
