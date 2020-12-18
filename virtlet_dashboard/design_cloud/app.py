import json, datetime, os, yaml, math, flask, subprocess, time, random, string, re
from flask import Flask, render_template, request, redirect, url_for, session,jsonify
from jinja2 import Environment, FileSystemLoader


from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata, ProviderMetadata
from flask_pyoidc.user_session import UserSession
from flask_pyoidc.flask_pyoidc import OIDCAuthentication


from common.driver.kubernetes.pods import Pods
from common.driver.kubernetes.deployment import Deployment
from common.driver.kubernetes.service import Service
from common.driver.kubernetes.configmap import ConfigMap
from common.driver.database.sqlite import Sqlite
from views.vms import vms

from dotenv import load_dotenv


import sqlite3
from flask import g


  # refers to application_top
dotenv_path = os.path.join('./.env')
load_dotenv(dotenv_path)

DATABASE = os.path.join('./design_cloud/db/credentials.db')
print(DATABASE)
app = Flask(__name__, template_folder='templates')
app.config.from_object(__name__)
app.config.update({
  'SERVER_NAME': os.getenv('DOMAIN_NAME'),
  'OIDC_REDIRECT_ENDPOINT': 'login_callback',
  'SECRET_KEY': '10a0b3e6c650868ec7e16693be9b71de',
  'PERMANENT_SESSION_LIFETIME': datetime.timedelta(days = 7).total_seconds(),
  'PREFERRED_URL_SCHEME': os.getenv('PREFERRED_URL_SCHEME'),
  'DEBUG': True
})

client_metadata = ClientMetadata(client_id = os.getenv('DEX_CLIENT_ID'), client_secret = os.getenv('DEX_CLIENT_SECRET'))

auth_params = {
  'scope': ['openid', 'email', 'offline_access']
}
config = ProviderConfiguration(issuer = 'https://dex.example.com:32000', client_metadata = client_metadata, auth_request_params = auth_params)

auth = OIDCAuthentication({
  'default': config
}, app)

app.secret_key = '10a0b3e6c650868ec7e16693be9b71de'

app.register_blueprint(vms)


def get_token():
    token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6InJlc2lsaWVuY3ktdG9rZW4tamNxNHgiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoicmVzaWxpZW5jeSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjRiZDY1NThlLWFmOTEtMTFlOS1iYTA5LTFjOThlYzEyM2I2OCIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OnJlc2lsaWVuY3kifQ.g7xUIBoETs7PBwWGSMK3qXQs5FunGxCbyLYow7uinjjx3zSyK9zPC2z-PuIZX2k8nYWMy3taOIhpTluXJApZUsDH8ChyTSeBEX-PA8l4iM15L8Vb18XszgLfsSvzlWWU1P4hsr6QAlPKiCqTZtw-kPwT-v1LWICPhUu67F3lnJnMAvDGVHX_NewzNcBrJm7zHeIovtZs4iCgS_aV7Qy_DRL2CyAeO-o2T9CkOZQ2On0EdRq83kCqYy0wWZ0bB3XTi2TgQzrg1RFZWFLyU_4fd8ALnO1VzSTZfR6uiSeCC3IL4GNqdMprfKxrqR4c2ujiZ1QWUP6s01P08bmNnfvRig"
    return token

def get_users(username):
    conn = sqlite3.connect(DATABASE)
    cursor_obj = conn.cursor()
    k = cursor_obj.execute('SELECT * FROM users WHERE username="{}"'.format(username))
    user = k.fetchone()
    conn.close()
    return user


def get_conn(resource_type):

    conn = None
    server = "https://185.11.35.18:6443"
    token = get_token()
    if resource_type == 'pod':
        conn = Pods(token=token, host=server)
    elif resource_type == 'deployment':
        conn = Deployment(token=token, host=server)
    elif resource_type == 'svc':
        conn = Service(token=token, host=server)
    elif resource_type == 'cm':
        conn = ConfigMap(token=token, host=server)

    return conn


def set_value(user=''):
    global CURRENT_USER
    if user:
        session['user'] = user
        CURRENT_USER = user
    elif session['user']:
        CURRENT_USER = session['user']
    return CURRENT_USER


