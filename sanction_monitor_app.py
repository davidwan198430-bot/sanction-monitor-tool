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
import os
from urllib.parse import urljoin
import uuid

# ===================== 页面配置 =====================
st.set_page_config(
    page_title="制裁监控平台",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== 科技感冷灰配色UI =====================
st.markdown("""
<style>
/* 全局深色科技背景 */
.stApp {
    background-color: #121212;
    background-image: 
        linear-gradient(rgba(30,30,46,0.7) 1px, transparent 1px),
        linear-gradient(90deg, rgba(30,30,46,0.7) 1px, transparent 1px);
    background-size: 30px 30px;
    color: #E0E0E0;
    font-family: "Microsoft YaHei", sans-serif;
}

/* 左侧导航栏 - 科技深色 */
section[data-testid="stSidebar"] {
    background-color: #1A1A2D;
    border-right: 1px solid #33334F;
}
div[data-testid="stSidebarNavItems"] {
    background-color: #1A1A2D;
}

/* 毛玻璃卡片 - 科技感 */
.glass-card {
    background: rgba(42, 42, 58, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(94, 106, 210, 0.2);
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

/* 标题样式 */
.module-title {
    font-size: 22px;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #5E6AD2;
}
.card-title {
    font-size: 16px;
    font-weight: 600;
    color: #4FD1C5;
    margin-bottom: 16px;
}

/* 指标卡片 - 对称科技风 */
.metric-box {
    background: linear-gradient(135deg, #2A2A3A, #33334F);
    border: 1px solid #5E6AD2;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
}
.metric-value {
    font-size: 30px;
    font-weight: 700;
    color: #39FF14;
    margin: 8px 0;
}
.metric-label {
    font-size: 14px;
    color: #B0B0C0;
}

/* 按钮 - 科技蓝 */
.stButton button {
    background: linear-gradient(90deg, #5E6AD2, #4FD1C5);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 600;
    box-shadow: 0 3px 10px rgba(94,106,210,0.3);
}
.stButton button:hover {
    background: linear-gradient(90deg, #4FD1C5, #5E6AD2);
    box-shadow: 0 3px 15px rgba(94,106,210,0.5);
}
button[kind="secondary"] {
    background: #33334F !important;
    border: 1px solid #5E6AD2 !important;
}

/* 表格 - 深色科技 */
.data-table {
    width: 100%;
    border-collapse: collapse;
    background: #222233;
    border-radius: 8px;
    overflow: hidden;
}
.data-table th {
    background: #5E6AD2;
    color: white;
    padding: 12px;
    text-align: left;
}
.data-table td {
    padding: 12px;
    border-bottom: 1px solid #33334F;
    color: #E0E0E0;
}
.data-table tr:hover {
    background: #2A2A3A;
}

/* 日志区域 */
.log-area {
    height: 350px;
    overflow-y: auto;
    background: #1E1E2E;
    border: 1px solid #33334F;
    border-radius: 8px;
    padding: 16px;
    font-size: 13px;
    line-height: 1.6;
}
.log-success { color: #39FF14; }
.log-info { color: #4FD1C5; }
.log-error { color: #FF4D4F; }

/* 输入框 - 深色 */
.stTextInput input, .stNumberInput input, .stSelectbox div {
    background-color: #2A2A3A !important;
    color: white !important;
    border: 1px solid #5E6AD2 !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# ===================== 全局状态 =====================
if "active_page" not in st.session_state:
    st.session_state.active_page = "监控面板"
if "monitor_running" not in st.session_state:
    st.session_state.monitor_running = False
if "monitor_interval" not in st.session_state:
    st.session_state.monitor_interval = 900
if "time_range_days" not in st.session_state:
    st.session_state.time_range_days = 30
if "logs" not in st.session_state:
    st.session_state.logs = []
if "main_domains" not in st.session_state:
    st.session_state.main_domains = [
        {"id":str(uuid.uuid4()),"name":"商务部官网","url":"https://www.mofcom.gov.cn/","remark":""},
        {"id":str(uuid.uuid4()),"name":"美国财政部","url":"https://www.treasury.gov/","remark":""},
    ]
if "keywords" not in st.session_state:
    st.session_state.keywords = [{"id":str(uuid.uuid4()),"content":"制裁"},{"id":str(uuid.uuid4()),"content":"出口管制"}]
if "email_config" not in st.session_state:
    st.session_state.email_config = {"smtp_server":"","smtp_port":465,"sender_email":"","sender_password":"","receiver_email":""}

# ===================== 工具函数 =====================
def add_log(msg, typ="info"):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.logs.append((f"[{t}] {msg}", typ))
    if len(st.session_state.logs) > 100:
        st.session_state.logs = st.session_state.logs[-100:]

def extract_sub_links(url):
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10, verify=False)
        links = re.findall(r'href=["\'](.*?)["\']', r.text)
        valid = [urljoin(url, l) for l in links if any(x in l.lower() for x in ["sanction","制裁","list","清单","notice"])]
        add_log(f"✅ 提取到 {len(valid)} 个子链接", "success")
        return list(set(valid)) or [url]
    except:
        add_log(f"❌ 提取子链接失败", "error")
        return [url]

# ===================== 左侧导航 =====================
with st.sidebar:
    st.markdown("<h1 style='color:#4FD1C5; text-align:center;'>🚨 制裁监控平台</h1>", unsafe_allow_html=True)
    st.markdown("---")
    menu = ["监控面板", "配置中心", "报表管理", "系统日志"]
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.active_page = item

# ===================== 主页面：监控面板 =====================
if st.session_state.active_page == "监控面板":
    st.markdown("<div class='module-title'>🏠 监控面板</div>", unsafe_allow_html=True)
    
    # 3列对称指标
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown("<div class='metric-box'><div class='metric-label'>监控域名</div><div class='metric-value'>"+str(len(st.session_state.main_domains))+"</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='metric-box'><div class='metric-label'>监控关键词</div><div class='metric-value'>"+str(len(st.session_state.keywords))+"</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='metric-box'><div class='metric-label'>监控频率</div><div class='metric-value'>"+str(st.session_state.monitor_interval//60)+"</div><div class='metric-label'>分钟</div></div>", unsafe_allow_html=True)
    
    # 2列对称控制
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("<div class='glass-card'><div class='card-title'>监控控制</div>", unsafe_allow_html=True)
        status = "🟢 运行中" if st.session_state.monitor_running else "🔴 已停止"
        st.markdown(f"<div style='color:#4FD1C5; font-size:16px;'>状态：{status}</div>", unsafe_allow_html=True)
        bc1,bc2 = st.columns(2)
        with bc1:
            if st.button("▶️ 启动监控", disabled=st.session_state.monitor_running):
                st.session_state.monitor_running = True
                add_log("🚀 启动监控")
        with bc2:
            if st.button("⏹️ 停止监控", disabled=not st.session_state.monitor_running):
                st.session_state.monitor_running = False
                add_log("🛑 停止监控")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with c2:
        st.markdown("<div class='glass-card'><div class='card-title'>快捷配置</div>", unsafe_allow_html=True)
        st.session_state.time_range_days = st.selectbox("时长", [1,3,7,30], index=3)
        st.session_state.monitor_interval = st.slider("频率(分)", 1, 60, 15) * 60
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 日志
    st.markdown("<div class='glass-card'><div class='card-title'>实时日志</div>", unsafe_allow_html=True)
    log_html = ""
    for txt,typ in st.session_state.logs:
        log_html += f"<div class='log-{typ}'>{txt}</div>"
    st.markdown(f"<div class='log-area'>{log_html}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ===================== 配置中心 =====================
elif st.session_state.active_page == "配置中心":
    st.markdown("<div class='module-title'>⚙️ 配置中心</div>", unsafe_allow_html=True)
    t1,t2,t3 = st.tabs(["🌐 域名配置", "🔑 关键词", "📧 邮箱配置"])
    
    with t1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>主域名管理</div>", unsafe_allow_html=True)
        n1,n2,n3 = st.columns(3)
        with n1: nm = st.text_input("名称")
        with n2: url = st.text_input("URL")
        with n3: rm = st.text_input("备注")
        if st.button("➕ 添加域名"):
            if nm and url:
                st.session_state.main_domains.append({"id":str(uuid.uuid4()),"name":nm,"url":url,"remark":rm})
        st.markdown("</div>", unsafe_allow_html=True)
    
    with t2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>关键词</div>", unsafe_allow_html=True)
        kw = st.text_input("新增关键词")
        if st.button("➕ 添加关键词"):
            if kw:
                st.session_state.keywords.append({"id":str(uuid.uuid4()),"content":kw})
        st.markdown("</div>", unsafe_allow_html=True)
    
    with t3:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>邮箱配置</div>", unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            st.session_state.email_config["smtp_server"] = st.text_input("SMTP")
            st.session_state.email_config["smtp_port"] = st.number_input("端口", 465)
        with c2:
            st.session_state.email_config["sender_email"] = st.text_input("发件邮箱")
            st.session_state.email_config["sender_password"] = st.text_input("授权码", type="password")
            st.session_state.email_config["receiver_email"] = st.text_input("收件邮箱")
        st.markdown("</div>", unsafe_allow_html=True)

# ===================== 报表/日志 =====================
elif st.session_state.active_page == "报表管理":
    st.markdown("<div class='module-title'>📁 报表管理</div>", unsafe_allow_html=True)
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>历史报表</div>", unsafe_allow_html=True)
    files = [f for f in os.listdir(".") if f.endswith(".xlsx")]
    if files:
        df = pd.DataFrame([{"文件名":f,"大小":round(os.path.getsize(f)/1024,2)} for f in files])
        st.markdown(df.to_html(classes="data-table", index=False), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.active_page == "系统日志":
    st.markdown("<div class='module-title'>📜 系统日志</div>", unsafe_allow_html_html=True)
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    log_html = ""
    for txt,typ in st.session_state.logs:
        log_html += f"<div class='log-{typ}'>{txt}</div>"
    st.markdown(f"<div class='log-area'>{log_html}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
