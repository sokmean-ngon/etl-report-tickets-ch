import json
import os

from config import STATE_FILE


class State:

    def __init__(self):

        self.data = {}

        if not os.path.exists(STATE_FILE):
            return

        try:

            with open(
                STATE_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                content = f.read().strip()

                if content:
                    self.data = json.loads(content)

        except (
            OSError,
            json.JSONDecodeError,
        ):
            self.data = {}

    def save_checkpoint(
        self,
        table: str,
        last_date: int,
        last_id: int,
    ) -> None:
        self.data[table] = {
            "last_date": int(last_date),
            "last_id": int(last_id),
        }

        self._save()

    def get_checkpoint(
        self,
        table: str,
    ) -> tuple[int, int]:
        value = self.data.get(table)

        if isinstance(value, int):
            return 0, value

        if not isinstance(value, dict):
            return 0, 0

        try:
            return (
                int(value.get("last_date", 0)),
                int(value.get("last_id", 0)),
            )
        except (TypeError, ValueError):
            return 0, 0

    def reset_checkpoint(self, table: str) -> None:
        self.data.pop(table, None)
        self._save()

    def _save(self) -> None:
        directory = os.path.dirname(STATE_FILE)
        if directory:
            os.makedirs(directory, exist_ok=True)

        tmp = f"{STATE_FILE}.tmp"

        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(
                self.data,
                f,
                indent=4,
                ensure_ascii=False,
                sort_keys=True,
            )
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp, STATE_FILE)