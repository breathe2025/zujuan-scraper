# 组卷网试卷抓取工具

输入组卷网试卷列表页 URL，一键提取试卷名称和链接。支持筛选分类、年份、省份等条件。

## 🚀 部署到阿里云轻量应用服务器

### 1. 购买服务器

- [阿里云轻量应用服务器](https://swas.console.aliyun.com/) → **2核2G**（¥54/月起）
- 镜像选择 **Ubuntu 22.04**
- 购买后复制 **公网 IP**

### 2. 开放端口

轻量服务器控制台 → **防火墙** → 添加规则：

| 端口 | 协议 | 说明 |
|------|------|------|
| 5000 | TCP | Web 服务 |

### 3. SSH 登录并一键部署

```bash
ssh root@你的公网IP

# 安装 Docker（如已安装则跳过）
curl -fsSL https://get.docker.com | bash

# 克隆项目
git clone https://github.com/breathe2025/zujuan-scraper.git
cd zujuan-scraper

# 构建镜像（首次约 3-5 分钟）
docker build -t zujuan-tool .

# 启动服务（后台运行，自动重启）
docker run -d --name zujuan --restart=always -p 5000:5000 zujuan-tool
```

### 4. 访问

打开浏览器访问：**http://你的公网IP:5000**

---

## 支持的 URL 参数

| 参数 | 含义 | 示例 |
|------|------|------|
| `tN` | 分类 | `t5`=期末, `t3`=阶段检测 |
| `yN` | 年份 | `y2026` |
| `aN` | 省份 | `a110000`=北京 |
| `gN_M` | 年级 | `g11_2`=高二下学期 |
| `pN` | 页码 | `p3`=第3页 |

## 本地运行

```bash
pip install flask playwright
python -m playwright install chromium
python server.py
# 浏览器打开 http://localhost:5000
```

## API 接口

```bash
curl -X POST http://IP:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://zujuan.xkw.com/gzhx/shijuan/jdcs/t5y2026","mode":"current"}'
```
