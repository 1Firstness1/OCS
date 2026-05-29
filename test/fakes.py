import uuid


class FakeScalars:
    def __init__(self, items):
        self._items = list(items or [])

    def all(self):
        return list(self._items)


class FakeResult:
    def __init__(self, scalar=None, all_rows=None, scalars=None):
        self._scalar = scalar
        self._all_rows = list(all_rows or [])
        self._scalars = list(scalars or [])

    def scalar_one_or_none(self):
        return self._scalar

    def scalar_one(self):
        return self._scalar

    def scalar(self):
        return self._scalar

    def scalars(self):
        return FakeScalars(self._scalars)

    def all(self):
        return list(self._all_rows)

    def first(self):
        return self._all_rows[0] if self._all_rows else None


class FakeAsyncSession:
    def __init__(self, results=None, strict=True):
        self._results = list(results or [])
        self._strict = strict
        self.added = []
        self.deleted = []

    async def execute(self, *args, **kwargs):
        if not self._results:
            if self._strict:
                raise AssertionError("No fake results left for execute")
            return FakeResult()
        return self._results.pop(0)

    def add(self, obj):
        self.added.append(obj)

    async def delete(self, obj):
        self.deleted.append(obj)

    async def flush(self):
        from datetime import datetime, timezone
        from app.models.user import PlatformRole
        from app.models.absence import AbsenceStatus
        from app.models.finance import FinanceStatus
        from app.models.invitation import InvitationStatus

        for obj in self.added:
            if hasattr(obj, "id") and getattr(obj, "id") is None:
                setattr(obj, "id", uuid.uuid4())
            if hasattr(obj, "is_active") and getattr(obj, "is_active") is None:
                setattr(obj, "is_active", True)
            if hasattr(obj, "platform_role") and getattr(obj, "platform_role") is None:
                setattr(obj, "platform_role", PlatformRole.USER)
            if hasattr(obj, "created_at") and getattr(obj, "created_at") is None:
                setattr(obj, "created_at", datetime.now(timezone.utc))
            if hasattr(obj, "status") and getattr(obj, "status") is None:
                if obj.__class__.__name__ == "Absence":
                    setattr(obj, "status", AbsenceStatus.PENDING)
                elif obj.__class__.__name__ == "FinanceRecord":
                    setattr(obj, "status", FinanceStatus.PENDING)
                elif obj.__class__.__name__ == "Invitation":
                    setattr(obj, "status", InvitationStatus.PENDING)

    async def refresh(self, obj, *_args, **_kwargs):
        return None
