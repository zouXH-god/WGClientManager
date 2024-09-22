## 项目名称：WGClientManager

### 介绍
WGClientManager 是一个基于 Flask 的 Web 应用程序，旨在简化对 WireGuard 客户端的管理。通过友好的用户界面，用户可以方便地添加、删除客户端，检查客户端状态，并生成密钥对。该项目结合了 WireGuard 的核心功能，提供了简洁且易于使用的接口，适合需要管理多个 WireGuard 客户端的用户。

### 使用方法

1. **环境配置**
- 安装依赖包：
   ```bash
   pip install flask qrcode
   ```
  
- 配置文件：
`setting.py` 文件中配置 WireGuard 服务名称、位置、IP等参数。

2. **运行应用程序**
   使用以下命令启动应用程序：

   ```bash
   python3 main.py
   ```

   应用程序将在 `http://IP:5000` 上运行。

3. **功能说明**
   - **主页**：访问 `/` 路径，查看并且管理当前所有 WireGuard 客户端的状态。
   - **获取所有客户端状态**：发送 GET 请求到 `/clients`，返回 JSON 格式的客户端状态信息。
   - **检查客户端连通性**：发送 GET 请求到 `/ping/<ip>`，检查指定 IP 地址的连通性。
   - **添加客户端**：发送 GET 请求到 `/add_client`，包含参数 `PublicKey`、`PrivateKey`、`AllowedIP` 和 `note`，如果未提供密钥，系统将自动生成。
   - **删除客户端**：发送 GET 请求到 `/del_client`，包含参数 `PublicKey`，以删除指定的客户端。
   - **生成密钥对**：发送 GET 请求到 `/generate_keypair`，获取一个新的公私钥对。

### 注意事项
- 确保在添加或删除客户端时，提供的 `PublicKey` 是有效的。
- 使用该应用程序时，确保 WireGuard 配置正确且服务器可访问。
