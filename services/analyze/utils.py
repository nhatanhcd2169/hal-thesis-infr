import os
import json
import psycopg2
import numpy as np
import pandas as pd
from sklearn import linear_model
from celery import Celery, shared_task
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta

ELASTICSEARCH_INDEX = os.environ.get("ELASTICSEARCH_INDEX", None)
ELASTICSEARCH_CONFIG = os.environ.get("ELASTICSEARCH_CONFIG", "{}")
POSTGRES_CONFIG = os.environ.get("POSTGRES_CONFIG", "{}")

ELASTICSEARCH_CONFIG = json.loads(ELASTICSEARCH_CONFIG)
POSTGRES_CONFIG = json.loads(POSTGRES_CONFIG)

def check_config(config: dict, fields: list):
    for field in fields:
        if field not in config:
            return False
    return True

assert ELASTICSEARCH_INDEX
assert check_config(ELASTICSEARCH_CONFIG, ["hosts"])
assert check_config(POSTGRES_CONFIG, ["user", "password", "host", "port"])


POSTGRES_URL = "postgres://{user}:{password}@{host}:{port}".format(**POSTGRES_CONFIG)

def get_service_metrics():
    total_aggs = []
    conn = psycopg2.connect(POSTGRES_URL )

    
    try:
        client = Elasticsearch(**ELASTICSEARCH_CONFIG)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM "public"."services"')
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
                "date_of_week": {
                    "type": "long",
                    "script": """
                            ZonedDateTime dateTime = doc['@timestamp'].value;
                            long dow = dateTime.getDayOfWeek().getValue();
                            emit(dow);
                        """,
                },
            }
            _fields = ["hour_truncated_time", "is_weekend"]
            _aggs = {
                "latency_percentiles_wrt_time": {
                    "terms": {
                        "field": "hour_truncated_time",
                        "order": {"_key": "desc"},
                        "size": 10000,
                    },
                    "aggs": {
                        "percentages": {
                            "percentiles": {
                                "field": "latencies.request",
                                "percents": [25, 50, 75, 80, 85, 90, 99],
                            }
                        },
                        "stats": {"stats": {"field": "latencies.request"}},
                    },
                }
            }

            data = client.search(
                index=ELASTICSEARCH_INDEX,
                query=_query,
                runtime_mappings=_runtime_mappings,
                fields=_fields,
                size=0,
                aggs=_aggs,
            ).body

            total = 0
            aggregations = data["aggregations"]["latency_percentiles_wrt_time"]["buckets"]

            for record in aggregations:
                total += record["doc_count"]

            total_aggs.append(
                (aggregations, len(aggregations), service[1], service[0], total)
            )
            
            os.makedirs(f"output/{service[0]}", exist_ok=True)

            with open(f"output/{service[0]}/metrics.json", "w") as file:
                json.dump(
                    {
                        "id": service[0],
                        "name": service[1],
                        "length": len(aggregations),
                        "total": total,
                        "data": aggregations,
                    },
                    file,
                    indent=2,
                )

        for total_agg in total_aggs:
            print(f"[{total_agg[3]}] {total_agg[2]} ({total_agg[1]}) -> {total_agg[-1]}")

        print("Total =", sum([agg[-1] for agg in total_aggs]))
        
    except Exception as err:
        print('Encountered', err.__class__.__name__)

    finally:
        conn.close()

    return total_aggs


