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


class ConfigMap(Kubernetes):

    def __init__(self, **kwargs):

        host = kwargs.get("host", None)
        token = kwargs.get("token", None)
        super().__init__(token=token, host=host)
        self.config_conn = client.CoreV1Api(self.api_client)


    def create_configmap(self, **kwargs):

        namespace = kwargs.get("namespace", "default")
        config_map = self.config_conn.create_namespaced_config_map(namespace=namespace,
                                                  body=kwargs.get("body",
                                                                  None))
        return config_map
 
    def replace_configmap(self, **kwargs):

        namespace = kwargs.get("namespace", "default")
        name = kwargs.get("name", "default")
        config_map = self.config_conn.replace_namespaced_config_map(name=name,namespace=namespace,
                                                  body=kwargs.get("body",
                                                                  None))
        return config_map


    def get_config_detail(self, **kwargs):

        name = kwargs.get("name", None)
        namespace = kwargs.get("namespace", None)
        config_map = self.config_conn.read_namespaced_config_map(name, namespace)
        return config_map
