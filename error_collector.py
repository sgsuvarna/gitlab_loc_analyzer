from collections import defaultdict
from datetime import datetime

class ErrorCollector:
    def __init__(self):
        self.errors = defaultdict(list)

    def add(self, project, message, context=None):
        self.errors[project].append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "context": context or {}
        })

    def has_errors(self):
        return bool(self.errors)
