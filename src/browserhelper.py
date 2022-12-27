
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

    # TODO list (Back End)
    # Delete after certain period, eg 24h
    # More format support (cov, wig, ... )
    # Status queue
    # Multiple OS support
    # Genome select

    # TODO list (Front End)
    # Status queue
    # New result page (Manifest, status, URL embeded parameters)
    #


    def get_file_type(self, file_path):


        init = True
        linecount = 0
        supported_type = ["bed", "bedgraph", "qbed"] # , ""
        supported_type_flag = {}
        for st in supported_type:
            supported_type_flag[st] = True


        with open(file_path) as f:

            for l in f:
                if init:
                    init = False
                    continue
                l = l.strip().split("\t")

                if linecount > 1000:
                    break

                # BEDGRAPH
                if len(l) != 4:
                    supported_type_flag["bedgraph"] = False
                try:
                    float(l[3])
                except ValueError:
                    supported_type_flag["bedgraph"] = False

                # qBed
                if len(l) != 6:
                    supported_type_flag["qbed"] = False
                try:
                    float(l[3])
                except ValueError:
                    supported_type_flag["qbed"] = False
                if l[4] not in "+-":
                    supported_type_flag["qbed"] = False

        res = None
        for st in reversed(supported_type):
            if supported_type_flag[st]:
                res = st
                break
        return res

    def file_check_and_process(self, input_path, original_file_name=None, assembly="hg38"):
        res = {
            "original_type": "",
            "converted_type": "",
            "converted_path": "",
            "error": [],
            # "": "",
        }

        chrom_size = f"http://hgdownload.soe.ucsc.edu/goldenPath/{assembly}/bigZips/{assembly}.chrom.sizes"

        file_extension = None
        if original_file_name != None and len(original_file_name.split(".")) > 0:
            file_extension = original_file_name.split(".")[-1].lower()
            if file_extension in ["bedgraph", "qbed", "qbed", "ccf", "bg"]:
                res["original_type"] = file_extension

        if res["original_type"] == "":
            # Get file type
            res["original_type"] = self.get_file_type(input_path)
            if res["original_type"] == None:
                res["error"].append("Cannot determine file type")


        output_path = input_path.replace("input", "output")
        res["converted_path"] = output_path


        print(res)
        if res["original_type"] in ["qbed", "ccf", "bed"]:

            tmp_format = "bed"
            if res["original_type"] != "bed":
                tmp_format = "qbed"

            cmd1 = "sort -k1V -k2n -k3n {input_path} > {output_path}.{tmp_format}".format(
                input_path=input_path, output_path=output_path, tmp_format=tmp_format
            )

            cmd2 = "bgzip {output_path}.{tmp_format}".format(
                output_path=output_path, tmp_format=tmp_format
            )

            cmd3 = "tabix -p bed {output_path}.{tmp_format}.gz".format(
                output_path=output_path, tmp_format=tmp_format
            )

            res["converted_type"] = "{tmp_format}".format(tmp_format=tmp_format)
            res["converted_path"] += ".{tmp_format}.gz".format(tmp_format=tmp_format)

            os.system(cmd1)
            os.system(cmd2)
            os.system(cmd3)

        elif res["original_type"] in ["bg", "bedgraph"]:
            cmd1 = "sort -k1,1 -k2,2n %s > %s.bedgraph" % (input_path, output_path)
            cmd2 = "./bin/bedGraphToBigWig %s.bedgraph %s %s.bigwig" % (output_path, chrom_size, output_path)

            res["converted_type"] = "bigwig"
            res["converted_path"] += ".bigwig"

            os.system(cmd1)
            os.system(cmd2)

        else:

            ""

        return res



    def worker(self, pid, task_queue, result_queue, suicide_queue_pair, params):

        self.output(2, "Worker-%s is starting up" % (pid))

        tmp_port = ""
        if params["public_facing_port"] not in [22, "22"]:
            tmp_port = ":%s" % params["public_facing_port"]
        public_facing_url = "%s://%s%s/" % (params["public_facing_protocol"], params["public_facing_host"], tmp_port)

        self.output(2, "Worker-%s is ready to take job" % (pid))

        while True:
            task_detail = self.task_queue_get(task_queue, pid, suicide_queue_pair)

            self.output(2, "Worker-%s is computing task: %s" % (pid, task_detail))

            error = []
            calculation_start_time = time.time()

            print(task_detail)
            list_id = task_detail["id"]
            assembly = task_detail.get("assembly", "hg38")

            working_dir = "./task/" + list_id + "/"
            working_dir_input = "./task/" + list_id + "/input/"
            working_dir_output = "./task/" + list_id + "/output/"

            datahub = []
            mapping = []
            datahub_file = working_dir_output + "/datahub.json"
            for original_file_name in task_detail["file_mapping"]:
                hash_file_name = task_detail["file_mapping"][original_file_name]

                input_file = working_dir_input + hash_file_name
                converting_process = self.file_check_and_process(
                    input_file,
                    original_file_name=original_file_name,
                    assembly=assembly,
                )

                original_type = converting_process["original_type"]
                converted_type = converting_process["converted_type"]
                converted_path = converting_process["converted_path"]

                mapping.append((original_file_name, original_type, converted_type, converted_path))

                datahub0 = {
                    "type": converted_type,
                    "name": original_file_name,
                    "url": "%s%s" % (public_facing_url, converted_path),
                    "options": {
                        # "color": "blue"
                    },
                    "showOnHubLoad": True
                }

                datahub.append(datahub0)
                print(datahub0)


            json.dump(datahub, open(datahub_file, "w"))


            result_url = "https://epigenomegateway.wustl.edu/browser/?genome={genome}&hub={datahub}".format(
                genome="hg38",
                datahub=public_facing_url + datahub_file[1:]
            )

            result = {
                "gburl": result_url,
                "dhjson": datahub_file[1:],
                "file_mapping": mapping
            }

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




