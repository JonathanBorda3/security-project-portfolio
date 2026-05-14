#!/usr/bin/env python3

import os
import sys
import traceback
import json
import pickle
import time
from pathlib import Path
from termcolor import colored

err_bullet = colored(">>>", "red")
inf_bullet = colored(">>>", "green")

RRC04 = "rrc04"
RRC12 = "rrc12"
TASK_1A = "task_1a"
TASK_1B = "task_1b"
TASK_1C = "task_1c"
TASK_2 = "task_2"
TASK_3 = "task_3"
TASK_4 = "task_4"

runtimes = {
    "summary": {RRC04: 0, RRC12: 0}, 
    "details": {RRC04: {TASK_1A: 0, TASK_1B: 0, TASK_1C: 0, TASK_2: 0, TASK_3: 0, TASK_4: 0}, RRC12: {TASK_1A: 0, TASK_1B: 0, TASK_1C: 0, TASK_2: 0, TASK_3: 0, TASK_4: 0}}
}

# pickle files are a standard way of serializing data in Python
# https://docs.python.org/3/library/pickle.html
def write_pickle(data, fpath):
    try:
        with open(Path(fpath), "wb") as f:
            pickle.dump(data, f)
    except Exception as e:
        print(f"{err_prologue} (pickle): {repr(e)}\n")


# Python also allows serialization of data to JSON, but you're not guaranteed to be able to capture all Python type
# https://docs.python.org/3/library/pickle.html#comparison-with-json
#def write_j(data, fpath, task):
def write_json(data, fpath, sort_keys=False, indent=4):
    try:
        with open(Path(fpath), "w") as f:
            json.dump(data, f, sort_keys=sort_keys, indent=indent)
            f.write("\n")
    except Exception as e:
        print(f"{err_prologue} {task} (json): {repr(e)}\n")


def load_reference_solution(collector, task):
    solution_file = Path(collector, f"reference_solution/{task}.p")
    try:
        with open(solution_file, "rb") as reference_solution:
            return pickle.load(reference_solution)
    except Exception as e:
        print(f"{err_prologue} (pickle): {repr(e)}\n")


if __name__ == "__main__":
    BASE_DIR = Path(os.path.abspath(__file__)).parent
    if BASE_DIR != Path(os.getcwd()):
        # print(f"{BASE_DIR} != {os.getcwd()} - changing")
        os.chdir(BASE_DIR)

    def get_cache_files(data_set, kind):
        return sorted([str(p) for p in Path(data_set, kind).glob("*.cache")])

    try:
        # import all the functions and exit with error if any fail
        try:
            from bgpm import unique_prefixes_by_snapshot
            from bgpm import unique_ases_by_snapshot
            from bgpm import top_10_ases_by_prefix_growth
            from bgpm import shortest_path_by_origin_by_snapshot
            from bgpm import aw_event_durations
            from bgpm import rtbh_event_durations
            msg = colored("All functions imported", attrs=["bold"])
            print(f"{inf_bullet} {msg}")
        except (ImportError, Exception) as e:
            print(f"{err_bullet} {repr(e)}")

        tasks = [
            (TASK_1A, unique_prefixes_by_snapshot, "rib_files"),
            (TASK_1B, unique_ases_by_snapshot, "rib_files"),
            (TASK_1C, top_10_ases_by_prefix_growth, "rib_files"),
            (TASK_2, shortest_path_by_origin_by_snapshot, "rib_files"),
            (TASK_3, aw_event_durations, "update_files"),
            (TASK_4, rtbh_event_durations, "update_files_blackholing"),
        ]

        collectors = [RRC04, RRC12]

        for collector in collectors:
            msg = colored(f"Processing {collector}", attrs=["bold"])
            print(f"\n{msg}")
            for task, func, arg in tasks:
                task_id = f"{collector}[{task:<7}]"
                inf_prologue = f"{inf_bullet} {task_id}"
                err_prologue = f"{err_bullet} {task_id}"

                try:
                    # run the task and capture timing information
                    begin = time.perf_counter()
                    res = func(get_cache_files(collector, arg))
                    end = time.perf_counter()
                    runtimes["details"][collector][task] = (end - begin)
                    if not res:
                        # res is empty, so nothing needs to be cached to disk - student skipped this task
                        print(f"{err_prologue} nothing returned for this task")
                    else:
                        # something was returned, so check the result
                        # check signature of result
                        if task in [TASK_1A, TASK_1B, TASK_1C]:
                            if type(res) is not type([]):
                                print(f"{err_prologue} your function should return a '{type([])}', not a '{type(res)}'")
    
                        if task in [TASK_2, TASK_3, TASK_4]:
                            if type(res) is not type({}):
                                print(f"{err_prologue} your function should return a '{type({})}', not a '{type(res)}'")

                        # check student solution against reference solution
                        solution = load_reference_solution(collector, task)

                        # there is a tie in the solution for Task 1C - it can be ignored, because the hidden data set has no tie
                        if solution != res and task == TASK_1C:
                            # reverse the tied elements and continue with the comparison
                            # rrc04_1c = {
                            #     "right": ["18300", "197328", "24309", "48159", "54540", "33330", "132061", "17072", "30036", "23650"],
                            #     "wrong": ["18300", "197328", "24309", "48159", "54540", "132061", "33330", "17072", "30036", "23650"]
                            #     #                                                       ^^^^^^^^^^^^^^^^^
                            # }
                            # rrc12_1c = {
                            #     "right": ["24309", "48159", "54540", "33330", "132061", "17072", "38370", "30036", "23650", "45090"],
                            #     "wrong": ["24309", "48159", "54540", "132061", "33330", "17072", "38370", "30036", "23650", "45090"]
                            #     #                                    ^^^^^^^^^^^^^^^^^
                            # }

                            v33330, v132061 = ['33330', '132061']
                            if all(origin in res for origin in [v33330, v132061]):
                                ndx33330, ndx132061 = res.index(v33330), res.index(v132061)
                                if abs(ndx33330 - ndx132061) == 1 and ndx33330 > ndx132061:
                                    res[ndx33330], res[ndx132061] = res[ndx132061], res[ndx33330]
                            
                        if solution == res:
                            print(f"{inf_prologue} returned value is correct")
                        else:
                            # solution and res don't match, even after tie-breaking
                            json_sort_keys = task in [TASK_2, TASK_3, TASK_4]
                            output_directory = Path(Path(collector), "student_solution")
                            output_json = Path(output_directory, f"{task}.json")
                            write_json(res, output_json, sort_keys=json_sort_keys)
                            print(f"{err_prologue} returned value is incorrect - your output is saved in {output_json}")
                            # if you want to create a pickle file (https://docs.python.org/3/library/pickle.html), uncomment the next line
                            # output_pickle = Path(output_directory, f"{task}.p")
                            # write_pickle(res, output_pickle)
                except (ImportError, Exception) as e:
                    print("here")
                    print(f"{err_prologue} {repr(e)}\n")
                    traceback.print_exc()

        # record timing summaries
        for collector in collectors:
            runtimes["summary"][collector] = sum(runtimes["details"][collector].values())

        # uncomment the next line if you want to record your runtime results to a file
        # write_json(runtimes, "runtimes.json")

        print("\nTiming Summary:")
        print(json.dumps(runtimes["summary"], indent=4))
        print("\nTiming Details:")
        print(json.dumps(runtimes["details"], indent=4))

    except Exception as e:
        # something bad happened, so print it to real stderr
        print(repr(e))
    finally:
        # clean up stdout
        sys.stdout.flush()
