import datetime
import decimal
import enum
import json
from dataclasses import asdict, is_dataclass
from typing import Any


class EnhancedJsonEncoder(json.JSONEncoder):
    """
    Custom json Encoder to properly handle decimals, datetimes and dataclasses
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)

        if isinstance(o, datetime.datetime):
            return o.isoformat()

        if isinstance(o, enum.Enum):
            return o.value

        if is_dataclass(o):
            return asdict(o)  # type: ignore

        return super(EnhancedJsonEncoder, self).default(o)
