from flask import Flask, jsonify, request, render_template

from wg_parse import parse_wg_output, parse_wg_conf, save_wg_conf, check_ping, cmd_add_client, add_client_to_conf, \
    cmd_del_client, get_all_clients_info, generate_wg_keypair, del_client_from_conf

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    clients = get_all_clients_info()
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

    # 判断 PublicKey 是否存在客户端中，不存在则添加
    if PublicKey not in [peer.get("PublicKey") for peer in parse_wg_conf().get("peer")]:
        add_client_to_conf(PublicKey, AllowedIP, note, PrivateKey=PrivateKey)
    if PublicKey not in [peer.get("public_key") for peer in parse_wg_output().get("peers")]:
        cmd_add_client(PublicKey, AllowedIP)
    return "ok"


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