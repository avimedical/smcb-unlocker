import dataclasses
from logging import Filter, LogRecord

from smcb_unlocker.client.konnektor.admin.model import ProtocolEntry


class GoogleCloudLoggingJsonFieldsFilter(Filter):
    def filter(self, record: LogRecord) -> bool:
        json_fields = record.__dict__.get("json_fields", {})

        if hasattr(record, "job"):
            if dataclasses.is_dataclass(record.job):
                job_dict = { field.name: getattr(record.job, field.name) for field in dataclasses.fields(record.job) if field.repr }
                job_dict["type"] = type(record.job).__name__
                json_fields["job"] = job_dict
            else:
                json_fields["job"] = str(record.job)

        if hasattr(record, "protocol"):
            if isinstance(record.protocol, ProtocolEntry):
                json_fields["protocol"] = record.protocol.model_dump()
            else:
                json_fields["protocol"] = str(record.protocol)

        record.json_fields = json_fields
        return super().filter(record)
