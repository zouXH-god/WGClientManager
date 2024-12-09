import base64
import re
import subprocess
from io import BytesIO

import qrcode
from setting import wg_name, wg_config_path, wg_host


#  检查ip是否可以ping通
def check_ping(ip):
    try:
        # 使用 subprocess 运行 ping 命令，ping 4 次
        output = subprocess.run(['ping', '-c', '2', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # 检查 ping 命令的退出状态码，0表示成功
        if output.returncode == 0:
            return True
        else:
            return False

    except Exception as e:
        print(f"执行 ping 时出错: {e}")
        return False


# 解析指令客户端信息
def parse_wg_output() -> dict:
    wg_output = subprocess.getoutput('wg')
    # 存储接口和peer的解析结果
    result = {
        'interface': {},
        'peers': []
    }

    # 拆分为行
    lines = wg_output.splitlines()

    # 定义用于匹配的正则表达式
    interface_re = re.compile(r'interface:\s+(\S+)')
    public_key_re = re.compile(r'public key:\s+(\S+)')
    listening_port_re = re.compile(r'listening port:\s+(\d+)')
    peer_re = re.compile(r'peer:\s+(\S+)')
    endpoint_re = re.compile(r'endpoint:\s+(\S+:\d+)')
    allowed_ips_re = re.compile(r'allowed ips:\s+(\S+)')
    latest_handshake_re = re.compile(r'latest handshake:\s+([\d\w\s,]+)')
    transfer_re = re.compile(r'transfer:\s+([\d.]+\s\w+)\sreceived,\s([\d.]+\s\w+)\ssent')

    current_peer = None

    for line in lines:
        line = line.strip()
        if interface_match := interface_re.match(line):
            result['interface']['name'] = interface_match.group(1)
        elif public_key_match := public_key_re.match(line):
            result['interface']['public_key'] = public_key_match.group(1)
        elif listening_port_match := listening_port_re.match(line):
            result['interface']['listening_port'] = listening_port_match.group(1)
        elif peer_match := peer_re.match(line):
            # 新的peer开始，添加前一个peer到peers列表中
            if current_peer:
                result['peers'].append(current_peer)
            current_peer = {'public_key': peer_match.group(1)}
        elif endpoint_match := endpoint_re.match(line):
            if current_peer:
                current_peer['endpoint'] = endpoint_match.group(1)
        elif allowed_ips_match := allowed_ips_re.match(line):
            if current_peer:
                current_peer['allowed_ips'] = allowed_ips_match.group(1)
        elif latest_handshake_match := latest_handshake_re.match(line):
            if current_peer:
                current_peer['latest_handshake'] = latest_handshake_match.group(1)
        elif transfer_match := transfer_re.match(line):
            if current_peer:
                current_peer['transfer_rx'] = transfer_match.group(1)
                current_peer['transfer_tx'] = transfer_match.group(2)

    # 最后一个peer也要添加到peers列表中
    if current_peer:
        result['peers'].append(current_peer)

    return result


# 动态添加客户端
def cmd_add_client(client_pub_key: str, client_ip: str):
    cmd = f"wg set {wg_name} peer {client_pub_key} allowed-ips {client_ip}"
    subprocess.run(cmd, shell=True)


# 动态删除客户端
def cmd_del_client(client_pub_key: str):
    cmd = f"wg set {wg_name} peer {client_pub_key} remove"
    subprocess.run(cmd, shell=True)


# 解析配置文件
def parse_wg_conf(conf_path: str = wg_config_path) -> dict:
    with open(conf_path, 'r') as f:
        conf_content = f.readlines()
    data = {
        'interface': {},
        'peer': []
    }
    line_type = ""
    peer_data = {}
    peer_note = ""
    for index, line in enumerate(conf_content):
        # print(line)
        line = line.strip()
        if line == "[Interface]":
            line_type = "interface"
        elif line == "[Peer]":
            line_type = "peer"
            if line_type == "peer" and peer_data:
                data['peer'].append(peer_data)

            if conf_content[index - 1].startswith("#") and "PrivateKey" not in conf_content[index - 1]:
                peer_note = conf_content[index - 1].strip()
                peer_data = {"note": peer_note}
            else:
                peer_data = {}

        if line_type == "interface":
            line_data = line.split("=", 1)
            if len(line_data) >= 2:
                data['interface'][line_data[0].strip()] = line_data[1].split("#")[0].strip()
        elif line_type == "peer":
            line_data = line.split("=", 1)
            if len(line_data) >= 2:
                if line_data[0].strip() == "#PrivateKey":
                    peer_data["PrivateKey"] = line_data[1].split("#")[0].strip()
                else:
                    peer_data[line_data[0].strip()] = line_data[1].split("#")[0].strip()
    if line_type == "peer" and peer_data:
        data['peer'].append(peer_data)
    return data


# 保存配置文件
def save_wg_conf(conf_path: str = wg_config_path, conf_data: dict = None):
    if not conf_data:
        return False
    with open(conf_path, 'w', encoding="utf-8") as fp:
        fp.write("[Interface]\n")
        for key, value in conf_data['interface'].items():
            fp.write(f"{key} = {value}\n")
        fp.write("\n")
        for peer in conf_data['peer']:
            if peer.get('note'):
                note = peer['note'] if peer['note'].startswith("#") else f"# {peer['note']}"
                fp.write(f"{note}\n")
                del peer['note']
            fp.write("[Peer]\n")
            for key, value in peer.items():
                if key == "PrivateKey":
                    fp.write(f"#{key} = {value}\n")
                else:
                    fp.write(f"{key} = {value}\n")
            fp.write("\n")


# 配置文件添加客户端
def add_client_to_conf(client_pub_key: str, client_ip: str, note: str = None, PrivateKey: str = None):
    conf_data = parse_wg_conf()
    peer_data = {
        "PublicKey": client_pub_key,
        "AllowedIPs": client_ip if "/" in client_ip else f"{client_ip}/24",
    }
    if note:
        peer_data["note"] = note
    if PrivateKey:
        peer_data["PrivateKey"] = PrivateKey
    conf_data["peer"].append(peer_data)
    print(conf_data)
    save_wg_conf(conf_data=conf_data)


# 配置文件删除客户端
def del_client_from_conf(client_pub_key: str):
    conf_data = parse_wg_conf()
    for index, peer in enumerate(conf_data['peer']):
        if peer['PublicKey'] == client_pub_key:
            del conf_data['peer'][index]
            break
    save_wg_conf(conf_data=conf_data)


# 综合获取所有信息
def get_all_clients_info() -> dict:
    clients = parse_wg_output()
    conf = parse_wg_conf()
    for key, value in conf.get("interface").items():
        clients['interface'][key] = value

    for conf_peer in conf.get("peer"):
        in_client = False
        for client_peer in clients.get("peers"):
            if client_peer.get("public_key") == conf_peer.get("PublicKey"):
                in_client = True
                for key, value in conf_peer.items():
                    client_peer[key] = value
                break
        if not in_client:
            client_peer = {
                "public_key": conf_peer.get("PublicKey"),
                "allowed_ips": conf_peer.get("AllowedIP") if conf_peer.get("AllowedIP") else "0.0.0.0",
                "note": conf_peer.get("note")
            }
            clients["peers"].append(client_peer)
        # 为配置创建二维码
        client_peer["wg_conf"], client_peer["qr_code"] = mk_wg_config(client_peer.get("PrivateKey"), client_peer.get("AllowedIPs"),
                                              clients.get("interface").get("public_key"),
                                              clients.get("interface").get("Address"),
                                              clients.get("interface").get("ListenPort"))
    clients["interface"]["host"] = wg_host
    return clients


# 创建私钥与公钥
def generate_wg_keypair():
    # 生成私钥
    private_key_output = subprocess.run(['wg', 'genkey'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    private_key = private_key_output.stdout.strip()

    # 生成公钥
    public_key_output = subprocess.run(['wg', 'pubkey'], input=private_key, text=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
    public_key = public_key_output.stdout.strip()

    return private_key, public_key


def mk_wg_config(priv_key, address, pub_key, allowed_ips, listening_port):
    AllowedIPs = re.sub("\.\d+/", ".0/", allowed_ips)
    wg_config = f"""
[Interface]
PrivateKey = {priv_key}
Address = {address}
DNS = 8.8.8.8
MTU = 1420

[Peer]
PublicKey = {pub_key}
AllowedIPs = {AllowedIPs}
Endpoint = {wg_host}:{listening_port}
PersistentKeepalive = 25
"""
    return wg_config, "data:image/png;base64," + generate_qr_code_base64(wg_config)


#  生成二维码
def generate_qr_code_base64(wg_config):
    # 生成二维码
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(wg_config)
    qr.make(fit=True)

    # 创建二维码图像
    img = qr.make_image(fill='black', back_color='white')

    # 将图像保存到内存中
    buffered = BytesIO()
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return img_str
