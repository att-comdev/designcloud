from flask import Blueprint, request,session, render_template,redirect, url_for
from flask_paginate import Pagination, get_page_parameter

from common.driver.kubernetes.pods import Pods
from common.driver.kubernetes.deployment import Deployment
from common.driver.kubernetes.service import Service
import sqlite3, math, subprocess, json, datetime
import os


DATABASE = os.path.join('./design_cloud/db/credentials.db')

vms = Blueprint('vms', __name__)

def get_token():
    token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6InJlc2lsaWVuY3ktdG9rZW4tamNxNHgiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoicmVzaWxpZW5jeSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjRiZDY1NThlLWFmOTEtMTFlOS1iYTA5LTFjOThlYzEyM2I2OCIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OnJlc2lsaWVuY3kifQ.g7xUIBoETs7PBwWGSMK3qXQs5FunGxCbyLYow7uinjjx3zSyK9zPC2z-PuIZX2k8nYWMy3taOIhpTluXJApZUsDH8ChyTSeBEX-PA8l4iM15L8Vb18XszgLfsSvzlWWU1P4hsr6QAlPKiCqTZtw-kPwT-v1LWICPhUu67F3lnJnMAvDGVHX_NewzNcBrJm7zHeIovtZs4iCgS_aV7Qy_DRL2CyAeO-o2T9CkOZQ2On0EdRq83kCqYy0wWZ0bB3XTi2TgQzrg1RFZWFLyU_4fd8ALnO1VzSTZfR6uiSeCC3IL4GNqdMprfKxrqR4c2ujiZ1QWUP6s01P08bmNnfvRig"
    return token


def get_conn(resource_type):

    conn = None
    server = "https://135.21.35.18:6443"
    token = get_token()
    if resource_type == 'pod':
        conn = Pods(token=token, host=server)
    elif resource_type == 'deployment':
        conn = Deployment(token=token, host=server)
    elif resource_type == 'svc':
        conn = Service(token=token, host=server)

    return conn


def get_users(username):
    conn = sqlite3.connect(DATABASE)
    cursor_obj = conn.cursor()
    k = cursor_obj.execute('SELECT * FROM users WHERE username="{}"'.format(username))
    user = k.fetchone()
    conn.close()
    return user


def set_value(user=''):
    global CURRENT_USER
    if user:
        session['user'] = user
        CURRENT_USER = user
    elif session['user']:
        CURRENT_USER = session['user']
    return CURRENT_USER



