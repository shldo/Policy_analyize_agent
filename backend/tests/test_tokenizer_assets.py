from io import BytesIO
from zipfile import ZipFile

import pytest

from app.core.tokenizer_assets import install


def test_wrong_tokenizer_never_creates_target(tmp_path):
    archive = BytesIO()
    with ZipFile(archive, "w") as zipped:
        zipped.writestr("deepseek_v4_tokenizer/tokenizer.json", "invalid tokenizer")
    target = tmp_path / "tokenizer.json"
    with pytest.raises(ValueError, match="checksum"):
        install(target, archive.getvalue())
    assert not target.exists()
