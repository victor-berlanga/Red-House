from .models import ID, Model, Text


class TraceEvent(Model):
    id: ID
    source: Text
    action: Text
    occurred_at: Text
