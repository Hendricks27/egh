

import os
import re
import sys
import json
import time
import requests

class BrowserHelperClient(object):
    _base_url_protocol = "https"
    _base_url_host = "10.20.127.22"
    _base_url_port = 10981
    _base_url = ""

    def __int__(self):
        self._base_url = self.make_url()

    def update_url(self):
        self._base_url = self.make_url()

    def make_url(self):
        port = ":%s" % self._base_url_port
        if self._base_url_port in ["22", 22]:
            port = ""
        url = "{protocol}://{host}{port}".format(
            protocol=self._base_url_protocol, host=self._base_url_host, port=port
        )
        return url

    def set_base_url_protocol(self, x):
        self._base_url_protocol = x
        self.update_url()

    def set_base_url_host(self, x):
        self._base_url_host = x
        self.update_url()

    def set_base_url_port(self, x):
        self._base_url_port = x
        self.update_url()

    def submit(self, input_files):
        files = []
        for file_name, file_path in input_files.items():
            files.append(("file", (file_name, open(file_path).read())))

        surl = self._base_url + "/file_upload"
        response = requests.post(surl, files=files, verify=False)

        assert response.status_code == 200
        reshtml = response.text
        p1 = re.compile(r'<div id=\"list_id\" data-list_id=\"(.*)\"></div>')
        task_id = p1.findall(reshtml)[0]
        return task_id

    def retrieve_simple(self, task_id):
        surl = self._base_url + "/retrieve?list_id=" + task_id
        response = requests.get(surl, verify=False)
        res = json.loads(response.text)[0]
        # print(res)
        return res

    def retrieve(self, task_id):
        while True:
            res = self.retrieve_simple(task_id)
            if res["finished"]:
                break
            time.sleep(1)
        return res

    def gburl(self, server_result):
        return server_result["result"]["gburl"]

    def simple_request(self, input_files):

        task_id = self.submit(input_files)
        result_json = self.retrieve(task_id)
        gburl = self.gburl(result_json)
        return gburl


if __name__ == "__main__":

    bhc = BrowserHelperClient()

    if True:
        bhc.set_base_url_host("localhost")
        bhc.set_base_url_port("10981")
        bhc.set_base_url_protocol("https")

    burl = bhc.make_url()
    print(burl)

    files = {
        "testx.bed": "./test.bed",
        # "testy.bedgraph": "./test.bedgraph",
        "testz.qbed": "./test.qbed"
    }

    gburl = bhc.simple_request(files)
    print(gburl)













