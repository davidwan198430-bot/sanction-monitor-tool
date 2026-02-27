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

# ===================== 科技感冷灰配色UI（修复样式+隐藏按钮） =====================
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

/* 按钮样式（统一对齐+无多余间距） */
.stButton > button {
    background: linear-gradient(90deg, #5E6AD2, #4FD1C5);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    box-shadow: 0 3px 10px rgba(94,106,210,0.3);
    margin: 2px 0;
    display: inline-block;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #4FD1C5, #5E6AD2);
    box-shadow: 0 3px 15px rgba(94,106,210,0.5);
}
/* 隐藏触发按钮（核心修复：替代style参数） */
.hidden-btn {
    display: none !important;
}
/* 操作列小按钮（统一尺寸+对齐） */
.op-btn {
    padding: 4px 8px !important;
    font-size: 12px !important;
    margin: 0 2px !important;
    width: 70px !important;
}
/* 删除按钮样式 */
.del-btn {
    background: linear-gradient(90deg, #FF4D4F, #FF7875) !important;
}

/* 表格样式（修复换行+对齐） */
.data-table {
    width: 100%;
    border-collapse: collapse;
    background: #222233;
    border-radius: 8px;
    overflow: hidden;
    margin: 10px 0;
    table-layout: fixed; /* 固定列宽，避免错乱 */
}
.data-table th {
    background: #5E6AD2;
    color: white;
    padding: 12px;
    text-align: left;
    white-space: nowrap; /* 禁止表头换行 */
}
.data-table td {
    padding: 12px;
    border-bottom: 1px solid #33334F;
    color: #E0E0E0;
    vertical-align: middle; /* 垂直居中 */
    white-space: nowrap; /* 禁止单元格换行 */
}
.data-table td:last-child {
    width: 160px; /* 操作列固定宽度，确保对齐 */
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

/* Expander（修改表单） */
.stExpander {
    background: #222233 !important;
    border: 1px solid #5E6AD2 !important;
    border-radius: 8px !important;
}
.stExpanderHeader {
    background: #2A2A3A !important;
    color: #4FD1C5 !important;
}
</style>
""", unsafe_allow_html=True)

# ===================== 全局状态初始化 =====================
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
        {"id": str(uuid.uuid4()), "name": "商务部官网", "url": "https://www.mofcom.gov.cn/", "remark": ""},
        {"id": str(uuid.uuid4()), "name": "美国财政部官网", "url": "https://www.treasury.gov/", "remark": ""},
        {"id": str(uuid.uuid4()), "name": "欧盟EEAS官网", "url": "https://eeas.europa.eu/", "remark": ""},
        {"id": str(uuid.uuid4()), "name": "中国出口管制信息网", "url": "https://www.ecrc.org.cn/", "remark": ""}
    ]
if "keywords" not in st.session_state:
    st.session_state.keywords = [
        {"id": str(uuid.uuid4()), "content": "制裁"},
        {"id": str(uuid.uuid4()), "content": "反制"},
        {"id": str(uuid.uuid4()), "content": "出口管制"},
        {"id": str(uuid.uuid4()), "content": "实体清单"},
        {"id": str(uuid.uuid4()), "content": "sanctions"}
    ]
if "email_config" not in st.session_state:
    st.session_state.email_config = {
        "smtp_server": "smtp.exmail.qq.com",
        "smtp_port": 465,
        "sender_email": "",
        "sender_password": "",
        "receiver_email": ""
    }

# ===================== 工具函数 =====================
def add_log(msg, typ="info"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.logs.append((f"[{timestamp}] {msg}", typ))
    if len(st.session_state.logs) > 100:
        st.session_state.logs = st.session_state.logs[-100:]

def extract_sub_links(url):
    filter_keywords = ["制裁", "反制", "出口管制", "实体清单", "sanctions", "export control"]
    invalid_patterns = [".jpg", ".png", ".pdf", ".doc", "login"]
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.encoding = response.apparent_encoding
        all_links = re.findall(r'href=["\'](.*?)["\']', response.text)
        valid_links = []
        for link in all_links:
            full_link = urljoin(url, link)
            if any(invalid in full_link.lower() for invalid in invalid_patterns):
                continue
            if any(kw in full_link.lower() or kw in response.text.lower() for kw in filter_keywords):
                valid_links.append(full_link)
        valid_links = list(set(valid_links)) or [url]
        add_log(f"✅ 从【{url}】提取到 {len(valid_links)} 个相关子链接", "success")
        return valid_links
    except Exception as e:
        add_log(f"❌ 提取【{url}】子链接失败：{str(e)}", "error")
        return [url]

def delete_domain(domain_id):
    st.session_state.main_domains = [d for d in st.session_state.main_domains if d["id"] != domain_id]
    add_log(f"🗑️ 删除主域名：ID={domain_id}", "info")

def delete_keyword(kw_id):
    st.session_state.keywords = [k for k in st.session_state.keywords if k["id"] != kw_id]
    add_log(f"🗑️ 删除关键词：ID={kw_id}", "info")

def update_domain(domain_id, new_name, new_url, new_remark):
    for d in st.session_state.main_domains:
        if d["id"] == domain_id:
            d["name"] = new_name
            d["url"] = new_url
            d["remark"] = new_remark
            add_log(f"✏️ 修改主域名：{new_name}", "success")
            break

def update_keyword(kw_id, new_content):
    for k in st.session_state.keywords:
        if k["id"] == kw_id:
            k["content"] = new_content
            add_log(f"✏️ 修改关键词：{new_content}", "success")
            break

# ===================== 左侧导航 =====================
with st.sidebar:
    st.markdown("<h1 style='color:#4FD1C5; text-align:center; margin:20px 0;'>🚨 制裁监控平台</h1>", unsafe_allow_html=True)
    st.markdown("---")
    nav_buttons = ["监控面板", "配置中心", "报表管理", "系统日志"]
    for btn in nav_buttons:
        if st.button(btn, use_container_width=True, key=f"nav_{btn}"):
            st.session_state.active_page = btn
            add_log(f"🔄 切换到页面：{btn}", "info")

# ===================== 监控面板 =====================
if st.session_state.active_page == "监控面板":
    st.markdown("<div class='module-title'>🏠 监控面板</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class='metric-box'>
            <div class='metric-label'>监控主域名数</div>
            <div class='metric-value'>{len(st.session_state.main_domains)}</div>
            <div class='metric-label'>个</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='metric-box'>
            <div class='metric-label'>监控关键词数</div>
            <div class='metric-value'>{len(st.session_state.keywords)}</div>
            <div class='metric-label'>个</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='metric-box'>
            <div class='metric-label'>监控频率</div>
            <div class='metric-value'>{st.session_state.monitor_interval//60}</div>
            <div class='metric-label'>分钟/次</div>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='glass-card'><div class='card-title'>🎮 监控控制</div>", unsafe_allow_html=True)
        status_text = "🟢 监控运行中" if st.session_state.monitor_running else "🔴 监控已停止"
        st.markdown(f"<div style='font-size:16px; color:#4FD1C5; margin-bottom:15px;'>{status_text}</div>", unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("▶️ 启动监控", key="btn_start_monitor", disabled=st.session_state.monitor_running):
                st.session_state.monitor_running = True
                add_log("🚀 手动启动监控任务", "success")
        with btn_col2:
            if st.button("⏹️ 停止监控", key="btn_stop_monitor", disabled=not st.session_state.monitor_running):
                st.session_state.monitor_running = False
                add_log("🛑 手动停止监控任务", "info")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='glass-card'><div class='card-title'>📋 快捷配置</div>", unsafe_allow_html=True)
        time_range_options = [1, 3, 7, 30]
        st.session_state.time_range_days = st.selectbox(
            "监控时长范围（天）",
            time_range_options,
            index=time_range_options.index(st.session_state.time_range_days),
            key="select_time_range"
        )
        monitor_minutes = st.slider(
            "执行间隔（分钟）",
            min_value=1, max_value=60, value=st.session_state.monitor_interval//60,
            key="slider_monitor_interval"
        )
        st.session_state.monitor_interval = monitor_minutes * 60
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass-card'><div class='card-title'>📜 实时监控日志</div>", unsafe_allow_html=True)
    log_html = ""
    for log_content, log_type in st.session_state.logs:
        log_html += f"<div class='log-{log_type}'>{log_content}</div>"
    st.markdown(f"<div class='log-area'>{log_html if log_html else '<div style=\"color:#B0B0C0;\">暂无日志</div>'}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ===================== 配置中心（核心修复：无换行+按钮对齐+无报错） =====================
elif st.session_state.active_page == "配置中心":
    st.markdown("<div class='module-title'>⚙️ 配置中心</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["🌐 主域名配置", "🔑 关键词配置", "📧 邮箱配置"])
    
    # 1. 主域名配置（修复操作列换行+按钮对齐）
    with tab1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>主域名管理</div>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
        with col1:
            new_domain_name = st.text_input("域名名称", placeholder="如：商务部官网", key="input_new_domain_name")
        with col2:
            new_domain_url = st.text_input("域名URL", placeholder="如：https://www.mofcom.gov.cn/", key="input_new_domain_url")
        with col3:
            new_domain_remark = st.text_input("备注（可选）", placeholder="手动子链接，逗号分隔", key="input_new_domain_remark")
        with col4:
            if st.button("➕ 添加", key="btn_add_domain", use_container_width=True):
                if new_domain_name and new_domain_url:
                    st.session_state.main_domains.append({
                        "id": str(uuid.uuid4()),
                        "name": new_domain_name,
                        "url": new_domain_url,
                        "remark": new_domain_remark
                    })
                    add_log(f"✅ 新增主域名：{new_domain_name}", "success")
                    st.rerun()
                else:
                    st.error("❌ 名称和URL不能为空！")
        
        st.markdown("---")
        
        if st.session_state.main_domains:
            table_data = []
            for idx, domain in enumerate(st.session_state.main_domains):
                edit_btn_key = f"btn_edit_domain_{domain['id']}"
                del_btn_key = f"btn_del_domain_{domain['id']}"
                # 修复：移除HTML中的换行/空格，避免显示\n
                op_html = f"<button class='op-btn' onclick=\"document.getElementById('{edit_btn_key}').click()\">✏️ 修改</button><button class='op-btn del-btn' onclick=\"document.getElementById('{del_btn_key}').click()\">🗑️ 删除</button>"
                table_data.append({
                    "序号": idx + 1,
                    "域名名称": domain["name"],
                    "URL": domain["url"],
                    "备注": domain["remark"],
                    "操作": op_html
                })
            
            df_domains = pd.DataFrame(table_data)
            st.markdown(df_domains.to_html(escape=False, index=False, classes="data-table"), unsafe_allow_html=True)
            
            # 修复：用CSS类hidden-btn替代style参数，解决TypeError
            for domain in st.session_state.main_domains:
                del_btn_key = f"btn_del_domain_{domain['id']}"
                if st.button("删除触发", key=del_btn_key, type="secondary", help="", args=[], kwargs={}, disabled=False, use_container_width=False):
                    delete_domain(domain["id"])
                    st.success(f"✅ 删除成功：{domain['name']}")
                    st.rerun()
                # 给隐藏按钮加CSS类（核心修复）
                st.markdown(f"""<style>div[data-testid="stButton"][key="{del_btn_key}"] {{display: none !important;}}</style>""", unsafe_allow_html=True)
                
                edit_btn_key = f"btn_edit_domain_{domain['id']}"
                if st.button("修改触发", key=edit_btn_key, type="secondary", help="", args=[], kwargs={}, disabled=False, use_container_width=False):
                    with st.expander(f"修改域名：{domain['name']}", expanded=True, key=f"exp_edit_domain_{domain['id']}"):
                        new_name = st.text_input("新名称", value=domain["name"], key=f"input_edit_name_{domain['id']}")
                        new_url = st.text_input("新URL", value=domain["url"], key=f"input_edit_url_{domain['id']}")
                        new_remark = st.text_input("新备注", value=domain["remark"], key=f"input_edit_remark_{domain['id']}")
                        if st.button("保存修改", key=f"btn_save_domain_{domain['id']}"):
                            if new_name and new_url:
                                update_domain(domain["id"], new_name, new_url, new_remark)
                                st.success(f"✅ 修改成功：{new_name}")
                                st.rerun()
                            else:
                                st.error("❌ 名称和URL不能为空！")
                # 隐藏修改触发按钮
                st.markdown(f"""<style>div[data-testid="stButton"][key="{edit_btn_key}"] {{display: none !important;}}</style>""", unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align:center; color:#B0B0C0; padding:20px;'>暂无主域名配置</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 2. 关键词配置（同修复逻辑）
    with tab2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>关键词管理</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            new_keyword = st.text_input("新增关键词", placeholder="如：制裁 / sanctions", key="input_new_keyword")
        with col2:
            if st.button("➕ 添加", key="btn_add_keyword", use_container_width=True):
                if new_keyword and new_keyword not in [k["content"] for k in st.session_state.keywords]:
                    st.session_state.keywords.append({
                        "id": str(uuid.uuid4()),
                        "content": new_keyword
                    })
                    add_log(f"✅ 新增关键词：{new_keyword}", "success")
                    st.rerun()
                elif new_keyword in [k["content"] for k in st.session_state.keywords]:
                    st.error("❌ 关键词已存在！")
                else:
                    st.error("❌ 关键词不能为空！")
        
        st.markdown("---")
        
        if st.session_state.keywords:
            table_data = []
            for idx, kw in enumerate(st.session_state.keywords):
                edit_btn_key = f"btn_edit_kw_{kw['id']}"
                del_btn_key = f"btn_del_kw_{kw['id']}"
                # 修复：无换行的操作列HTML
                op_html = f"<button class='op-btn' onclick=\"document.getElementById('{edit_btn_key}').click()\">✏️ 修改</button><button class='op-btn del-btn' onclick=\"document.getElementById('{del_btn_key}').click()\">🗑️ 删除</button>"
                table_data.append({
                    "序号": idx + 1,
                    "关键词内容": kw["content"],
                    "操作": op_html
                })
            
            df_kw = pd.DataFrame(table_data)
            st.markdown(df_kw.to_html(escape=False, index=False, classes="data-table"), unsafe_allow_html=True)
            
            for kw in st.session_state.keywords:
                del_btn_key = f"btn_del_kw_{kw['id']}"
                if st.button("删除触发", key=del_btn_key, type="secondary"):
                    delete_keyword(kw["id"])
                    st.success(f"✅ 删除成功：{kw['content']}")
                    st.rerun()
                st.markdown(f"""<style>div[data-testid="stButton"][key="{del_btn_key}"] {{display: none !important;}}</style>""", unsafe_allow_html=True)
                
                edit_btn_key = f"btn_edit_kw_{kw['id']}"
                if st.button("修改触发", key=edit_btn_key, type="secondary"):
                    with st.expander(f"修改关键词：{kw['content']}", expanded=True, key=f"exp_edit_kw_{kw['id']}"):
                        new_content = st.text_input("新关键词", value=kw["content"], key=f"input_edit_kw_{kw['id']}")
                        if st.button("保存修改", key=f"btn_save_kw_{kw['id']}"):
                            if new_content and new_content not in [k["content"] for k in st.session_state.keywords if k["id"] != kw["id"]]:
                                update_keyword(kw["id"], new_content)
                                st.success(f"✅ 修改成功：{new_content}")
                                st.rerun()
                            elif new_content in [k["content"] for k in st.session_state.keywords if k["id"] != kw["id"]]:
                                st.error("❌ 关键词已存在！")
                            else:
                                st.error("❌ 关键词不能为空！")
                st.markdown(f"""<style>div[data-testid="stButton"][key="{edit_btn_key}"] {{display: none !important;}}</style>""", unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align:center; color:#B0B0C0; padding:20px;'>暂无关键词配置</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 3. 邮箱配置
    with tab3:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>邮箱配置（用于报表发送）</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            smtp_server = st.text_input(
                "SMTP服务器",
                value=st.session_state.email_config["smtp_server"],
                placeholder="如：smtp.exmail.qq.com",
                key="input_smtp_server"
            )
            smtp_port = st.number_input(
                "SMTP端口",
                value=st.session_state.email_config["smtp_port"],
                min_value=1, max_value=65535,
                key="input_smtp_port"
            )
            sender_email = st.text_input(
                "发件人邮箱",
                value=st.session_state.email_config["sender_email"],
                placeholder="your@company.com",
                key="input_sender_email"
            )
        with col2:
            sender_password = st.text_input(
                "SMTP授权码",
                type="password",
                value=st.session_state.email_config["sender_password"],
                placeholder="邮箱授权码（非登录密码）",
                key="input_sender_pwd"
            )
            receiver_email = st.text_input(
                "收件人邮箱",
                value=st.session_state.email_config["receiver_email"],
                placeholder="recipient@company.com",
                key="input_receiver_email"
            )
        
        if st.button("💾 保存邮箱配置", key="btn_save_email"):
            st.session_state.email_config = {
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "sender_email": sender_email,
                "sender_password": sender_password,
                "receiver_email": receiver_email
            }
            add_log("✅ 保存邮箱配置成功", "success")
            st.success("✅ 邮箱配置已保存！")
        
        st.markdown("""
        <div style='margin-top:15px; padding:10px; background:#2A2A3A; border-radius:6px; color:#B0B0C0;'>
        📌 配置提示：<br>
        1. SMTP服务器：腾讯企业邮箱=smtp.exmail.qq.com，网易=smtp.163.com<br>
        2. 端口：SSL加密默认465，非加密默认25<br>
        3. 授权码：需在邮箱后台开启SMTP服务并生成
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# ===================== 报表管理 =====================
elif st.session_state.active_page == "报表管理":
    st.markdown("<div class='module-title'>📁 报表管理</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>历史报表列表</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        filter_date = st.date_input("筛选日期", value=datetime.now(), key="input_filter_date")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ 清空所有报表", key="btn_clear_reports"):
            for f in os.listdir("."):
                if f.endswith(".xlsx") and "制裁监控报表" in f:
                    os.remove(f)
            add_log("🗑️ 清空所有报表文件", "info")
            st.success("✅ 已清空所有报表！")
            st.rerun()
    
    report_files = [f for f in os.listdir(".") if f.endswith(".xlsx") and "制裁监控报表" in f]
    if report_files:
        table_data = []
        for idx, file in enumerate(report_files):
            file_size = round(os.path.getsize(file) / 1024, 2)
            create_time = datetime.fromtimestamp(os.path.getctime(file)).strftime("%Y-%m-%d %H:%M:%S")
            download_btn_key = f"btn_download_report_{idx}"
            # 修复：无换行的操作列
            op_html = f"<button class='op-btn' onclick=\"document.getElementById('{download_btn_key}').click()\">📥 下载</button>"
            table_data.append({
                "序号": idx + 1,
                "报表名称": file,
                "文件大小(KB)": file_size,
                "生成时间": create_time,
                "操作": op_html
            })
        
        df_reports = pd.DataFrame(table_data)
        st.markdown(df_reports.to_html(escape=False, index=False, classes="data-table"), unsafe_allow_html=True)
        
        for idx, file in enumerate(report_files):
            download_btn_key = f"btn_download_report_{idx}"
            with open(file, "rb") as f:
                st.download_button(
                    label="下载触发",
                    data=f,
                    file_name=file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=download_btn_key
                )
            # 隐藏下载触发按钮
            st.markdown(f"""<style>div[data-testid="stButton"][key="{download_btn_key}"] {{display: none !important;}}</style>""", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center; color:#B0B0C0; padding:20px;'>暂无报表文件</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ===================== 系统日志 =====================
elif st.session_state.active_page == "系统日志":
    st.markdown("<div class='module-title'>📜 系统日志</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>日志筛选与查看</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        log_level_filter = st.selectbox("日志级别筛选", ["所有", "成功", "错误", "信息"], key="select_log_level")
    with col2:
        if st.button("🗑️ 清空日志", key="btn_clear_logs"):
            st.session_state.logs = []
            add_log("✅ 清空系统日志", "info")
            st.success("✅ 日志已清空！")
            st.rerun()
    
    st.markdown("---")
    
    if st.session_state.logs:
        filtered_logs = st.session_state.logs
        if log_level_filter != "所有":
            level_map = {"成功": "success", "错误": "error", "信息": "info"}
            filtered_logs = [log for log in st.session_state.logs if log[1] == level_map[log_level_filter]]
        
        table_data = []
        for idx, (log_content, log_type) in enumerate(filtered_logs):
            log_type_cn = {"success": "成功", "error": "错误", "info": "信息"}[log_type]
            table_data.append({
                "序号": idx + 1,
                "日志内容": log_content,
                "级别": log_type_cn,
                "样式": f"log-{log_type}"
            })
        
        html_table = "<table class='data-table'><thead><tr><th>序号</th><th>日志内容</th><th>级别</th></tr></thead><tbody>"
        for row in table_data:
            html_table += f"<tr><td>{row['序号']}</td><td class='{row['样式']}'>{row['日志内容']}</td><td>{row['级别']}</td></tr>"
        html_table += "</tbody></table>"
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center; color:#B0B0C0; padding:20px;'>暂无系统日志</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
