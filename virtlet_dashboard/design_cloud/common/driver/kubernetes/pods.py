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


class Pods(Kubernetes):

    def __init__(self, **kwargs):

        host = kwargs.get("host", None)
        token = kwargs.get("token", None)
        super().__init__(token=token, host=host)
        self.pod_conn = client.CoreV1Api(self.api_client)

    def get_pods(self, **kwargs):

        namespace = kwargs.get("namespace", "default")
        label_selector = kwargs.get("label_selector", "")
        field_selector = kwargs.get("field_selector", "")
        pod_list = []
        node_list = []
        pods = self.pod_conn.list_namespaced_pod(
            namespace=namespace,
            label_selector=label_selector,
            field_selector=field_selector,
            watch=False)

        for pod in pods.items:
            if not pod.metadata.deletion_timestamp:
                #pod_list.append(pod.metadata.labels)
                pod_list.append({
                    'labels' : pod.metadata.labels,
                    'name': pod.metadata.name
                    })
                node_list.append(pod.spec.node_name)
        return pod_list, list(set(node_list))

    def get_pod_detail(self, **kwargs):

        name = kwargs.get("name", None)
        namespace = kwargs.get("namespace", None)
        pod = self.pod_conn.read_namespaced_pod(name, namespace)
        return pod

    def create_pod(self, **kwargs):

        namespace = kwargs.get("namespace", "default")
        pod = self.pod_conn.create_namespaced_pod(namespace=namespace,
                                                  body=kwargs.get("body",
                                                                  None))
        return pod

    def delete_pod(self, **kwargs):

        name = kwargs.get("name", None)
        namespace = kwargs.get("namespace", None)
        body = client.V1DeleteOptions()
        del_pod = self.pod_conn.delete_namespaced_pod(name, namespace,
            body=body)

    def delete_pods(self, **kwargs):

        namespace = kwargs.get("namespace", None)
        label_selector = kwargs.get("label_selector", None)
        del_pods = self.pod_conn.delete_collection_namespaced_pod(
            namespace,
            label_selector=label_selector)

    def get_nodes(self, **kwargs):

        label_selector = kwargs.get("label_selector", None)
        field_selector = kwargs.get("field_selector", "")
        node_list = self.pod_conn.list_node(label_selector=label_selector,
                                            field_selector=field_selector)
        nodes = []
        for item in node_list.items:
            nodes.append(item.metadata.name)
        return nodes