def timeseries_linear_regression(
    features: pd.Series,
    train_str_dates: pd.DatetimeIndex,
    train_flt_dates: np.ndarray,
    predict_str_dates: pd.DatetimeIndex,
    predict_flt_dates: np.ndarray,
):
    """
    Build linear regression model for time series data

    @Args:
        - `features` (`pd.Series`): sample data on y-axis
        - `train_str_dates` (`pd.DatetimeIndex`): sample dates
        - `train_flt_dates` (`np.ndarray`): sample dates in `float64`
        - `predict_str_dates` (`pd.DatetimeIndex`): predict dates
        - `predict_flt_dates` (`np.ndarray`): predict dates in `float64`

    @Returns: tri-pair dictionary (`train_data`, `predict_points`, `linear_function`):
        - `train_data`: `features`                          -> Input from the function
        - `predict_points`: `predict_values`                -> Start and end point for regression line
        - `linear_function`: {`weight`: ..., `bias`: ... }  -> Weight and bias of regression function
    """

    lm = linear_model.LinearRegression()
    model = lm.fit(train_flt_dates.reshape(-1, 1), features)
    weight, bias = model.coef_, model.intercept_
    linear_formula = lambda flt_date: weight * flt_date + bias

    predict_values = np.array(
        [linear_formula(predict_flt_date) for predict_flt_date in predict_flt_dates]
    )
    train_data = {
        "timestamp": train_flt_dates.tolist(),
        "latency": features
    }
    predict_data = {
        "timestamp": predict_flt_dates.tolist(),
        "latency": predict_values.reshape(-1).tolist()
    }

    train_ = pd.DataFrame(
        data=train_data,
        index=train_str_dates
    )
    predict_ = pd.DataFrame(
        data=predict_data,
        index=predict_str_dates
    )
    output = {
        "train_data": train_,
        "predict_points": predict_,
        "linear_function": {
            "weight": weight,
            "bias": bias
        },
    }
    return output


def run_linear_function(data, filename: str, predict_range: dict):
    """
    Feed data into linear regression model
    
    @Args:
        data (list<dict>): input data for analyze function
        predict_range (dict, optional): Dictionary indicates range for regression line. Defaults to {}.


    @Returns: 5-pair dictionary (`mean`, `50th`, `75th`, `85th`, `99th`):
        - `mean`: `train_data`, `predict_points`, `linear_function` for average
        - `50th`: `train_data`, `predict_points`, `linear_function` for 50th percentiles
        - `75th`: `train_data`, `predict_points`, `linear_function` for 75th percentiles
        - `85th`: `train_data`, `predict_points`, `linear_function` for 85th percentiles
        - `99th`: `train_data`, `predict_points`, `linear_function` for 99th percentiles

    .. highlight:: python
    .. code-block:: python
    [
        {
            "key": "float64",
            "key_as_string": "optional",
            "doc_count": "long",
            "stats": {
                "count": "float64",
                "min": "float64",
                "max": "float64",
                "avg": "float64",
                "sum": "float64",
            },
            "percentages": {
                "values": {
                    "25.0": "float64",
                    "50.0": "float64",
                    "75.0": "float64",
                    "80.0": "float64",
                    "85.0": "float64",
                    "90.0": "float64",
                    "99.0": "float64",
                }
            },
        }
    ]
    """
    df_data = [
        (
            data_point["stats"]["avg"],
            data_point["percentages"]["values"]["50.0"],
            data_point["percentages"]["values"]["75.0"],
            data_point["percentages"]["values"]["85.0"],
            data_point["percentages"]["values"]["99.0"],
        )
        for data_point in data
    ]
    index = [datetime.fromtimestamp(data_point["key"] / 1000) for data_point in data]
    columns = [
        "latency_mean",
        "latency_50th",
        "latency_75th",
        "latency_85th",
        "latency_99th",
    ]
    df = pd.DataFrame(
        data=df_data,
        columns=columns,
        index=index,
    )
    if not len(predict_range):
        predict_day = 1
    else:
        predict_day = predict_range.pop("days", 0)

    str_dates = df.index
    ext_str_dates = pd.date_range(
        str_dates[0],
        str_dates[-1] + timedelta(days=predict_day, **predict_range),
        freq="h",
    )
    flt_dates = str_dates.to_numpy(dtype="float64")
    ext_flt_dates = ext_str_dates.to_numpy(dtype="float64")
    params_gen = lambda field: [
        df[field],
        str_dates,
        flt_dates,
        ext_str_dates,
        ext_flt_dates,
    ]
    output = {}
    for column in columns:
        params = params_gen(column)
        general_column = column.split("_")[-1]
        linear_output = timeseries_linear_regression(*params)
        linear_output_keys = [key for key in linear_output.keys()]
        filepath = f'output/{filename.split(".json")[0]}'
        new_folder_path = f'{filepath}/{general_column}'
        os.makedirs(new_folder_path, exist_ok=True)
        for key in linear_output_keys:
            new_path = f'{new_folder_path}/{key}.csv'
            output_df = pd.DataFrame(linear_output[key])
            if 'linear' not in key:
                output_df = output_df.reset_index().rename(columns={"index": "datetime"})
            output_df.to_csv(new_path, index=False)
        output[general_column] = linear_output
    return output

