
from __future__ import print_function

import os
import re
import sys
import copy
import time
import json
import math
import flask
import werkzeug
import atexit
import hashlib
import random
import string
import shutil
import datetime
import multiprocessing
import multiprocessing.queues


try:
    # Python3 import
    import queue
except ImportError:
    # Python2 import
    import Queue as queue

try:
    import configparser
except ImportError:
    import ConfigParser as configparser



class APIErrorBase(RuntimeError):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class APIParameterError(APIErrorBase):
    pass


class APIUnfinishedError(APIErrorBase):
    pass



# For MacOS/Unix only...
class SharedCounter(object):

    def __init__(self, n=0):
        self.count = multiprocessing.Value('i', n)

    def increment(self, n=1):
        with self.count.get_lock():
            self.count.value += n

    @property
    def value(self):
        return self.count.value


class MacOSQueue(multiprocessing.queues.Queue):

    def __init__(self, *args, **kwargs):
        super(MacOSQueue, self).__init__(ctx=multiprocessing.get_context(), *args, **kwargs)
        self.size = SharedCounter(0)

    def put(self, *args, **kwargs):
        super(MacOSQueue, self).put(*args, **kwargs)

    def get(self, *args, **kwargs):
        res = super(MacOSQueue, self).get(*args, **kwargs)
        return res

    def qsize(self):
        return 1

    def empty(self):
        return False

    def clear(self):
        while not self.empty():
            self.get()

# Hmmm not the best implementation..
try:
    q = multiprocessing.Queue()
    q.qsize()
except NotImplementedError:
    multiprocessing.Queue = MacOSQueue


