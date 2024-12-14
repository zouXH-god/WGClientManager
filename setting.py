import shutil

from dotenv import load_dotenv
import os


template_file = ".env.example"
target_file = ".env"
if not os.path.exists(target_file):
    shutil.copy(template_file, target_file)
    print(f"初始化 {template_file} 文件，请修改里面的配置项再运行程序.")
    exit()
else:
    print(f"{target_file} already exists.")

load_dotenv()
wg_name = os.getenv("WG_NAME", "wg0")
wg_config_path = os.getenv("WG_CONFIG_PATH", "/etc/wireguard/wg0.conf")
wg_host = os.getenv("WG_HOST", "")
Token = os.getenv("TOKEN", "")
user_name = os.getenv("USER_NAME", "")
user_password = os.getenv("USER_PASSWORD", "")
