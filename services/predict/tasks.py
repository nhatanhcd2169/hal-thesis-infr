
import utils
from celery import shared_task

@shared_task
def run_pipeline(stages: list[int] = []):
    pipe_stages = [
        utils.stage_1,
        utils.stage_2,
        utils.stage_3,
    ]
    if not len(stages):
        print("Run full pipeline")
        for pipe_stage in pipe_stages:
            pipe_stage()
    else:
        print("Run specific stages")
        for stage in stages:
            pipe_stages[stage - 1]()

