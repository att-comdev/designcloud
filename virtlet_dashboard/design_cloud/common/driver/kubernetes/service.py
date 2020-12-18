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


class Service(Kubernetes):

    def __init__(self, **kwargs):

        host = kwargs.get("host", None)
        token = kwargs.get("token", None)
        super().__init__(token=token, host=host)
        self.svc_conn = client.CoreV1Api(self.api_client)

    def get_services(self, **kwargs):

        namespace = kwargs.get("namespace", "defaul")
        label_selector = kwargs.get("label_selector", "")
        field_selector = kwargs.get("field_selector", "")
        svc = self.svc_conn.list_namespaced_service(
            namespace=namespace,
            label_selector=label_selector,
            field_selector=field_selector,
            watch=False)
        return svc

    def get_service_detail(self, **kwargs):

        name = kwargs.get("name", None)
        namespace = kwargs.get("namespace", None)
        svc = self.svc_conn.read_namespaced_service(name, namespace)
        return svc

    def create_service(self, **kwargs):

        namespace = kwargs.get("namespace", "default")
        svc = self.svc_conn.create_namespaced_service(namespace=namespace,
                                                  body=kwargs.get("body",
                                                                  None))
        return svc

    def delete_service(self, **kwargs):

        name = kwargs.get("name", None)
        namespace = kwargs.get("namespace", None)
        body = client.V1DeleteOptions()
        del_svc = self.svc_conn.delete_namespaced_service(name, namespace,
            body=body)
