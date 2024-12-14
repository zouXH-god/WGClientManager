import ipaddress

from flask import Flask, jsonify, request, render_template, redirect, url_for, make_response

import setting
from wg_parse import parse_wg_output, parse_wg_conf, save_wg_conf, check_ping, cmd_add_client, add_client_to_conf, \
    cmd_del_client, get_all_clients_info, generate_wg_keypair, del_client_from_conf, get_allowed_ips

app = Flask(__name__)

# 定义一个全局的 before_request 处理器
@app.before_request
def check_token():
    # 排除不需要认证的路由，比如登录路由
    excluded_routes = ['/login']
    if request.path not in excluded_routes:
        token = request.headers.get('X-Token') or request.cookies.get('auth_token')
        if not token or token != setting.Token:
            # 如果没有找到 Token，则重定向到登录页面
            return redirect(url_for('login'))


# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == setting.user_name and password == setting.user_password:
            response = make_response(redirect("/"))
            response.set_cookie('auth_token', setting.Token)
            return response
    return render_template("login.html")


@app.route('/', methods=['GET'])
def index():
    clients = get_all_clients_info()
    # 排序
    clients["peers"] = sorted(clients["peers"], key=lambda x: ipaddress.ip_network(x['allowed_ips']))
    for client in clients["peers"]:
        print(client["allowed_ips"])
    return render_template("index.html", clients=clients)


# 获取所有客户端状态
@app.route('/clients', methods=['GET'])
def get_clients():
    clients = get_all_clients_info()
    return jsonify(clients)


@app.route('/ping/<ip>', methods=['GET'])
def ping(ip):
    return jsonify({
        "result": check_ping(ip)
    })


@app.route('/add_client', methods=['GET'])
def add_client():
    PublicKey = request.args.get('PublicKey')
    PrivateKey = request.args.get('PrivateKey')
    AllowedIP = request.args.get('AllowedIP')
    note = request.args.get('note')
    if not PublicKey or not PrivateKey:
        PublicKey, PrivateKey = generate_wg_keypair()
    wg_conf = parse_wg_conf()
    wg_output = parse_wg_output()

    # 判断 AllowedIP 是否重复
    if (
            get_allowed_ips(AllowedIP) in [peer.get("AllowedIPs") for peer in wg_conf.get("peer")] or
            get_allowed_ips(AllowedIP) in [peer.get("allowed_ips") for peer in wg_output.get("peer")]
    ):
        return 500, jsonify({
            "result": "error",
            "message": "AllowedIP 重复"
        })

    # 判断 PublicKey 是否存在客户端中，不存在则添加
    if PublicKey not in [peer.get("PublicKey") for peer in wg_conf.get("peer")]:
        add_client_to_conf(PublicKey, AllowedIP, note, PrivateKey=PrivateKey)
    if PublicKey not in [peer.get("public_key") for peer in wg_output.get("peers")]:
        cmd_add_client(PublicKey, AllowedIP)
    return 200, "ok"


@app.route('/del_client', methods=['GET'])
def del_client():
    PublicKey = request.args.get('PublicKey')

    # 判断 PublicKey 是否存在客户端中，存在则删除
    if PublicKey in [peer.get("PublicKey") for peer in parse_wg_conf().get("peer")]:
        del_client_from_conf(PublicKey)
    if PublicKey in [peer.get("public_key") for peer in parse_wg_output().get("peers")]:
        cmd_del_client(PublicKey)

    return "ok"


@app.route('/generate_keypair', methods=['GET'])
def generate_keypair():
    return jsonify(generate_wg_keypair())


if __name__ == '__main__':
    app.run("0.0.0.0", debug=True)