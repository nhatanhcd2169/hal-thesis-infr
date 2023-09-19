import utils
from celery import shared_task

@shared_task
def regression_analyze():
    print("-- Services' metrics")
    services_metrics = utils.get_service_metrics()
    print("-- Services' regression function (x = float64_time)")
    for service_metrics in services_metrics:
        data = service_metrics[0][::-1]
        output = utils.run_linear_function(data, service_metrics[3], {"days": 12})
        print(f'{service_metrics[3]}:')
        for key in output:
            linear_ = output[key]['linear_function']
            func_ = f"f(x) = {linear_['weight']} * x + {linear_['bias']}"
            print(f'\t- {key}:', func_)
