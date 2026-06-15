# 组卷网试卷抓取工具

输入组卷网试卷列表页 URL，一键提取试卷名称和链接。支持筛选分类、年份、省份等条件。

## 快速部署到云端（免费）

### 方式一：Render.com 部署（推荐，免信用卡）

1. 把这个项目上传到 GitHub
2. 打开 [render.com](https://render.com) 注册账号
3. 点击 **New + → Web Service**
4. 连接你的 GitHub 仓库
5. Render 会自动检测 `render.yaml` 并完成部署
6. 等待 5-10 分钟构建完成，获得 `https://xxx.onrender.com` 链接
7. 把链接分享给任何人使用！

### 方式二：本地运行

```bash
pip install flask playwright
python -m playwright install chromium
python server.py
# 浏览器打开 http://localhost:5000
```

## 支持的 URL 参数

| 参数 | 含义 | 示例 |
|------|------|------|
| `tN` | 分类 | `t5`=期末, `t3`=阶段检测 |
| `yN` | 年份 | `y2026` |
| `aN` | 省份 | `a110000`=北京 |
| `gN_M` | 年级 | `g11_2`=高二下学期 |
| `pN` | 页码 | `p3`=第3页 |

## API 接口

```bash
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://zujuan.xkw.com/gzhx/shijuan/jdcs/t5y2026","mode":"current"}'
```
