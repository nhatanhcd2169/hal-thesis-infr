import typing as T

class Metrics(T.TypedDict):
    mae_linear: float
    mse_linear: float
    r2_linear: float
    mae_random_forest: float
    mse_random_forest: float
    r2_random_forest: float

class PredictRange(T.TypedDict):
    start: float
    current: float
    end: float
    per_day: float
    per_hour: float

class PredictOutput(T.TypedDict):
    metrics: Metrics
    predict_range: PredictRange
    ts_unit: str
    data: T.List[T.Dict]