@vms.route('/list_vms', methods=['GET'])
def index():

    page = request.args.get(get_page_parameter(), type=int, default=1)   
    itemsPerPage = 10

    if 'user' not in session:
        return redirect(url_for('login'))


    pod_conn = get_conn('pod')
    svc_conn = get_conn('svc')
    deploy_conn = get_conn('deployment')
    user = get_users(set_value())

    if user[2] == 'admin':
        deployments_and_nodes = deploy_conn.get_deployments(namespace='default', label_selector='virtlet=enabled')
        pods_and_nodes = pod_conn.get_pods(namespace='default', label_selector='virtlet=enabled')
    else:
        username = user[0].lower()
        deployments_and_nodes = deploy_conn.get_deployments(namespace='default',
            label_selector='created-by={}'.format(username))
        pods_and_nodes = pod_conn.get_pods(namespace='default',
            label_selector='created-by={}'.format(username))

    vm_list = []
    vm_count = 1
    #total_detail_dict = {}

    for i in pods_and_nodes[0]:
        try:
            svc = svc_conn.get_service_detail(name=i["name"], namespace="default")
        except Exception as var:
            continue

        #deploy_spec = deploy_conn.get_deployment_detail(name=i["name"], namespace="default")
        pod_spec = pod_conn.get_pod_detail(name=i["name"], namespace="default")
        #disk_size = deploy_spec.spec.template.metadata.annotations.get('VirtletRootVolumeSize')
        disk_size = pod_spec.metadata.annotations.get('VirtletRootVolumeSize')
        #vcpus= deploy_spec.spec.template.metadata.annotations.get('VirtletVCPUCount')
        vcpus= pod_spec.metadata.annotations.get('VirtletVCPUCount')
        #ram = deploy_spec.spec.template.spec.containers[0].resources.limits.get('memory')
        ram = pod_spec.spec.containers[0].resources.requests.get('memory')
        #replicas_count = deploy_spec.status.ready_replicas
        #status = "Running" if replicas_count == 1 else "Pending"
        status = pod_spec.status.phase
        creation_time = pod_spec.metadata.creation_timestamp
        running_time = datetime.datetime.now(tz=datetime.timezone.utc) - creation_time

        try:
            vm_name = svc.spec.selector.get('login-name')
            vm_name = vm_name.lower()
        except Exception as var:
            vm_name = 'testuser'

        try:
            external_ip = svc.status.load_balancer.ingress[0].ip
        except Exception as var:
            continue
        #Flask doesnt support '-' in dict key names. 
        # A hack to get the username
        i['labels'] = {key.replace('-','_'): val for key,val in i['labels'].items()}
        login_username = 'testuser'
        if 'created_by' in i['labels'].keys():
            login_username = i['labels']['created_by'] 

        login_command = "ssh {0}@{1}".format(login_username,external_ip)

        vm_details = {
           "vm_name": i["name"],
	   "login_command": login_command,
	   "vm_count": vm_count,
           "disk_size": disk_size,
           "vcpus": vcpus,
           "ram": ram,
           "status" : status,
           "running_since":"{0} days, {1} hours".format(running_time.days, int(running_time.seconds/60/60)),
	}
 
        vm_list.append(vm_details)
        vm_count += 1
    

    for i in deployments_and_nodes[0]:
        try:
            svc = svc_conn.get_service_detail(name=i["name"], namespace="default")
        except Exception as var:
            continue

        deploy_spec = deploy_conn.get_deployment_detail(name=i["name"], namespace="default")
        #pod_spec = pod_conn.get_pod_detail(name=i["name"], namespace="default")
        disk_size = deploy_spec.spec.template.metadata.annotations.get('VirtletRootVolumeSize')
        #disk_size = pod_spec.metadata.annotations.get('VirtletRootVolumeSize')
        vcpus= deploy_spec.spec.template.metadata.annotations.get('VirtletVCPUCount')
        #vcpus= pod_spec.metadata.annotations.get('VirtletVCPUCount')
        ram = deploy_spec.spec.template.spec.containers[0].resources.limits.get('memory')
        #ram = pod_spec.spec.containers[0].resources.requests.get('memory')
        replicas_count = deploy_spec.status.ready_replicas
        status = "Running" if replicas_count == 1 else "Pending"
        #status = pod_spec.status.phase
        creation_time = deploy_spec.metadata.creation_timestamp
        running_time = datetime.datetime.now(tz=datetime.timezone.utc) - creation_time

        try:
            vm_name = svc.spec.selector.get('login-name')
            vm_name = vm_name.lower()
        except Exception as var:
            vm_name = 'testuser'

        try:
            external_ip = svc.status.load_balancer.ingress[0].ip
        except Exception as var:
            continue
        #Flask doesnt support '-' in dict key names. 
        # A hack to get the username
        i['labels'] = {key.replace('-','_'): val for key,val in i['labels'].items()}
        login_username = 'testuser'
        if 'created_by' in i['labels'].keys():
            login_username = i['labels']['created_by']

        login_command = "ssh {0}@{1}".format(login_username,external_ip)
        vm_details = {
           "vm_name": i["name"],
           "login_command": login_command,
           "vm_count": vm_count,
           "disk_size": disk_size,
           "vcpus": vcpus,
           "ram": ram,
           "status" : status,
           "running_since":"{0} days, {1} hours".format(running_time.days, int(running_time.seconds/60/60)),
        }

        vm_list.append(vm_details)
        vm_count += 1

    pagination = Pagination(page=page, total=len(vm_list), record_name='vms', per_page=itemsPerPage, bs_version=4)
    endIndex = page * itemsPerPage -1
    startIndex = endIndex - itemsPerPage + 1
    total = len(vm_list)
    totalPage = range(1,math.ceil(total / itemsPerPage) + 1)
    vm_list = vm_list[startIndex:endIndex+1]


    return render_template('vms.html',
                           vm_list=vm_list,
                           pagination=pagination,
                           username=session['id_token']['email']
                           )

