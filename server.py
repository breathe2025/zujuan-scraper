#!/usr/bin/env python3
"""
组卷网试卷抓取工具 — Web 服务版

启动后浏览器访问 http://localhost:5000 即可使用。
局域网内其他设备可通过 http://你的IP:5000 访问。

用法:
    python server.py              # 默认端口 5000
    python server.py --port 8080  # 指定端口
"""

import re
import sys
import json
import time
from urllib.parse import urljoin, urlparse

from flask import Flask, request, jsonify, send_from_directory
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

app = Flask(__name__, static_folder="static", static_url_path="")

# ============================================================
# Playwright 浏览器（每个请求独立创建和销毁）
# ============================================================


def get_browser():
    """为每个请求创建独立的浏览器实例，避免状态污染"""
    pw = sync_playwright().start()
    # 云环境通常只有 Chromium，本地优先用 Edge
    channels = ["msedge", "chrome", None] if sys.platform == "win32" else [None, "chrome"]
    for channel in channels:
        try:
            browser = pw.chromium.launch(
                headless=True,
                channel=channel,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                ],
            )
            return pw, browser
        except Exception:
            continue
    raise RuntimeError("无法启动浏览器")


# ============================================================
# 核心抓取逻辑（复用 zujuan_scraper.py）
# ============================================================
PAPER_CARD_SELECTOR = "section.exam-box ul.exam-list > li"
PAPER_TITLE_SELECTOR = "a.exam-name"
PAGER_SELECTOR = ".tk-pager"
NEXT_PAGE_SELECTOR = 'a[data-type="nextPage"]:not(.disabled)'


def parse_url_filters(url: str) -> dict:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    last_segment = path.rstrip("/").split("/")[-1] if "/" in path else path

    filters = {}
    page_num = 1

    page_m = re.search(r"p(\d+)$", last_segment)
    if page_m:
        page_num = int(page_m.group(1))
        last_segment = last_segment[: page_m.start()]

    filter_patterns = {
        "tree_id": r"t(\d+)",
        "year": r"y(\d+)",
        "grade": r"g(\d+_\d+)",
        "level": r"l(\d+)",
        "diff": r"d(\d+)",
        "province": r"a(\d+)",
    }
    for key, pattern in filter_patterns.items():
        m = re.search(pattern, last_segment)
        if m:
            filters[key] = m.group(1)

    parts = path.split("/")
    last = parts[-1] if parts else ""
    if re.match(r"^t\d+", last):
        base_path = "/".join(parts[:-1])
    else:
        base_path = "/".join(parts)

    base_url = f"{parsed.scheme}://{parsed.netloc}{base_path}/"
    return {"base_url": base_url, "filters": filters, "page": page_num}


def apply_filters(page, filters: dict) -> None:
    tree_id = filters.get("tree_id")
    if tree_id:
        try:
            page.wait_for_selector(f'a.tree-anchor[tree-id="{tree_id}"]', timeout=5000)
            page.click(f'a.tree-anchor[tree-id="{tree_id}"]')
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeout:
                pass
            time.sleep(1)
        except Exception:
            pass

    year = filters.get("year")
    if year:
        try:
            page.wait_for_selector(f'a[data-type="selectYear"][data-id="{year}"]', timeout=5000)
            page.click(f'a[data-type="selectYear"][data-id="{year}"]')
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeout:
                pass
            time.sleep(1)
        except Exception:
            pass

    province = filters.get("province")
    if province:
        try:
            el = page.query_selector(f'a[data-type="selectProvince"][data-id="{province}"]')
            if el:
                el.scroll_into_view_if_needed()
                el.click()
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except PlaywrightTimeout:
                    pass
                time.sleep(1)
        except Exception:
            pass

    grade = filters.get("grade")
    if grade:
        try:
            page.wait_for_selector(f'a[data-type="selectLearnGrades"][data-id="{grade}"]', timeout=5000)
            page.click(f'a[data-type="selectLearnGrades"][data-id="{grade}"]')
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeout:
                pass
            time.sleep(1)
        except Exception:
            pass

    level = filters.get("level")
    if level:
        try:
            page.wait_for_selector(f'a[data-type="selectLevel"][data-id="{level}"]', timeout=5000)
            page.click(f'a[data-type="selectLevel"][data-id="{level}"]')
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeout:
                pass
            time.sleep(1)
        except Exception:
            pass


