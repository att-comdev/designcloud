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


class Deployment(Kubernetes):

    def __init__(self, **kwargs):

        host = kwargs.get("host", None)
        token = kwargs.get("token", None)
        super().__init__(token=token, host=host)
        self.deploy_conn = client.AppsV1Api(self.api_client)

    def get_deployments(self, **kwargs):

        namespace = kwargs.get("namespace", "default")
        label_selector = kwargs.get("label_selector", "")
        field_selector = kwargs.get("field_selector", "")
        deployment_list = []
        node_list = []
        deployments = self.deploy_conn.list_namespaced_deployment(
            namespace=namespace,
            label_selector=label_selector,
            field_selector=field_selector,
            watch=False)

        for deploy in deployments.items:
            if not deploy.metadata.deletion_timestamp:
                deployment_list.append({
                    'labels' : deploy.metadata.labels,
                    'name': deploy.metadata.name
                    })
                node_list.append(deploy.spec.template.spec.node_name)
        return deployment_list, set(node_list)


    def get_deployment_detail(self, **kwargs):

        name = kwargs.get("name", None)
        namespace = kwargs.get("namespace", "default")
        deployment = self.deploy_conn.read_namespaced_deployment(name, namespace)
        return deployment

    def create_deployment(self, **kwargs):

        namespace = kwargs.get("namespace", "default")
        deployment = self.deploy_conn.create_namespaced_deployment(namespace=namespace,
                                                  body=kwargs.get("body",
                                                                  None))
        return deployment

    def replace_deployment(self, **kwargs):
        namespace = kwargs.get("namespace", "default")
        deployment = self.deploy_conn.replace_namespaced_deployment(name=kwargs.get("name",""), namespace=namespace,
                                                  body=kwargs.get("body",
                                                                  None))
        return deployment

    def delete_deployment(self, **kwargs):

        name = kwargs.get("name", None)
        namespace = kwargs.get("namespace", None)
        body = client.V1DeleteOptions()
        del_deployment = self.deploy_conn.delete_namespaced_deployment(name, namespace,
            body=body)

