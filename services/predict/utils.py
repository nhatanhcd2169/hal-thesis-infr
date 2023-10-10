import os
import json
import psycopg2
import numpy as np
import pandas as pd
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn import metrics

ELASTICSEARCH_INDEX = os.environ.get("ELASTICSEARCH_INDEX", None)
ELASTICSEARCH_CONFIG = os.environ.get("ELASTICSEARCH_CONFIG", "{}")
POSTGRES_CONFIG = os.environ.get("POSTGRES_CONFIG", "{}")
PREDICT_RANGE = os.environ.get("PREDICT_RANGE", '{"days": 7}')

ELASTICSEARCH_CONFIG = json.loads(ELASTICSEARCH_CONFIG)
POSTGRES_CONFIG = json.loads(POSTGRES_CONFIG)
PREDICT_RANGE = json.loads(PREDICT_RANGE)


def check_config(config: dict, fields: list):
    for field in fields:
        if field not in config:
            return False
    return True


assert ELASTICSEARCH_INDEX
assert check_config(ELASTICSEARCH_CONFIG, ["hosts"])
assert check_config(POSTGRES_CONFIG, ["user", "password", "host", "port"])

USER, PASSWORD, HOST, PORT = (
    POSTGRES_CONFIG.pop("user"),
    POSTGRES_CONFIG.pop("password"),
    POSTGRES_CONFIG.pop("host"),
    POSTGRES_CONFIG.pop("port"),
)

DATA_DIR = "output"

POSTGRES_URL = f"postgres://{USER}:{PASSWORD}@{HOST}:{PORT}"

if POSTGRES_CONFIG:
    POSTGRES_URL += "&".join(
        [f"{key}={POSTGRES_CONFIG[key]}" for key in POSTGRES_CONFIG]
    )

PERCENTILES = [25, 50, 75, 80, 85, 90, 99]


def pipeline_stage(stage_name: str):
    def wrapper(func):
        def inner(*args, **kwargs):
            print("---------------------------------------------------------------")
            print("start_stage:", stage_name)
            func(*args, **kwargs)
            try:
                pass
            except Exception as err:
                print("encounter error:", err.__class__.__name__)
                print("full detail:", err)
            print("end_stage:", stage_name)
            print("---------------------------------------------------------------")

        return inner

    return wrapper