@app.route('/create_vm', methods=['GET', 'POST'])
def create_vm():
    db_conn = Sqlite(db_file=DATABASE)

    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    user_row = db_conn.get_user(username=username)

    if request.method == 'GET':

        if user_row[2] == 'admin':
            return render_template('create_vm.html',
                                   user_type = 'admin',
                                   msg = '', 
                                  )

        return render_template('create_vm.html',
                                user_type = 'normal_user',
                                msg = '',
                               )

    svc_conn = get_conn('svc')
    pod_conn = get_conn('pod')
    cm_conn = get_conn('cm')
    deploy_conn = get_conn('deployment')

    if request.method == 'POST':
        virtlet_params = request.form
        allowed_ram = 80 if user_row[2] == 'admin' else 32

        if int(virtlet_params['ram']) > allowed_ram:
            return render_template('create_vm.html',
                                   user_type = user_row[2],
                                   msg = 'Allowed range for RAM is {0} GB'.format(allowed_ram),
                                  )

        cm_response = cm_conn.get_config_detail(name='resource-config', namespace='default')
        res_dict = cm_response.data
        user = get_users(set_value())
        used_disk, used_vcpu, used_ram = re.findall('\d+', res_dict[user[0]])

        if int(used_disk) > 500 or int(used_vcpu) > 40 or int(used_ram) > 50:
            return render_template('create_vm.html',
                                   user_type = 'admin',
                                   msg = 'You have exceeded your limit of 500Gb disk,50Gb ram and 40vcpus.',
                                  )
        ram = str(int(virtlet_params['ram']) * 1024)
        template_dir = "/app/design_cloud/templates"
        templateLoader = FileSystemLoader(searchpath=template_dir)
        ENV = Environment(loader=templateLoader, trim_blocks=True,
                          lstrip_blocks=True)
        svc_template = ENV.get_template("svc_template.j2")
        deploy_template = ENV.get_template("deployment_template.j2")

        if virtlet_params.get("user_name"):
            user_name = virtlet_params.get("user_name")
        else:
            user = get_users(set_value())
            user_name = user[0]

        for i in range(0, int(virtlet_params['count'])):
            random_text = ''.join(random.choice(string.ascii_lowercase + string.digits + string.ascii_lowercase) for _ in range(5))
            render_deploy = deploy_template.render(vcpu=virtlet_params['vcpu'],
                                         ram=ram,
                                         ssh_key=virtlet_params['ssh_key'],
                                         disk=virtlet_params['disk'],
                                         image=virtlet_params['image'],
                                         vm_name= "{0}-{1}".format(virtlet_params['vm_name'].lower(),random_text),
                                         creator_name=user_name.lower(),
                                         login_name=user_name.lower(),
                                         rack_detail = ''
                                        )
            deploy_response = deploy_conn.create_deployment(namespace='default',
                                               body=yaml.load(render_deploy))
            vm_name = deploy_response.metadata.name
            time.sleep(2)
            pod_response = pod_conn.get_pods(namespace='default',label_selector='vm={0}'.format(vm_name))
            rack_name = pod_response[1][0]
            #rack_name = deploy_response.spec.template.spec.node_name
            rack_number = 'r06' if 'r06' in str(rack_name) else 'r07'

            render_deploy = deploy_template.render(vcpu=virtlet_params['vcpu'],
                                         ram=ram,
                                         ssh_key=virtlet_params['ssh_key'],
                                         disk=virtlet_params['disk'],
                                         image=virtlet_params['image'],
                                         vm_name= "{0}-{1}".format(virtlet_params['vm_name'].lower(),random_text),
                                         creator_name=user_name.lower(),
                                         login_name=user_name.lower(),
                                         rack_detail = "rackNo: {0}".format(rack_number)
                                        )
            deploy_response = deploy_conn.replace_deployment(name=vm_name, namespace='default',
                                               body=yaml.load(render_deploy))
            vm_name = deploy_response.metadata.name
            render_svc = svc_template.render(vcpu=virtlet_params['vcpu'],
                                             memory=ram,
                                             ssh_key=virtlet_params['ssh_key'],
                                             disk=virtlet_params['disk'],
                                             selector_name=vm_name,
                                             vm_name=vm_name,
                                             creator_name=user_name.lower(),
                                             login_name=user_name.lower(),
                                             rack_no = rack_number
                                            )
            svc_response = svc_conn.create_service(namespace='default',
                                                   body=yaml.load(render_svc))
            
            ram_in_gb = int(virtlet_params['ram'])
            used_disk, used_vcpu, used_ram = re.findall('\d+', res_dict[user[0]])
            res_dict[user[0]] = 'disk-vcpu-ram= [{0},{1},{2}]\n'.format(str(int(used_disk)+int(virtlet_params['disk'])),
                                                                          str(int(used_vcpu)+int(virtlet_params['vcpu'])),
                                                                          str(int(used_ram)+int(ram_in_gb))
                                                                         )
            available_disk, available_vcpu, available_ram = re.findall('\d+', res_dict["Total"])
            res_dict["Total"] = 'disk-vcpu-ram= [{0},{1},{2}]\n'.format(str(int(available_disk)-int(virtlet_params['disk'])),
                                                                        str(int(available_vcpu)-int(virtlet_params['vcpu'])),
                                                                        str(int(available_ram)-int(ram_in_gb))
                                                                         )
            cm_response.data = res_dict
            cm_conn.replace_configmap(name='resource-config', namespace='default', body=cm_response)
            
        return redirect('/list_vms')


