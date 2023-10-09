import utils as U
import sys
if __name__ == "__main__":
    argv = [int(arg) for arg in sys.argv[1:]]
    stages = [arg - 1 for arg in argv]
    U.run(stages)
