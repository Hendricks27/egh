
import os
import sys
import time
import json
import shutil
import random
import string
import multiprocessing
from APIFramework import APIFramework, APIFrameworkWithFrontEnd, queue



class Final(APIFrameworkWithFrontEnd):

    def form_task(self, p):
        res = {}

        # task_str = p["original_file_name"].encode("utf-8")
        list_id = self.str2hash(''.join(random.choices(string.ascii_uppercase + string.digits, k=1000)).encode("utf-8"))

        res["id"] = list_id
        # res["task_type"] = p["task_type"]

        return res

    def file_check_and_process(self, input_path, output_path):
        return


    def worker(self, pid, task_queue, result_queue, suicide_queue_pair, params):

        self.output(2, "Worker-%s is starting up" % (pid))

        self.output(2, "Worker-%s is ready to take job" % (pid))

        while True:
            task_detail = self.task_queue_get(task_queue, pid, suicide_queue_pair)

            self.output(2, "Worker-%s is computing task: %s" % (pid, task_detail))

            error = []
            calculation_start_time = time.time()

            try:
                os.mkdir("./task/")
            except:
                pass

            list_id = task_detail["id"]

            working_dir = "./task/" + list_id + "/"
            input_file = working_dir + "/data.txt"
            output_file = working_dir + "data2.bw"
            datahub_file = working_dir + "/datahub.json"
            os.mkdir(working_dir)
            shutil.copy("./input/%s" % list_id, input_file)

            cmd = "./bin/bedGraphToBigWig %s http://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.chrom.sizes %s" % (input_file, output_file)
            os.system(cmd)


            datahub = [{
                "type": "bigwig",
                "name": "Your Track 1",
                "url": "https://localhost:10981/%s" % output_file,
                "options": {
                    "color": "blue"
                },
                "showOnHubLoad": True
            }]
            json.dump(datahub, open(datahub_file, "w"))


            result = "https://epigenomegateway.wustl.edu/browser/?genome={genome}&hub={datahub}".format(
                genome="hg38",
                datahub="https://localhost:10981" + datahub_file[1:]
            )

            calculation_end_time = time.time()
            calculation_time_cost = calculation_end_time - calculation_start_time

            self.output(2, "Worker-%s finished computing job (%s)" % (pid, list_id))

            res = {
                "id": list_id,
                "start time": calculation_start_time,
                "end time": calculation_end_time,
                "runtime": calculation_time_cost,
                "error": error,
                "result": result
            }

            self.output(2, "Job (%s): %s" % (list_id, res))

            result_queue.put(res)




if __name__ == '__main__':
    multiprocessing.freeze_support()

    browserhelper_app = Final()
    browserhelper_app.find_config("browserhelper.ini")
    browserhelper_app.start()




