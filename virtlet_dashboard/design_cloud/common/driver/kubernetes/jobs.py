#!/usr/bin/python3

# Copyright 2017 AT&T Intellectual Property. All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from kubernetes import client

from .base import Kubernetes


class Jobs(Kubernetes):

    def __init__(self, **kwargs):

        host = kwargs.get("host", None)
        token = kwargs.get("token", None)
        super().__init__(token=token, host=host)
        self.job_conn = client.BatchV1Api(self.api_client)

    def create_job(self, **kwargs):

        namespace = kwargs.get("namespace", None)
        job = self.job_conn.create_namespaced_job(namespace=namespace,
                                                  body=kwargs.get("body",
                                                                  None))
        return job.metadata.name

    def get_jobs(self, **kwargs):

        namespace = kwargs.get("namespace", None)
        label_selector = kwargs.get("label_selector", None)
        jobs = self.job_conn.list_namespaced_job(namespace,
                                                 label_selector=label_selector)
        return jobs

    def get_job_detail(self, **kwargs):

        name = kwargs.get("name", None)
        namespace = kwargs.get("namespace", None)
        job = self.job_conn.read_namespaced_job(name, namespace)
        return job

    def delete_job(self, **kwargs):

        name = kwargs.get("name", None)
        namespace = kwargs.get("namespace", None)
        body = kwargs.get("body", client.V1DeleteOptions())
        body.propagation_policy = 'Background'
        del_job = self.job_conn.delete_namespaced_job(name, namespace,
                                                      body=body)

    def delete_jobs(self, **kwargs):

        namespace = kwargs.get("namespace", None)
        label_selector = kwargs.get("label_selector", None)
        del_jobs = self.job_conn.delete_collection_namespaced_job(
            namespace,
            label_selector=label_selector)

    def get_job_status(self, **kwargs):

        namespace = kwargs.get("namespace", None)
        name = kwargs.get("name", None)
        job_status = self.job_conn.read_namespaced_job_status(name,
                                                              namespace)
        return job_status
