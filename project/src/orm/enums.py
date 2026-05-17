import enum


class PredictionStatus(str, enum.Enum):
    READY = "READY"
    FAILED = "FAILED"


class AnalyticStatus(str, enum.Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    READY = "READY"
    FAILED = "FAILED"


class DataType(str, enum.Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    DATETIME = "DATETIME"
