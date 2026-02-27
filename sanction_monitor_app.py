# -*- coding: utf-8 -*-
import streamlit as st
import requests
import re
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import time
import json
import os

# ===================== 全局配置 =====================
# 初始化会话状态（保存参数、监控状态）
if "monitor_running" not in st.session_state:
    st.session_state.monitor_running = False  # 监控状态：默认关闭
if "monitor_interval" not in st.session_state:
    st.session_state.monitor_interval = 900  # 默认15分钟
if "time_range_days" not in st.session_state:
    st.session_state.time_range_days = 30  # 默认监控30天
if "monitor_urls" not in st.session_state:
    # 初始域名列表
    st.session_state.monitor_urls = {
        "商务部条约法律司-主站": "https://trb.mofcom.gov.cn/",
        "美国OFAC-主站": "https://ofac.treasury.gov/"
    }
if "keywords" not in st.session_state:
    # 初始关键词
    st.session_state.keywords = ["制裁", "反制", "出口管制", "sanctions", "export control"]
if "sent_content_hash" not in st.session_state:
    st.session_state.sent_content_hash = set()  # 去重缓存

# ===================== 邮箱配置（用户在界面填写） =====================
st.sidebar.header("📧 邮箱配置")
SMTP_SERVER = st.sidebar.text_input("SMTP服务器", value="smtp.exmail.qq.com")
SMTP_PORT = st.sidebar.number_input("SMTP端口", value=465)
SENDER_EMAIL = st.sidebar.text_input("发件邮箱")
SENDER_PASSWORD = st.sidebar.text_input("SMTP授权码", type="password")
RECEIVER_EMAIL = st.sidebar.text_input("收件邮箱")

# ===================== 监控参数配置（可视化调整） =====================
st.sidebar.header("⚙️ 监控参数")
# 1. 监控时长选择
time_range_options = {"1天": 1, "3天": 3, "7天": 7, "30天": 30}
selected_time_range = st.sidebar.selectbox("监控内容时长", options=list(time_range_options.keys()))
st.session_state.time_range_days = time_range_options[selected_time_range]

# 2. 监控频率（秒）
monitor_interval_min = st.sidebar.slider("监控频率（分钟）", 1, 60, 15)
st.session_state.monitor_interval = monitor_interval_min * 60

# 3. 域名增删改
st.sidebar.header("🌐 域名管理")
# 添加域名
new_domain_name = st.sidebar.text_input("新增域名名称")
new_domain_url = st.sidebar.text_input("新增域名URL")
if st.sidebar.button("添加域名"):
    if new_domain_name and new_domain_url:
        st.session_state.monitor_urls[new_domain_name] = new_domain_url
        st.sidebar.success(f"添加成功：{new_domain_name}")
    else:
        st.sidebar.error("名称和URL不能为空")

# 删除域名
domain_to_delete = st.sidebar.selectbox("选择要删除的域名", options=list(st.session_state.monitor_urls.keys()))
if st.sidebar.button("删除域名"):
    del st.session_state.monitor_urls[domain_to_delete]
    st.sidebar.success(f"删除成功：{domain_to_delete}")

# 4. 关键词调整
st.sidebar.header("🔑 关键词管理")
new_keyword = st.sidebar.text_input("新增关键词")
if st.sidebar.button("添加关键词"):
    if new_keyword:
        st.session_state.keywords.append(new_keyword)
        st.sidebar.success(f"添加关键词：{new_keyword}")
    else:
        st.sidebar.error("关键词不能为空")

# ===================== 核心功能函数 =====================
def extract_publish_time(text, url):
    """提取发布时间"""
    time_patterns = [r'(\d{4})[-/年](\d{2})[-/月](\d{2})日?', r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})']
    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                year, month, day = match.groups()[:3]
                return datetime(int(year), int(month), int(day))
            except:
                continue
    return datetime.now()

def is_within_time_range(publish_time):
    """判断是否在监控时长内"""
    cutoff_time = datetime.now() - timedelta(days=st.session_state.time_range_days)
    return publish_time >= cutoff_time