@app.route('/delete_vm/', methods=['GET', 'POST'])
def delete_vm():
    svc_conn = get_conn('svc')
    deploy_conn = get_conn('deployment')
    cm_conn = get_conn('cm')
    vm_name = request.query_string.decode("utf-8")
    deploy_spec = deploy_conn.get_deployment_detail(name=vm_name, namespace="default")
    disk = deploy_spec.spec.template.metadata.annotations.get('VirtletRootVolumeSize')
    vcpu= deploy_spec.spec.template.metadata.annotations.get('VirtletVCPUCount')
    ram = deploy_spec.spec.template.spec.containers[0].resources.limits.get('memory')    
    delete_svc = svc_conn.delete_service(name=vm_name, namespace="default")
    delete_deploy = deploy_conn.delete_deployment(name=vm_name, namespace="default")
    # Updating resources
    disk = re.findall('\d+', disk)[0]
    vcpu = re.findall('\d+', vcpu)[0]
    ram = re.findall('\d+', ram)[0]
    cm_response = cm_conn.get_config_detail(name='resource-config', namespace='default')
    res_dict = cm_response.data
    user = get_users(set_value())
    user_name = user[0]
    used_disk, used_vcpu, used_ram = re.findall('\d+', res_dict[user_name])
    res_dict[user_name] = 'disk-vcpu-ram= [{0},{1},{2}]\n'.format(str(int(used_disk)-int(disk)),
                                                                  str(int(used_vcpu)-int(vcpu)),
                                                                  str(int(used_ram)-int(ram))
                                                                 )
    available_disk, available_vcpu, available_ram = re.findall('\d+', res_dict["Total"])
    res_dict["Total"] = 'disk-vcpu-ram= [{0},{1},{2}]\n'.format(str(int(available_disk)+int(disk)),
                                                                str(int(available_vcpu)+int(vcpu)),
                                                                str(int(available_ram)+int(ram))
                                                                 )
    cm_response.data = res_dict
    cm_conn.replace_configmap(name='resource-config', namespace='default', body=cm_response)
    return redirect('/list_vms')


@app.route('/logout', methods=['POST', 'GET'])
@auth.oidc_logout
def logout():
  session.clear()
  resp = json.dumps( {"msg": "Success", "code" : 200 })
  return resp

@app.route('/login')
@auth.oidc_auth('default')
def login():
  user_session = UserSession(flask.session)
  email = session['id_token']['email']
  if email:
    username = email.split('@')[0]
    db_conn = Sqlite(db_file=DATABASE)
    if not db_conn.get_user(username=username):
      db_conn.create_user(username=username)
      cm_conn = get_conn('cm')
      cm_response = cm_conn.get_config_detail(name='resource-config', namespace='default')
      res_dict = cm_response.data
      res_dict[username] = 'disk-vcpu-ram= [0,0,0]\n'
      cm_response.data = res_dict
      cm_conn.replace_configmap(name='resource-config', namespace='default', body=cm_response)
    
    set_value(username)
  return redirect('/list_vms')


@app.route('/test')
def test():
  #return jsonify(session['id_token_claims'])a

  return session['user']


@app.route('/')
def index():
  return redirect('/list_vms')


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
