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

        except Exception:

            self.data = {}

    def get_last_id(self, table):

        return self.data.get(table, 0)

    def save_last_id(self, table, value):

        self.data[table] = int(value)

        with open(STATE_FILE, "w") as f:

            json.dump(self.data, f, indent=4)