def send_email_with_excel(excel_path):
    """发送带Excel的邮件"""
    if not excel_path or not SENDER_EMAIL or not RECEIVER_EMAIL or not SENDER_PASSWORD:
        st.warning("邮箱配置不完整或无Excel，跳过发邮件")
        return

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"【制裁监控报表】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    body = f"""本次监控覆盖 {len(st.session_state.monitor_urls)} 个域名，
筛选出近{st.session_state.time_range_days}天内命中关键词的内容，详见附件。
监控频率：{monitor_interval_min}分钟"""
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        with open(excel_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(excel_path)}"')
            msg.attach(part)

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        st.success("邮件发送成功！")
    except Exception as e:
        st.error(f"邮件发送失败：{str(e)}")

def crawl_and_filter():
    """抓取+筛选"""
    result_data = []
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_container = st.empty()

    for site_name, url in st.session_state.monitor_urls.items():
        log_container.info(f"正在抓取：{site_name} - {url}")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            response.encoding = response.apparent_encoding
            pure_text = re.sub(r'<[^>]+>', '', response.text).strip()
            content_hash = hash(pure_text[:1000])

            # 去重
            if content_hash in st.session_state.sent_content_hash:
                log_container.info(f"{site_name}：内容已发送过，跳过")
                continue

            # 时间筛选
            publish_time = extract_publish_time(pure_text, url)
            if not is_within_time_range(publish_time):
                log_container.info(f"{site_name}：内容超出{st.session_state.time_range_days}天，跳过")
                continue

            # 关键词筛选
            hit_keywords = [kw for kw in st.session_state.keywords if kw.lower() in pure_text.lower()]
            if not hit_keywords:
                log_container.info(f"{site_name}：未命中关键词，跳过")
                continue

            # 记录数据
            result_data.append({
                "网站名称": site_name,
                "网址": url,
                "命中关键词": ",".join(hit_keywords),
                "发布时间": publish_time.strftime('%Y-%m-%d'),
                "监控时间": current_time,
                "内容摘要": pure_text[:500]
            })
            st.session_state.sent_content_hash.add(content_hash)
            log_container.success(f"{site_name}：命中关键词[{','.join(hit_keywords)}]")
            time.sleep(1)

        except Exception as e:
            log_container.error(f"{site_name}：抓取失败 - {str(e)}")
            continue

    return result_data

def generate_excel(data):
    """生成Excel"""
    if not data:
        st.info("未抓取到符合条件的内容，不生成Excel")
        return None

    df = pd.DataFrame(data)
    excel_filename = f"制裁监控报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(excel_filename, index=False, engine='openpyxl')
    st.success(f"Excel生成成功：{excel_filename}")
    return excel_filename

def monitor_loop():
    """监控循环"""
    while st.session_state.monitor_running:
        st.subheader(f"📊 监控执行中（{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}）")
        # 1. 抓取筛选
        monitor_data = crawl_and_filter()
        # 2. 生成Excel
        excel_path = generate_excel(monitor_data)
        # 3. 发邮件
        send_email_with_excel(excel_path)
        # 4. 等待下一次执行
        wait_time = st.session_state.monitor_interval
        for i in range(wait_time, 0, -1):
            st.info(f"下次监控将在 {i} 秒后执行（点击「停止监控」可终止）")
            time.sleep(1)
            if not st.session_state.monitor_running:
                break

# ===================== 主界面 =====================
st.title("🚨 制裁监控小工具")
st.subheader("当前监控状态：" + ("🟢 运行中" if st.session_state.monitor_running else "🔴 已停止"))

# 开启/关闭按钮
col1, col2 = st.columns(2)
with col1:
    if st.button("开启监控", disabled=st.session_state.monitor_running):
        st.session_state.monitor_running = True
        st.success("监控已开启！")
        monitor_loop()
with col2:
    if st.button("停止监控", disabled=not st.session_state.monitor_running):
        st.session_state.monitor_running = False
        st.warning("监控已停止！")

# 显示当前配置
st.subheader("📋 当前配置")
st.write(f"监控时长：{st.session_state.time_range_days}天")
st.write(f"监控频率：{monitor_interval_min}分钟")
st.write("监控域名列表：")
for name, url in st.session_state.monitor_urls.items():
    st.write(f"- {name}：{url}")
st.write("监控关键词：")
st.write(", ".join(st.session_state.keywords))

# 日志和Excel下载
st.subheader("📁 报表下载")
# 列出当前目录下的Excel文件
excel_files = [f for f in os.listdir(".") if f.endswith(".xlsx") and "制裁监控报表" in f]
if excel_files:
    selected_excel = st.selectbox("选择要下载的报表", excel_files)
    with open(selected_excel, "rb") as f:
        st.download_button("下载Excel", f, file_name=selected_excel)
else:
    st.write("暂无报表文件")