def extract_papers(page) -> list:
    cards = []
    for _ in range(5):
        time.sleep(0.5)
        cards = page.query_selector_all(PAPER_CARD_SELECTOR)
        if cards:
            break

    papers = []
    for card in cards:
        title_el = card.query_selector(PAPER_TITLE_SELECTOR)
        if not title_el:
            continue
        title = (title_el.get_attribute("title") or title_el.inner_text() or "").strip()
        href = (title_el.get_attribute("href") or "").strip()
        paper_id = (card.get_attribute("data-paperid") or "").strip()
        if not paper_id and href:
            m = re.search(r"/(\d+)p(\d+)\.html", href)
            if m:
                paper_id = m.group(2)
        if title and href:
            link = urljoin(page.url, href)
            papers.append({"title": title, "link": link, "paper_id": paper_id})
    return papers


def click_next_page(page) -> bool:
    next_btn = page.query_selector(NEXT_PAGE_SELECTOR)
    if not next_btn:
        return False
    first_card = page.query_selector(PAPER_CARD_SELECTOR)
    old_id = first_card.get_attribute("data-paperid") if first_card else None
    next_btn.click()
    for _ in range(20):
        time.sleep(0.5)
        cur_card = page.query_selector(PAPER_CARD_SELECTOR)
        cur_id = cur_card.get_attribute("data-paperid") if cur_card else None
        if cur_id and cur_id != old_id:
            return True
    return page.query_selector(NEXT_PAGE_SELECTOR) is not None


def get_pager_info(page) -> dict:
    info = {"total_items": 0, "page_size": 10, "total_pages": 1}
    try:
        pager = page.query_selector(PAGER_SELECTOR)
        if pager:
            info["total_items"] = int(pager.get_attribute("data-sum") or 0)
            info["page_size"] = int(pager.get_attribute("data-size") or 10)
            info["total_pages"] = max(1, (info["total_items"] + info["page_size"] - 1) // info["page_size"])
    except Exception:
        pass
    return info


# ============================================================
# API 路由
# ============================================================

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    data = request.get_json()
    if not data or not data.get("url"):
        return jsonify({"error": "缺少 URL 参数"}), 400

    url = data["url"]
    mode = data.get("mode", "current")       # current | range | all
    page_start = data.get("page_start", 1)
    page_end = data.get("page_end", 1)

    try:
        parsed = parse_url_filters(url)
    except Exception as e:
        return jsonify({"error": f"URL 解析失败: {e}"}), 400

    pw, browser = get_browser()
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="zh-CN",
    )
    page = context.new_page()

    try:
        # 加载基础页 + 应用筛选
        page.goto(parsed["base_url"], wait_until="domcontentloaded", timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeout:
            pass
        time.sleep(1)

        if parsed["filters"]:
            apply_filters(page, parsed["filters"])
            time.sleep(2)

        pager_info = get_pager_info(page)
        total_pages = pager_info["total_pages"]
        total_items = pager_info["total_items"]

        all_papers = []

        if mode == "current":
            # 跳到 URL 中指定的页
            target_page = parsed["page"]
            if target_page > 1:
                for _ in range(target_page - 1):
                    if not click_next_page(page):
                        break
                    time.sleep(0.5)
            papers = extract_papers(page)
            all_papers = papers
            current_page = target_page

        elif mode == "range":
            page_start = max(1, page_start)
            page_end = min(page_end, total_pages)
            # 先跳到起始页
            for _ in range(page_start - 1):
                if not click_next_page(page):
                    break
                time.sleep(0.5)
            for pg in range(page_start, page_end + 1):
                papers = extract_papers(page)
                all_papers.extend(papers)
                if pg < page_end:
                    if not click_next_page(page):
                        break
                    time.sleep(0.5)
            current_page = page_start

        elif mode == "all":
            papers = extract_papers(page)
            all_papers.extend(papers)
            for pg in range(2, total_pages + 1):
                if not click_next_page(page):
                    break
                time.sleep(0.5)
                papers = extract_papers(page)
                all_papers.extend(papers)
            current_page = 1

        # 去重
        seen = set()
        unique = []
        for p in all_papers:
            if p["paper_id"] not in seen:
                seen.add(p["paper_id"])
                unique.append(p)

        return jsonify({
            "papers": unique,
            "total_papers": len(unique),
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": current_page,
            "filters": parsed["filters"],
        })

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        return jsonify({"error": str(e), "traceback": tb}), 500
    finally:
        context.close()
        browser.close()
        pw.stop()


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "commit": "v3"})

@app.route("/api/test-playwright")
def test_pw():
    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        version = browser.version
        browser.close()
        pw.stop()
        return jsonify({"status": "ok", "browser": version})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e), "type": type(e).__name__})


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    print("=" * 50)
    print("  组卷网试卷抓取工具 — Web 服务")
    print(f"  访问地址: http://localhost:{port}")
    print("=" * 50)

    app.run(host="0.0.0.0", port=port, debug=False)