class APIFramework(object):

    def __init__(self):

        self._verbose_level = 100

        self._host = "localhost"
        self._port = 10980

        self._max_worker_num = 1
        self._clean_start = True
        self._file_based_job = False

        self._app_name = "testing"
        # self._flask_app = flask.Flask(self._app_name)

        self._input_file_folder = self.autopath("input")
        # self._output_file_folder = self.abspath("output")

        self._allowed_file_ext = ["txt", "doc", "docx", "pdf", "jpg", "png", "csv", "tsv", "bed", "qbed", "bedgraph", "bg"]
        self._allow_cors = True
        self._adhoc_cert = False

        self._expiration_period = False

        self._worker_para = {}

        self.result_cache = {}
        self.task_queue   = multiprocessing.Queue()
        self.status_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.flask_queue  = multiprocessing.Queue()
        self.request_suicide_queue = multiprocessing.Queue()
        self.approve_suicide_queue = multiprocessing.Queue()


        self._static_folder = None
        self._static_url = None

        self._template_folder = None
        self._home_html = None
        self._file_upload_finished_html = None

        self._status_saving_location = None

        self._worker_started = False
        self._last_worker_process_id = 0

        self._google_analytics_tag_id = ""



    # Proper APIs for changing config
    def host(self):
        return self._host

    def set_host(self, h):
        self._host = h

    def port(self):
        return self._port

    def set_port(self, p):
        if isinstance(p, int):
            self._port = p
        else:
            raise APIParameterError("Port number requires integer, %s is not acceptable")

    def max_worker_num(self):
        return self._max_worker_num

    def set_max_worker_num(self, w):
        self._max_worker_num = w

    def verbose_level(self):
        return self._verbose_level

    def set_verbose_level(self, v):
        assert isinstance(v, int)
        assert 0 <= v <= 100
        self._verbose_level = v

    def set_app_name(self, an):
        self._app_name = an

    def google_analytics_tag_id(self):
        return self._google_analytics_tag_id

    def set_google_analytics_tag_id(self, tag):
        assert type(tag) in [str, unicode]
        self._google_analytics_tag_id = tag

    def input_file_folder(self):
        return self._input_file_folder

    def set_input_file_folder(self, fp):
        self._input_file_folder = self.autopath(fp)

    def set_expiration_period(self, s):
        res = 0
        s = s.lower()
        try:
            res = float(s)
        except:
            res = 0
            v = float(s[:-1])
            unit = s[-1]
            if unit == "s":
                res = v
            elif unit == "m":
                res = v * 60
            elif unit == "h":
                res = v * 60 * 60
            elif unit == "d":
                res = v * 60 * 60 * 24

        self._expiration_period = res


    # set_status_saving_location

    # def output_file_folder(self):
    #     return self._output_file_folder

    # def set_output_file_folder(self, fp):
    #     self._output_file_folder = self.abspath(fp)

    def status_saving_location(self):
        return self._status_saving_location

    def set_status_saving_location(self, fp):
        self._status_saving_location = self.autopath(fp, newfile=True)

    def allowed_file_ext(self):
        return self._allowed_file_ext

    def clear_allowed_file_ext(self):
        self._allowed_file_ext = []

    def add_allowed_file_ext(self, ext):
        ext = ext.lower()
        if ext not in self._allowed_file_ext:
            self._allowed_file_ext.append(ext)

    def rm_allowed_file_ext(self, ext):
        ext = ext.lower()
        if ext in self._allowed_file_ext:
            self._allowed_file_ext.remove(ext)

    def output(self, lvl, msg):
        if lvl <= self.verbose_level():
            t = datetime.datetime.now()
            print("[%s %s %s] %s" % (t.strftime("%x"), t.strftime("%X"), lvl, msg), file=sys.stderr)


    def abspath(self, fp):
        # Getting things from current folder
        base = os.path.dirname(os.path.abspath(sys.argv[0]))
        res = os.path.join(base, fp)
        return res

    def datapath(self, fp):
        # Getting things from /data folder inside docker
        base = "/data"
        res = os.path.join(base, fp)
        return res

    def autopath(self, fp, newfile=False):
        res = self.abspath(fp)
        dtp = self.datapath(fp)

        if self.inside_docker():
            if os.path.exists(dtp) or newfile:
                res = dtp

        return res

    def bool(self, s):
        if s.lower() in ["y","yes","true",]:
            return True
        else:
            return False

    def inside_docker(self):
        inside_docker = False
        try:
            inside_docker = "docker" in open("/proc/self/cgroup").read()
        except:
            pass
        return inside_docker


    def find_config(self, config_file_name):

        inside_docker = self.inside_docker()

        config_current_path = self.abspath(config_file_name)
        config_docker_path  = "/data/" + config_file_name

        if inside_docker:
            if os.path.exists(config_docker_path):
                self.parse_config(config_docker_path)
            else:
                self.parse_config(config_current_path)

            self.environmental_variable()
        else:
            self.parse_config(config_current_path)

    def parse_config(self, config_file_name):

        config = configparser.ConfigParser()
        if hasattr(config,"read_file"):
            config.read_file(open(config_file_name))
        else:
            config.readfp(open(config_file_name))

        res = {}
        for each_section in config.sections():
            res[each_section] = {}
            for (each_key, each_val) in config.items(each_section):
                if each_val != "":
                    res[each_section][each_key] = each_val


        if "basic" in res:

            #for k,v in res["basic"].items():
            #    print("%s: |%s|" % (k,v))

            if "host" in res["basic"]:
                self.set_host(res["basic"]["host"])

            if "port" in res["basic"]:
                self.set_port(int(res["basic"]["port"]))

            if "max_cpu_core" in res["basic"]:
                self.set_max_worker_num(int(res["basic"]["max_cpu_core"]))

            if "clean_start" in res["basic"]:
                self._clean_start = self.bool(res["basic"]["clean_start"])

            if "file_based_job" in res["basic"]:
                self._file_based_job = self.bool(res["basic"]["file_based_job"])

            if "input_file_folder" in res["basic"]:
                self.set_input_file_folder(res["basic"]["input_file_folder"])

            # if "output_file_folder" in res["basic"]:
            #     self.set_output_file_folder(res["basic"]["output_file_folder"])

            if "status_saving_location" in res["basic"]:
                self.set_status_saving_location(res["basic"]["status_saving_location"])

            if "template_folder" in res["basic"]:
                self._template_folder = res["basic"]["template_folder"]

            if "static_folder" in res["basic"]:
                self._static_folder = res["basic"]["static_folder"]

            if "static_url" in res["basic"]:
                self._static_url = res["basic"]["static_url"]

            if "home_page" in res["basic"]:
                self._home_html = res["basic"]["home_page"]

            if "file_upload_finished_page" in res["basic"]:
                self._file_upload_finished_html = res["basic"]["file_upload_finished_page"]

            if "allowed_file_ext" in res["basic"]:
                allowed_file_ext = res["basic"]["allowed_file_ext"].split(",")
                self.clear_allowed_file_ext()
                for ext in allowed_file_ext:
                    ext = ext.strip()
                    self.add_allowed_file_ext(ext)

            if "allow_cors" in res["basic"]:
                self._allow_cors = self.bool(res["basic"]["allow_cors"])

            if "adhoc_cert" in res["basic"]:
                self._adhoc_cert = self.bool(res["basic"]["adhoc_cert"])

            if "expiration_period" in res["basic"]:
                self.set_expiration_period(res["basic"]["expiration_period"])

            if "google_analytics_tag_id" in res["basic"]:
                self.set_google_analytics_tag_id(res["basic"]["google_analytics_tag_id"])

            if "app_name" in res["basic"]:
                self.set_app_name(res["basic"]["app_name"])

                if res["basic"]["app_name"] in res:
                    self._worker_para = res[res["basic"]["app_name"]]


            #if "" in res["docker"]:
            #    self._xxxxx = res["docker"][""]

    def environmental_variable(self):

        if "WEBSERVICE_BASIC_HOST" in os.environ:
            self.set_host(os.environ["WEBSERVICE_BASIC_HOST"])

        if "WEBSERVICE_BASIC_PORT" in os.environ:
            self.set_port(int(os.environ["WEBSERVICE_BASIC_PORT"]))

        if "WEBSERVICE_BASIC_CPU_CORE" in os.environ:
            self.output(0, "Environment variable (WEBSERVICE_BASIC_CPU_CORE) is deprecated!")
            self.set_max_worker_num(int(os.environ["WEBSERVICE_BASIC_CPU_CORE"]))

        if "WEBSERVICE_BASIC_MAX_CPU_CORE" in os.environ:
            self.set_max_worker_num(int(os.environ["WEBSERVICE_BASIC_MAX_CPU_CORE"]))

        if "WEBSERVICE_BASIC_GOOGLE_ANALYTICS_TAG_ID" in os.environ:
            self.set_google_analytics_tag_id(os.environ["WEBSERVICE_BASIC_GOOGLE_ANALYTICS_TAG_ID"])

        for k, v in os.environ.items():
            if k.startswith("WEBSERVICE_APP_"):
                newk = k[15:].lower()

                self._worker_para[newk] = v


        return


    # Worker function
    def worker(self, pid, task_queue, status_queue, result_queue, params):
        # Params are key value pairs from configuration file, section app_name
        raise NotImplemented

    def flask_start(self, pid, task_queue, status_queue, result_queue, params):
        self.output(1, "FLASK service started at %s:%s" % (self.host(), self.port()) )

        if self._template_folder is None:
            tf = None
        else:
            tf = self.autopath(self._template_folder)

        if self._static_folder is None:
            sf = None
        else:
            sf = self.autopath(self._static_folder)

        if not self._clean_start and self.status_saving_location() != None:
            if os.path.exists(self.status_saving_location()):
                self.result_cache = json.load(open(self.status_saving_location()))


        flask_app = flask.Flask(self._app_name,
                                template_folder = tf,
                                static_folder   = sf,
                                static_url_path = self._static_url)

        self.load_route(flask_app)

        # flask_cors.CORS(flask_app)
        # flask_app.config['CORS_HEADERS'] = 'Content-Type'

        # ssl_context = "adhoc"
        kwarg = {}
        if self._adhoc_cert:
            kwarg["ssl_context"] = "adhoc"
        flask_app.run(self.host(), self.port(), False, **kwarg)

    # FLASK related functions starts here

    # FLASK handlers, need to be overwritten for your own app
    def home(self, **kwargs):
        if self._home_html is None:
            return flask.jsonify("Hello from %s:%s" % (self.host(), self.port()))
        else:
            return flask.render_template(self._home_html, **kwargs)

    def file_upload_finished_page(self, **kwargs):

        if self._file_upload_finished_html is None:
            return flask.jsonify("Not Implemented")
        else:
            return flask.render_template(self._file_upload_finished_html, **kwargs)

    def queue_length(self):
        self.update_results(getall=True)
        n = len(list(filter(lambda x: not x["finished"], self.result_cache.values())))

        response = flask.jsonify(n)
        return response

    @staticmethod
    def random_str(l=20):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(l))

    @staticmethod
    def str2hash(s):
        return hashlib.md5(s).hexdigest()

    _all_letters = string.ascii_uppercase + string.ascii_lowercase + string.digits
    def random_hash(self):
        return self.str2hash(''.join(random.choices(self._all_letters, k=10000)).encode("utf-8"))

    def submit(self):
        if flask.request.method in ['GET', 'POST']:
            p = self.api_para()
        else:
            response = flask.jsonify("METHOD %s is not suppoted" % flask.request.method)
            return response

        if "tasks" not in p and "task" not in p and "q" not in p:
            response = flask.jsonify("Please submit with actual tasks")
            return response

        if "tasks" in p:
            raw_tasks = json.loads(p["tasks"])
        elif "task" in p:
            raw_tasks = [json.loads(p["task"])]
        elif "q" in p:
            raw_tasks = json.loads(p["q"])


        developer_email = ""
        developer_email_valid = False
        if "developer_email" in p:
            developer_email = p["developer_email"].strip()
            email_valid = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
            developer_email_valid = bool(email_valid.match(developer_email))
        else:
            self.output(1, "No email address is provided for task(%s)" % raw_tasks)
            response = flask.jsonify("Please provide your E-mail address. Use developer_email field.")
            return response

        if not developer_email_valid:
            self.output(1, "Invalid email(%s) for task(%s)" % (developer_email, raw_tasks))
            response = flask.jsonify("Please provide valid E-mail address")
            return response

        userid = self.str2hash(developer_email.encode("utf8"))[:20]


        res = []
        for raw_task in raw_tasks:
            task_detail = self.form_task(raw_task)

            if "id" not in task_detail:
                raise APIParameterError(
                    "No id provided for your job(%s), probably check the form_task method"
                    % task_detail)


            returned_task_detail = copy.deepcopy(task_detail)

            res.append(returned_task_detail)

            if "error" in returned_task_detail:
                del returned_task_detail["id"]
                continue
            else:
                returned_task_detail["id"] = returned_task_detail["id"] + userid

            task_id = task_detail["id"]
            status = {
                "id": task_id,
                "initial_user_id": userid,
                "submission_original": raw_task,
                "submission_detail": task_detail,
                "finished": False,
                "stat": {},
                "result": {}
            }

            if task_id in self.result_cache:
                pass
            else:
                self.task_queue.put(task_detail)
                self.result_cache[task_id] = status
            self.output(1, "Job received by API: %s" % (task_detail))

        response = flask.jsonify(res)
        return response


    def retrieve(self):
        if flask.request.method in ['GET', 'POST']:
            p = self.api_para()
        else:
            response = flask.jsonify("METHOD %s is not suppoted" % flask.request.method)
            return response

        if "list_ids" not in p and \
                "task_ids" not in p and \
                "list_id" not in p and \
                "task_id" not in p:
            return flask.jsonify("Please provide with list_id(s)")

        if "list_ids" in p:
            task_ids = json.loads(p["list_ids"])
        elif "list_id" in p:
            task_ids = [str(p["list_id"])]

        elif "task_ids" in p:
            task_ids = json.loads(p["task_ids"])
        elif "task_id" in p:
            task_ids = [str(p["task_id"])]


        timeout = 0
        if "timeout" in p:
            try:
                timeout = float(p["timeout"])
                if timeout < 0:
                    timeout = -timeout
                if timeout > 10:
                    timeout = 10
            except:
                pass


        res = []
        query_start_timestamp = time.time()
        for query_round in range(30):
            res = []
            got_all = True
            self.update_results(getall=True)

            for tmp in task_ids:
                # Assume MD5
                task_id = tmp[:32]
                user_id = tmp[32:]

                if task_id in self.result_cache:
                    r = copy.deepcopy(self.result_cache[task_id])
                else:
                    res.append({"error": "task_id (%s) not found" % task_id})
                    continue

                cached = True
                if r["finished"]:
                    r["stat"]["cached"] = cached
                else:
                    got_all = False

                r["task"] = r["submission_detail"]

                del r["submission_original"]
                del r["submission_detail"]

                r["id"] = tmp
                r["task"]["id"] = tmp

                try:
                    del r["stat"]["start time"]
                    del r["stat"]["end time"]
                except:
                    pass

                res.append(r)


            if time.time() - query_start_timestamp > timeout:
                break
            if got_all:
                break
            time.sleep(0.5)


        response = flask.jsonify(res)
        self.output(1, "Retrieve json: %s" % res)
        return response


    def upload_file(self):
        if flask.request.method == 'POST':

            if 'file' not in flask.request.files:
                return flask.abort(400)

            files = flask.request.files.getlist("file")

            task_id = self.random_hash()

            p = self.api_para()
            print(p)

            assembly = "hg38"
            if "assembly" in p:
                assembly = p["assembly"]
            pre_defined_file_format = {}


            file_name_mapping = {}
            for file in files:
                filename = werkzeug.utils.secure_filename(file.filename)
                hashfilename = self.str2hash(''.join(random.choices(string.ascii_uppercase + string.digits, k=1000)).encode("utf-8"))

                if filename in p:
                    pre_defined_file_format[filename] = p[filename]

                file_name_mapping[filename] = hashfilename

                task_folder = "./task/%s/input" % (task_id)
                os.makedirs(task_folder, exist_ok=True)
                os.makedirs(task_folder.replace("input", "output"), exist_ok=True)
                tmp_filename = "./%s/%s" % (task_folder, hashfilename)
                file.save(tmp_filename)

                if file.filename == '':
                    response = flask.jsonify('No selected file')
                    return response


            task_detail = {
                "id": task_id,
                "file_mapping": file_name_mapping,
                "assembly": assembly,
                "pre_defined_file_format": pre_defined_file_format,
            }

            status = {
                "id": task_id,
                "submission_original": {},
                "submission_detail": task_detail,
                "finished": False,
                "stat": {},
                "status": {"started": False},
                "result": {}
            }

            if task_id in self.result_cache:
                pass
            else:
                self.task_queue.put(task_detail)
                self.result_cache[task_id] = status
            self.output(1, "Job received by API: %s" % (task_detail))

        return task_id


    def download_file(self):
        if flask.request.method in ['GET', 'POST']:
            p = self.api_para()
        else:
            response = flask.jsonify("METHOD %s is not suppoted" % flask.request.method)

            return response


        if "list_id" not in p:
            response = flask.jsonify("Please provide with list_id(s)")

            return response

        list_id = p["list_id"]

        if not self.result_cache[list_id]["finished"]:
            response = flask.jsonify("The computation haven't finished yet")

            return response

        target_file_path = self.result_cache[list_id]["result"]["output_file_abs_path"]

        download_file_name = target_file_path
        if "rename" in self.result_cache[list_id]["result"]:
            download_file_name = self.result_cache[list_id]["result"]["rename"]

        download_option = {}
        if "flask_download_option" in self.result_cache[list_id]["result"]:
            download_option = self.result_cache[list_id]["result"]["flask_download_option"]

        try:
            return flask.send_file(target_file_path,
                                   attachment_filename=download_file_name,
                                   **download_option)
        except:
            flask.abort(404)


    # FLASK helper functions
    def form_task(self, params):
        task = {}
        task_str = ""
        for par in self.task_params:
            if par in params:
                task[par] = params[par].strip()
            elif self.task_params[par] != None:
                task[par] = self.task_params[par].strip()
            task_str += "_" + task[par]
        task["id"] = self.str2hash(task_str.encode("utf-8"))
        return task

    # @staticmethod
    def api_para(self):
        if flask.request.method == "GET":
            return flask.request.args
        elif flask.request.method == "POST":
            return flask.request.form
        else:
            raise APIErrorBase


    def result_cache_clear(self):
        # result_cache lives with FLASK process, so simple result_cache = {} in main process doen't work
        try:
            res = self.flask_queue.get_nowait()
            l = len(self.result_cache)
            self.result_cache = {}
            self.output(1, "Clear result cache, previously stored %s record(s)" % l)
        except queue.Empty:
            pass

    def update_results(self, getall=True):

        dump = False
        i = 0
        while True:

            i += 1

            try:
                res = self.result_queue.get_nowait()

                self.result_cache[res["id"]]["stat"] = {
                    "start time": res["start time"],
                    "end time": res["end time"],
                    "runtime": res["runtime"]
                }

                self.result_cache[res["id"]]["error"] = res["error"]
                self.result_cache[res["id"]]["result"] = res["result"]

                self.result_cache[res["id"]]['finished'] = True

                dump = True
            except queue.Empty:
                break
            except KeyError:
                self.output(1, "Job ID %s is not present" % res["id"])

        while True:
            try:
                status = self.status_queue.get_nowait()
                task_id = status["id"]
                del status["id"]
                self.result_cache[task_id]["status"] = status

                dump = True
            except queue.Empty:
                break


        if dump:
            self.dump_status()

        if isinstance(self._expiration_period, int):
            if self._expiration_period > 0:
                self.delete_outdated_files()

    def delete_outdated_files(self):
        # print("Deleting Check")
        for task_id in list(self.result_cache.keys()):
            detail = self.result_cache[task_id]
            if "stat" in detail:
                stat = detail["stat"]
                if "start time" in stat:
                    start_ts = stat["start time"]
                    passed = time.time() - start_ts

                    if passed > self._expiration_period:
                        message = "Task(%s) was created at %0.1fs, %0.1fs has paseed since then, deleted because of task expires after %0.1fs" % (task_id, start_ts, passed, self._expiration_period)
                        self.output(0, message)

                        del self.result_cache[task_id]
                        try:
                            shutil.rmtree("./task/%s" % task_id, )
                        except:
                            pass
        return

    def allow_file_ext(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_file_ext()

    def status(self):
        response = flask.jsonify(True)
        return response


    # Load route and handler to flask app
    def load_route(self, app):

        app.add_url_rule("/status", "status", self.status, methods=["GET", "POST"])
        # app.add_url_rule("/queue_length", "queue_length", self.queue_length, methods=["GET", "POST"])
        app.add_url_rule("/retrieve", "retrieve", self.retrieve, methods=["GET", "POST"])
        if self._file_based_job:
            app.add_url_rule("/file_upload", "upload_file", self.upload_file, methods=["GET", "POST"])
            app.add_url_rule("/file_download", "download_file", self.download_file, methods=["GET", "POST"])
        else:
            app.add_url_rule("/submit", "submit", self.submit, methods=["GET", "POST"])


        @app.after_request
        def cors(response):
            # http://epigenomegateway.wustl.edu
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', '*')
            response.headers.add('Access-Control-Allow-Private-Network', "true")
            response.headers.add('Vary', "*")

            return response


        self.load_modular_front_end(app)
        self.load_additional_route(app)


    def load_modular_front_end(self, app):
        app.add_url_rule("/", "home", self.home, methods=["GET", "POST"])
        return

    def load_additional_route(self, app):
        return

    def manipulate_dirs(self):
        if self._file_based_job:
            if not os.path.exists(self.input_file_folder()):
                os.makedirs(self.input_file_folder())
            """
            if not os.path.exists(self.output_file_folder()):
                os.makedirs(self.output_file_folder())
    
            if self._clean_start:
                for folder in [self.input_file_folder(), self.output_file_folder()]:
                    for fn in os.listdir(folder):
                        # Clean up the input and output folder
                        fp = os.path.join(folder, fn)
                        os.remove(fp)
            """
        return


    def pre_start(self, worker_para):
        # Function for downloading necessary data and others.
        # Execute before everything else starts
        return None


    def start(self):

        self.output(0, "Host: %s" % self._host)
        self.output(0, "Port: %s" % self._port)
        self.output(0, "Max_Worker_Num: %s" % self._max_worker_num)

        for k,v in self._worker_para.items():
            self.output(0, "%s(worker para): %s" % (k,v))

        flask_process = multiprocessing.Process(target=self.flask_start, args=(0, self.task_queue, self.status_queue, self.result_queue, self._worker_para))
        flask_process.start()

        self._worker_started = True
        self.manipulate_dirs()

        if not self._clean_start and self.status_saving_location() != None:
            if os.path.exists(self.status_saving_location()):
                self.result_cache = json.load(open(self.status_saving_location()))

        self.output(0, "Starting workers")
        self._deamon_process_pool = self.new_worker_processes()

        if self._clean_start:

            self.output(0, "Downloading necessary data... please wait")
            self.pre_start(self._worker_para)
            self.output(0, "Download phase finished")

            self.flask_queue.put("CLEAR")

            self.output(0, "Terminating previous workers with outdated data")
            self.terminate_all()

            self.output(0, "Starting workers with updated data")
            self._deamon_process_pool = self.new_worker_processes()
        else:
            pass


        self.monitor()

    def new_worker_process(self):

        self._last_worker_process_id += 1
        pid = self._last_worker_process_id

        suicide_queue = [
            self.request_suicide_queue,
            self.approve_suicide_queue
        ]
        suicide_queue = []

        proc = multiprocessing.Process(
            target=self.worker,
            args=(pid, self.task_queue, self.status_queue, self.result_queue, suicide_queue, self._worker_para)
        )

        proc.start()

        self.output(0, "Worker-%s is created" % (pid))

        return pid, proc

    def new_worker_processes(self):

        process_pool = {}
        for i in range(self._max_worker_num):
            pid, proc = self.new_worker_process()
            process_pool[pid] = proc

        return process_pool

    def task_queue_get(self, task_queue, pid, suicide_queue):

        i = 0
        counter = 0
        next_report = 600
        while True:
            counter += 1
            i += 1

            try:
                task_detail = task_queue.get_nowait()
                # task_detail = task_queue.get_nowait(block=True)
                return task_detail
            except queue.Empty:
                time.sleep(1)


    def deamon_process_pool_update(self):

        for pid, proc in list(self._deamon_process_pool.items()):

            if not proc.is_alive():
                self.output(0, "Worker-%s was terminated for some reasons... Please check the log for more info" % (pid))
                del self._deamon_process_pool[pid]

        return

    def monitor(self):
        self.cleanup()

        while True:
            time.sleep(10)

            unfinished_job_count = self.task_queue.qsize()

            self.deamon_process_pool_update()

            require_new_worker = False
            if len(self._deamon_process_pool) < self.max_worker_num():
                require_new_worker = True

            if require_new_worker:

                self.output(0, "Need more worker...")
                new_pid, new_proc = self.new_worker_process()
                self._deamon_process_pool[new_pid] = new_proc



    def cleanup(self):
        atexit.register(self.terminate_all)
        # atexit.register(self.dump_status)


    def terminate_all(self):
        for i, p in list(self._deamon_process_pool.items()):
            self.output(0, "Worker-%s is terminated" % (i))
            p.terminate()
            del self._deamon_process_pool[i]

    def dump_status(self):
        if self.status_saving_location() != None:
            useful_result = {}
            for task_id, task in self.result_cache.items():
                if task["finished"]:
                    useful_result[task_id] = task

            json.dump(
                useful_result,
                open(self.status_saving_location(), "w"),
                indent=2
            )


class APIFrameworkWithFrontEnd(APIFramework):

    def load_modular_front_end(self, app):

        self.data_folder = "./image"

        google_tracking_js = ""
        if self.google_analytics_tag_id() not in [None, ""]:
            google_tracking_js = self.google_analytics_script()

        kwarg = {
            "app_name": self._app_name,
            "app_name_lower": self._app_name.lower(),
            "google_analytics_html": google_tracking_js
        }

        # TODO better routing management

        @app.route('/', methods=["GET", "POST"])
        def home():
            return flask.render_template(self._home_html, **kwarg)

        @app.route('/header', methods=["GET", "POST"])
        def header():
            return flask.render_template("./header.html", **kwarg)

        @app.route('/footer', methods=["GET", "POST"])
        def footer():
            return flask.render_template("./footer.html", **kwarg)

        @app.route('/renderer.js', methods=["GET", "POST"])
        def renderer():
            return open("./htmls/renderer.js").read()

        @app.route('/loader.gif', methods=["GET", "POST"])
        def loaderimgxxfjkslafjlka():
            return flask.send_file("./htmls/loader.gif")

        @app.route('/task/<path:path>',
                   methods=['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH'],
                   )
        def static_file1(path):
            p = "./task/" + path
            return flask.send_file(p, conditional=True, as_attachment=True,)


    def google_analytics_script(self):
        tag = self.google_analytics_tag_id()
        res = """""" % (tag, tag)
        return res


if __name__ == '__main__':
    multiprocessing.freeze_support()