@pipeline_stage("get data")
def stage_1():
    def enrich(record):
        _ts = datetime.fromisoformat(record["key_as_string"])
        _output = {}
        _output["ts"] = record["key"]
        _output["ts_iso"] = record["key_as_string"]
        _output["dow"] = _ts.isoweekday()
        _output["weekend"] = _ts.isoweekday in [6, 7]
        _output["occurences"] = record["doc_count"]
        for key in record:
            if key not in ["key", "key_as_string", "doc_count"]:
                _output[key] = record[key]
        return _output

    conn = psycopg2.connect(POSTGRES_URL)
    output = {}
    try:
        client = Elasticsearch(**ELASTICSEARCH_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, host FROM services")
        services = cursor.fetchall()

        for service in services[:]:
            _query = {"bool": {"must": {"match": {"service.id": service[0]}}}}
            _runtime_mappings = {
                "hour_truncated_time": {
                    "type": "date",
                    "script": """
                            ZonedDateTime truncatedDateTime = doc['@timestamp'].value.truncatedTo(ChronoUnit.HOURS);
                            long miliTimestamp = truncatedDateTime.toEpochSecond() * 1000;
                            emit(miliTimestamp);
                        """,
                },
            }
            _fields = ["hour_truncated_time"]
            _aggs = {
                "aggs": {
                    "terms": {
                        "size": 10000,
                        "field": "hour_truncated_time",
                        "order": {"_key": "desc"},
                    },
                    "aggs": {
                        "latency_stats": {"stats": {"field": "latencies.request"}},
                        "request_size_stats": {"stats": {"field": "request.size"}},
                        "response_size_stats": {"stats": {"field": "response.size"}},
                    },
                },
            }

            data = client.search(
                index=ELASTICSEARCH_INDEX,
                query=_query,
                runtime_mappings=_runtime_mappings,
                fields=_fields,
                size=0,
                aggs=_aggs,
            ).body

            os.makedirs(f"{DATA_DIR}/{service[0]}/new_metrics", exist_ok=True)

            raw_aggregations = data["aggregations"]["aggs"]["buckets"]
            aggregated_data = [enrich(record) for record in raw_aggregations]

            output = {
                "id": service[0],
                "name": service[1],
                "data": aggregated_data,
            }

            with open(f"{DATA_DIR}/{service[0]}/new_metrics/stage-1.json", "w") as file:
                json.dump(
                    output,
                    file,
                    indent=2,
                )

    except Exception as err:
        print("Encountered", err.__class__.__name__)
        print(err)

    finally:
        conn.close()


@pipeline_stage("predict timeseries")
def stage_2():
    def to_date(ts: float):
        return datetime.fromtimestamp(ts / 1000)

    def get_X(record):
        return (
            record["ts"],
            record["dow"],
            record["weekend"],
        )

    def get_Y(record):
        return record["latency_stats"]["avg"]

    def get_Xy(data):
        def get_data():
            samp_ = []
            feat_ = []
            for record in data:
                samp_.append(get_X(record))
                feat_.append(get_Y(record))
            return samp_, feat_

        X_train, X_test, y_train, y_test = train_test_split(
            *get_data(), test_size=1 / 3, random_state=0
        )

        return X_train, X_test, y_train, y_test

    for service_id in os.listdir(DATA_DIR)[:]:
        data = []
        with open(f"{DATA_DIR}/{service_id}/new_metrics/stage-1.json", "r") as file:
            data = json.load(file)["data"]

        train_samples, _, train_features, _ = get_Xy(data)

        org_ts = {point["ts"]: idx for idx, point in enumerate(data)}

        # TODO: Limit the output so that the payload is not too big
        ext_start_range = to_date(data[-1]["ts"])
        ext_predict_range = timedelta(**PREDICT_RANGE)
        ext_end_range = datetime.utcnow() + ext_predict_range

        ext_date_range = pd.date_range(
            ext_start_range,
            ext_end_range,
            freq="h",
        )
        test_samples = []
        test_features = []
        ext_samples = []
        ext_features = []
        for idx, ext_date in enumerate(ext_date_range):
            _sample = get_X(
                {
                    "ts": ext_date.timestamp() * 1000,
                    "dow": ext_date.isoweekday(),
                    "weekend": ext_date.isoweekday() in [6, 7],
                }
            )
            _feature = None
            if _sample[0] in org_ts:
                org_idx = org_ts[_sample[0]]
                _feature = get_Y(data[org_idx])
                test_samples.append(_sample)
                test_features.append(_feature)
            ext_samples.append(_sample)
            ext_features.append(_feature)

        rfr = RandomForestRegressor(200).fit(train_samples, train_features)
        lr = LinearRegression().fit(train_samples, train_features)
        rfr_features = rfr.predict(ext_samples)
        pred_features = [
            rfr_features[idx]
            for idx in range(len(ext_features))
            if ext_features[idx] is not None
        ]
        rfr_mae = metrics.mean_absolute_error(test_features, pred_features)
        rfr_mse = metrics.mean_squared_error(test_features, pred_features)
        rfr_r2 = metrics.r2_score(test_features, pred_features)
        lr_features = lr.predict(ext_samples)
        pred_features = [
            lr_features[idx]
            for idx in range(len(ext_features))
            if ext_features[idx] is not None
        ]
        lr_mae = metrics.mean_absolute_error(test_features, pred_features)
        lr_mse = metrics.mean_squared_error(test_features, pred_features)
        lr_r2 = metrics.r2_score(test_features, pred_features)
        _df_data = []
        for idx in range(len(ext_samples)):
            _df_data.append(
                (
                    to_date(ext_samples[idx][0]).isoformat(),
                    *ext_samples[idx],
                    ext_features[idx],
                    rfr_features[idx],
                    lr_features[idx],
                )
            )
        df = pd.DataFrame(
            data=_df_data,
            columns=[
                "ts_iso",
                "ts",
                "dow",
                "weekend",
                "latency",
                "latency_random_forest",
                "latency_linear",
            ],
        )
        df.to_csv(
            f"{DATA_DIR}/{service_id}/new_metrics/stage-2.csv", header=True, index=False
        )
        with open(f"{DATA_DIR}/{service_id}/new_metrics/stage-2.json", "w") as file:
            json.dump(
                {
                    "metrics": {
                        "mae_linear": lr_mae,
                        "mse_linear": lr_mse,
                        "r2_linear": lr_r2,
                        "mae_random_forest": rfr_mae,
                        "mse_random_forest": rfr_mse,
                        "r2_random_forest": rfr_r2,
                    },
                    "predict_range": {
                        "start": data[-1]["ts"],
                        "current": data[0]["ts"],
                        "end": ext_samples[-1][0],
                        "per_day": timedelta(days=1).total_seconds() * 1000,
                        "per_hour": timedelta(hours=1).total_seconds() * 1000,
                    },
                    "ts_unit": "ms",
                    "data": df.replace(np.nan, None).to_dict(orient="records"),
                },
                file,
                indent=None,
            )


@pipeline_stage("ingest to ES")
def stage_3():
    for service_id in os.listdir(DATA_DIR)[:]:
        data = {}
        with open(f"{DATA_DIR}/{service_id}/new_metrics/stage-2.json", "r") as file:
            data = json.load(file)
        client = Elasticsearch(**ELASTICSEARCH_CONFIG)
        client.index(
            id=service_id,
            index="predict",
            document=data,
        )
