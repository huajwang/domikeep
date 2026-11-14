"""Copy the SQLite database and uploaded images to /var/backups/domikeep."""

import os
import sqlite3
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEST = Path("/var/backups/domikeep")
KEEP_DAYS = 14


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    database = Path(os.environ.get("DATABASE_PATH", "/var/lib/domikeep/db.sqlite3"))
    media = Path(os.environ.get("MEDIA_ROOT", "/var/lib/domikeep/media"))
    if database.is_file():
        target = sqlite3.connect(DEST / f"db-{stamp}.sqlite3")
        source = sqlite3.connect(database)
        with target:
            source.backup(target)
        source.close()
        target.close()
    if media.is_dir():
        with tarfile.open(DEST / f"media-{stamp}.tar", "w") as archive:
            archive.add(media, arcname="media")
    cutoff = datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)
    for path in DEST.iterdir():
        modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        if modified < cutoff:
            path.unlink()


if __name__ == "__main__":
    main()
