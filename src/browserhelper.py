
import os
import re
import sys
import time
import json
import shutil
import platform
import subprocess
import multiprocessing
from APIFramework import APIFramework, APIFrameworkWithFrontEnd, queue

import conversionscript


class EGH(APIFrameworkWithFrontEnd):

    # TODO list (Back End)
    # Original File name
    # AWS / GCP / Azure
    # Ensemble / UCSC Genome Browser Support

    # TODO list (Front End)
    # Prettier result page

    _allowed_genome = [
        "hg19", "hg38",
        "panTro4", "panTro5", "panTro6",
        "gorGor3", "gorGor4",

        "nomLeu3",
        "papAnu2",
        "rheMac2", "rheMac3", "rheMac8", "rheMac10",

        "calJac3", "calJac4",
        "bosTau8",
        "oviAri4",

        "susScr3", "susScr11",
        "oryCun2",
        "canFam2", "canFam3",

        "mm9", "mm10", "mm39",
        "rn4", "rn6", "rn7",
        "monDom5",

        "galGal5", "galGal6",
        "xenTro10",
        "danRer7", "danRer10", "danRer11",

        "sacCer3",

    ]

    # bedgraph ? dynseq ? bigInteract ?
    _bed_like_formats = ["bed", "qbed", "cov", "methylc", "categorical", "refbed", "longrange", ]
    _other_formats = ["wig", "bedgraph"]
    _processed_formats = ["bigwig", "bigbed", "hic", ]
    _all_format = _bed_like_formats + _other_formats + _processed_formats

    _longrange_column4_regex_pattern = re.compile(r"^(.*):(\d*)-(\d*),(\d*)$")


    def get_file_type(self, file_path):

        init = True
        linecount = 0

        supported_type = self._bed_like_formats + self._other_formats
        supported_type_flag = {}
        for st in supported_type:
            supported_type_flag[st] = True
        supported_type_flag["wig"] = False

        # Test Binary File
        try:
            with open(file_path) as f:
                for l in f:
                    break
        except:
            return None



        with open(file_path) as f:

            for l in f:
                if init:
                    init = False
                    continue

                if linecount > 1000:
                    break

                # Basic BED checking
                l = l.strip().split("\t")
                if len(l) < 3:
                    for st in self._bed_like_formats:
                        supported_type_flag[st] = False
                    break

                # BEDGRAPH
                if len(l) != 4:
                    supported_type_flag["bedgraph"] = False
                try:
                    float(l[3])
                except ValueError:
                    supported_type_flag["bedgraph"] = False

                # qBED
                if len(l) != 6:
                    supported_type_flag["qbed"] = False
                try:
                    float(l[3])
                except ValueError:
                    supported_type_flag["qbed"] = False
                if l[4] not in "+-":
                    supported_type_flag["qbed"] = False


                # Bismark CoV
                if len(l) != 6:
                    supported_type_flag["cov"] = False
                try:
                    float(l[3])
                    int(l[4])
                    int(l[5])
                except ValueError:
                    supported_type_flag["cov"] = False


                # methylc
                if len(l) != 7:
                    supported_type_flag["methylc"] = False
                try:
                    ml = float(l[4])
                    assert ml >= 0
                    assert ml <= 1
                    assert l[5] in ["+", "-"]
                    int(l[6])
                except (ValueError, AssertionError):
                    supported_type_flag["methylc"] = False


                # categorical
                if len(l) != 4:
                    supported_type_flag["categorical"] = False


                # longrange
                try:
                    # Example: chr1:234-567,89
                    assert len(self._longrange_column4_regex_pattern.findall(l[3])) > 0
                except AssertionError:
                    supported_type_flag["longrange"] = False


        with open(file_path) as f:
            for l in f:
                l = l.strip()
                if l.startswith("track") and "type=wiggle_0" in l:
                    supported_type_flag["wig"] = True
                    break


        res = None
        for st in reversed(supported_type):
            if supported_type_flag[st]:
                res = st
                break
        return res

    def file_check_and_process(self, input_path, original_file_name=None, assembly="hg38", pre_defined_file_format=None):
        res = {
            "original_type": "",
            "converted_type": "",
            "converted_path": "",
            "error": [],
            # "": "",
        }

        bin_folder = "./bin/linux/"
        if platform.processor() == "arm":
            bin_folder = "./bin/macarm/"

        # chrom_size = f"http://hgdownload.soe.ucsc.edu/goldenPath/{assembly}/bigZips/{assembly}.chrom.sizes"
        chrom_size = f"./chrom.sizes/{assembly}.chrom.sizes"

        # File Format Determined By User
        if pre_defined_file_format:
            res["original_type"] = pre_defined_file_format

        # Automatic
        else:
            # Try to determine file format by file extension
            file_extension = None
            file_dot_split = original_file_name.split(".")
            if original_file_name != None and len(file_dot_split) > 0:
                file_extension = file_dot_split[-1].lower()
                if file_extension in self._all_format:
                    res["original_type"] = file_extension

                if res["original_type"] == "bed":
                    if len(file_dot_split) > 2:
                        file_secondary_extension = file_dot_split[-2].lower()
                        if file_extension in self._bed_like_formats:
                            res["original_type"] = file_secondary_extension


            # Try to determine file format by file content
            if res["original_type"] == "":
                # Get file type
                ft = None
                try:
                    ft = self.get_file_type(input_path)
                except:
                    pass
                res["original_type"] = ft
                if res["original_type"] == None:
                    res["error"].append("Cannot determine file type")
                    return res


        output_path = input_path.replace("input", "output")
        res["converted_path"] = output_path


        print(res)
        # "bed", "methylc", "categorical", "refbed", "longrange"
        if res["original_type"] in self._bed_like_formats:
            tmp_format = res["original_type"]
            if res["original_type"] == "cov":
                tmp_format = "methylc"
                conversionscript.cov2methylC(input_path, input_path+".methylc", genome_path=f"./genome/{assembly}.fasta")
                input_path = input_path+".methylc"


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

            for cmd in [cmd1, cmd2, cmd3]:
                subp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cmd_out = subp.stdout.read().decode("utf-8")
                cmd_err = subp.stderr.read().decode("utf-8")

                if cmd_err != "":
                    res["error"].append(cmd_err)

        elif res["original_type"] in ["bedgraph"]:
            cmd1 = "sort -k1,1 -k2,2n %s > %s.bedgraph" % (input_path, output_path)
            cmd2 = "%s/bedGraphToBigWig %s.bedgraph %s %s.bigwig" % (bin_folder, output_path, chrom_size, output_path)

            res["converted_type"] = "bigwig"
            res["converted_path"] += ".bigwig"

            for cmd in [cmd1, cmd2]:
                subp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cmd_out = subp.stdout.read().decode("utf-8")
                cmd_err = subp.stderr.read().decode("utf-8")

                if cmd_err != "":
                    res["error"].append(cmd_err)

            os.remove("%s.bedgraph" % output_path)

        elif res["original_type"] in ["wig"]:
            cmd = "%s/wigToBigWig %s %s %s.bigwig" % (bin_folder, input_path, chrom_size, output_path)

            res["converted_type"] = "bigwig"
            res["converted_path"] += ".bigwig"

            subp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd_out = subp.stdout.read().decode("utf-8")
            cmd_err = subp.stderr.read().decode("utf-8")

            if cmd_err != "":
                res["error"].append(cmd_err)

        elif res["original_type"] in self._processed_formats:
            tmp_format = res["original_type"]
            cmd = f"mv {input_path} {output_path}.{tmp_format}"
            os.system(cmd)

            res["converted_type"] = tmp_format
            res["converted_path"] += f".{tmp_format}"

        else:
            ""

        return res


    def worker(self, pid, task_queue, status_queue, result_queue, suicide_queue_pair, params):

        self.output(2, "Worker-%s is starting up" % (pid))

        tmp_port = ""
        if params["public_facing_port"] not in [22, "22"]:
            tmp_port = ":%s" % params["public_facing_port"]
        public_facing_url = "%s://%s%s/" % (params["public_facing_protocol"], params["public_facing_host"], tmp_port)

        self.output(2, "Worker-%s is ready to take job" % (pid))

        import random
        random.randint(1, 100)

        while True:
            task_detail = self.task_queue_get(task_queue, pid, suicide_queue_pair)

            self.output(2, "Worker-%s is computing task: %s" % (pid, task_detail))

            error = []
            calculation_start_time = time.time()

            print(task_detail)
            task_id = task_detail["id"]
            assembly = task_detail["assembly"]
            if assembly not in self._allowed_genome:
                error.append("Genome Assembly (%s) is not supported" % assembly)
            pre_defined_file_formats = task_detail["pre_defined_file_format"]

            working_dir = "./task/" + task_id + "/"
            working_dir_input = "./task/" + task_id + "/input/"
            working_dir_output = "./task/" + task_id + "/output/"

            datahub = []
            mapping = []
            datahub_file = working_dir_output + "/datahub.json"


            status = {
                "id": task_id,
                "started": True,
                "working": "",
                "totalcount": len(task_detail["file_mapping"]),
                "finishedcount": 0,
            }
            status_queue.put(status)



            for original_file_name in task_detail["file_mapping"]:
                status["working"] = original_file_name
                status_queue.put(status)

                hash_file_name = task_detail["file_mapping"][original_file_name]

                input_file = working_dir_input + hash_file_name

                pre_defined_file_format = None
                if original_file_name in pre_defined_file_formats:
                    if pre_defined_file_formats[original_file_name] != "auto":
                        pre_defined_file_format = pre_defined_file_formats[original_file_name]

                converting_process = self.file_check_and_process(
                    input_file,
                    original_file_name=original_file_name,
                    assembly=assembly,
                    pre_defined_file_format=pre_defined_file_format

                )

                original_type = converting_process["original_type"]
                converted_type = converting_process["converted_type"]
                converted_path = converting_process["converted_path"]
                conversion_error = converting_process["error"]

                mapping.append((original_file_name, original_type, converted_type, converted_path, conversion_error))

                datahub0 = {
                    "type": converted_type,
                    "name": original_file_name,
                    "url": "%s%s" % (public_facing_url, converted_path),
                    "options": {
                        # "color": "blue"
                    },
                    "showOnHubLoad": True
                }

                if converted_type == "qbed":
                    datahub0["options"]["logScale"] = "log10"

                datahub.append(datahub0)

                print(datahub0)

                status["finishedcount"] += 1
                status_queue.put(status)

            shutil.rmtree(working_dir_input)

            cmd = f"zip -r ./task/{task_id}.zip ./task/{task_id} && mv ./task/{task_id}.zip ./task/{task_id}/all.zip"
            subp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd_out = subp.stdout.read().decode("utf-8")
            cmd_err = subp.stderr.read().decode("utf-8")


            json.dump(datahub, open(datahub_file, "w"))

            result_url = "https://epigenomegateway.wustl.edu/browser/?genome={assembly}&hub={datahub}".format(
                assembly=assembly,
                datahub=public_facing_url + datahub_file[1:]
            )

            result = {
                "gburl": result_url,
                "dhjson": datahub_file[1:],
                "file_mapping": mapping,
                "allzip": public_facing_url + working_dir[1:] + "all.zip"
            }

            calculation_end_time = time.time()
            calculation_time_cost = calculation_end_time - calculation_start_time

            self.output(2, "Worker-%s finished computing job (%s)" % (pid, task_id))

            time.sleep(10)
            res = {
                "id": task_id,
                "start time": calculation_start_time,
                "end time": calculation_end_time,
                "runtime": calculation_time_cost,
                "error": error,
                "result": result
            }

            self.output(2, "Job (%s): %s" % (task_id, res))

            result_queue.put(res)




if __name__ == '__main__':
    multiprocessing.freeze_support()

    browserhelper_app = EGH()
    browserhelper_app.find_config("browserhelper_aws.ini")
    browserhelper_app.start()




