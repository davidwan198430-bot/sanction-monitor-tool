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

# ===================== 1. 页面基础配置（监控平台后台风格） =====================
st.set_page_config(
    page_title="制裁监控平台",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"  # 左侧导航常驻展开
)

# 自定义CSS（企业级监控平台后台风格，通过key定位按钮样式）
st.markdown("""
<style>
    /* 全局重置 */
    * {margin: 0; padding: 0; box-sizing: border-box;}
    .stApp {background-color: #F0F2F6; font-family: "Microsoft YaHei", sans-serif;}
    
    /* 左侧导航栏（固定） */
    .sidebar .sidebar-content {
        background-color: #2B3A48;
        color: white;
        padding: 24px 0;
        width: 220px !important;
    }
    
    /* 导航按钮样式 */
    div[data-testid="stButton"][key*="nav_"] button {
        width: 100%;
        background-color: #2B3A48;
        color: white;
        border: none;
        text-align: left;
        padding: 12px 24px;
        margin: 4px 0;
        border-left: 3px solid transparent;
    }
    div[data-testid="stButton"][key*="nav_"].active button {
        background-color: #165DFF;
        border-left: 3px solid #4096FF;
    }
    div[data-testid="stButton"][key*="nav_"] button:hover {
        background-color: #374758;
    }
    
    /* 右侧内容区容器 */
    .main-content {
        margin-left: 240px;
        padding: 24px;
    }
    
    /* 模块标题 */
    .module-title {
        font-size: 20px;
        font-weight: 600;
        color: #1D2129;
        margin-bottom: 20px;
        padding-bottom: 8px;
        border-bottom: 2px solid #E5E6EB;
    }
    
    /* 卡片样式（对称统一） */
    .card {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 20px;
        height: 100%;  /* 对称关键：卡片高度统一 */
    }
    .card-header {
        font-size: 16px;
        font-weight: 600;
        color: #1D2129;
        margin-bottom: 16px;
    }
    
    /* 指标卡片（对称） */
    .metric-card {
        text-align: center;
        padding: 20px 10px;
        background: linear-gradient(135deg, #E8F3FF 0%, #F0F7FF 100%);
        border-radius: 8px;
        border: 1px solid #D1E9FF;
    }
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #165DFF;
        margin: 8px 0;
    }
    .metric-label {
        font-size: 14px;
        color: #4E5969;
    }
    
    /* 按钮样式（通过key定位） */
    /* 主按钮（primary） */
    div[data-testid="stButton"][key*="_primary"] button {
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        width: 100%;
        background-color: #165DFF;
        color: white;
    }
    div[data-testid="stButton"][key*="_primary"] button:hover {
        background-color: #0E42CC;
    }
    
    /* 成功按钮（success） */
    div[data-testid="stButton"][key*="_success"] button {
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        width: 100%;
        background-color: #00B42A;
        color: white;
    }
    div[data-testid="stButton"][key*="_success"] button:hover {
        background-color: #009A22;
    }
    
    /* 危险按钮（danger） */
    div[data-testid="stButton"][key*="_danger"] button {
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        width: 100%;
        background-color: #F53F3F;
        color: white;
    }
    div[data-testid="stButton"][key*="_danger"] button:hover {
        background-color: #D92D20;
    }
    
    /* 表格样式（后台风格） */
    .data-table {
        width: 100%;
        border-collapse: collapse;
        border: 1px solid #E5E6EB;
    }
    .data-table th {
        background-color: #F7F8FA;
        color: #1D2129;
        font-weight: 600;
        padding: 12px 10px;
        text-align: left;
        border-bottom: 2px solid #E5E6EB;
    }
    .data-table td {
        padding: 12px 10px;
        border-bottom: 1px solid #E5E6EB;
        color: #4E5969;
    }
    .data-table tr:hover {background-color: #F7F8FA;}
    
    /* 操作按钮（表格内） */
    .op-btn {
        padding: 6px 10px;
        border-radius: 4px;
        font-size: 12px;
        border: none;
        cursor: pointer;
        margin: 0 2px;
    }
    .op-edit {background-color: #FF7D00; color: white;}
    .op-delete {background-color: #F53F3F; color: white;}
    
    /* 日志区域（滚动） */
    .log-container {
        height: 350px;
        overflow-y: auto;
        background-color: #F7F8FA;
        border-radius: 8px;
        padding: 16px;
        font-size: 14px;
        line-height: 1.6;
    }
    .log-success {color: #00B42A;}
    .log-error {color: #F53F3F;}
    .log-info {color: #165DFF;}
    
    /* 隐藏默认元素 */
    .stSidebarHeader, .stSidebarFooter {display: none;}
    .block-container {padding: 0 !important;}
</style>
""", unsafe_allow_html=True)

# ===================== 2. 全局会话状态初始化 =====================
# 核心状态
if "active_module" not in st.session_state:
    st.session_state.active_module = "监控面板"
if "monitor_running" not in st.session_state:
    st.session_state.monitor_running = False
if "monitor_interval" not in st.session_state:
    st.session_state.monitor_interval = 900  # 15分钟
if "time_range_days" not in st.session_state:
    st.session_state.time_range_days = 30
if "sent_content_hash" not in st.session_state:
    st.session_state.sent_content_hash = set()
if "system_logs" not in st.session_state:
    st.session_state.system_logs = []

# 主域名配置
if "main_domains" not in st.session_state:
    st.session_state.main_domains = [
        {"id": str(uuid.uuid4()), "name": "商务部官网", "url": "https://www.mofcom.gov.cn/", "remark": ""},
        {"id": str(uuid.uuid4()), "name": "美国财政部官网", "url": "https://www.treasury.gov/", "remark": ""},
        {"id": str(uuid.uuid4()), "name": "欧盟EEAS官网", "url": "https://eeas.europa.eu/", "remark": ""},
        {"id": str(uuid.uuid4()), "name": "中国出口管制信息网", "url": "https://www.ecrc.org.cn/", "remark": ""},
        {"id": str(uuid.uuid4()), "name": "外交部官网", "url": "https://www.mfa.gov.cn/", "remark": ""},
        {"id": str(uuid.uuid4()), "name": "海关总署官网", "url": "https://www.customs.gov.cn/", "remark": ""}
    ]

# 关键词配置
if "keywords" not in st.session_state:
    st.session_state.keywords = [
        {"id": str(uuid.uuid4()), "content": "制裁"},
        {"id": str(uuid.uuid4()), "content": "反制"},
        {"id": str(uuid.uuid4()), "content": "出口管制"},
        {"id": str(uuid.uuid4()), "content": "实体清单"},
        {"id": str(uuid.uuid4()), "content": "sanctions"},
        {"id": str(uuid.uuid4()), "content": "export control"}
    ]

# 邮箱配置
if "email_config" not in st.session_state:
    st.session_state.email_config = {
        "smtp_server": "smtp.exmail.qq.com",
        "smtp_port": 465,
        "sender_email": "",
        "sender_password": "",
        "receiver_email": ""
    }

# ===================== 3. 核心工具函数 =====================
def add_system_log(message, level="info"):
    """添加系统日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    st.session_state.system_logs.append((log_entry, level))
    if len(st.session_state.system_logs) > 200:
        st.session_state.system_logs = st.session_state.system_logs[-200:]

def extract_sub_links(main_url):
    """提取主域名下相关子链接"""
    filter_keywords = ["制裁", "反制", "出口管制", "实体清单", "公告", "政策", "sanctions", "export control"]
    invalid_patterns = [".jpg", ".png", ".pdf", ".doc", ".xls", "login", "register", "logout"]
    
    sub_links = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    try:
        response = requests.get(main_url, headers=headers, timeout=15, verify=False)
        response.encoding = response.apparent_encoding
        all_links = re.findall(r'href=["\'](.*?)["\']', response.text)
        
        for link in all_links:
            full_link = urljoin(main_url, link)
            if any(invalid in full_link.lower() for invalid in invalid_patterns):
                continue
            if any(kw in full_link.lower() or kw in response.text.lower() for kw in filter_keywords):
                sub_links.append(full_link)
        
        sub_links = list(set(sub_links))
        if not sub_links:
            sub_links = [main_url]
        
        add_system_log(f"✅ 从【{main_url}】提取到 {len(sub_links)} 个相关子链接", "success")
        return sub_links
    
    except Exception as e:
        add_system_log(f"❌ 提取【{main_url}】子链接失败：{str(e)}", "error")
        return [main_url]

def extract_publish_time(text, url):
    """提取内容发布时间"""
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
    """判断是否在监控时间范围内"""
    cutoff_time = datetime.now() - timedelta(days=st.session_state.time_range_days)
    return publish_time >= cutoff_time

def send_email_with_excel(excel_path):
    """发送带Excel附件的邮件"""
    if not excel_path:
        add_system_log("⚠️ 无Excel文件，跳过邮件发送", "info")
        return
    if not all([st.session_state.email_config["sender_email"], 
                st.session_state.email_config["receiver_email"], 
                st.session_state.email_config["sender_password"]]):
        add_system_log("⚠️ 邮箱配置不完整，跳过邮件发送", "info")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = st.session_state.email_config["sender_email"]
        msg['To'] = st.session_state.email_config["receiver_email"]
        msg['Subject'] = f"【制裁监控平台】报表 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        body = f"""
制裁监控平台执行结果：
1. 监控主域名数量：{len(st.session_state.main_domains)} 个
2. 监控时长范围：近 {st.session_state.time_range_days} 天
3. 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
4. 报表文件：{os.path.basename(excel_path)}
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        with open(excel_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(excel_path)}"')
            msg.attach(part)
        
        with smtplib.SMTP_SSL(st.session_state.email_config["smtp_server"], 
                              st.session_state.email_config["smtp_port"]) as server:
            server.login(st.session_state.email_config["sender_email"], 
                        st.session_state.email_config["sender_password"])
            server.sendmail(st.session_state.email_config["sender_email"], 
                            st.session_state.email_config["receiver_email"], 
                            msg.as_string())
        
        add_system_log("✅ 邮件发送成功", "success")
        st.success("✅ 邮件发送成功！")
    
    except Exception as e:
        add_system_log(f"❌ 邮件发送失败：{str(e)}", "error")
        st.error(f"❌ 邮件发送失败：{str(e)}")

def generate_excel(data):
    """生成Excel报表"""
    if not data:
        add_system_log("ℹ️ 未抓取到符合条件的内容，不生成Excel", "info")
        return None
    
    df = pd.DataFrame(data)
    excel_filename = f"制裁监控报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(excel_filename, index=False, engine='openpyxl')
    
    add_system_log(f"📊 Excel报表生成成功：{excel_filename}", "success")
    return excel_filename

def crawl_and_filter():
    """核心抓取筛选逻辑"""
    result_data = []
    add_system_log("🔍 开始执行监控任务", "info")
    
    for domain in st.session_state.main_domains:
        domain_name = domain["name"]
        main_url = domain["url"]
        remark = domain["remark"]
        
        add_system_log(f"🔍 监控主域名：{domain_name}", "info")
        sub_links = extract_sub_links(main_url)
        
        # 补充手动备注的子链接
        if remark:
            manual_links = [link.strip() for link in remark.split(",") if link.strip()]
            sub_links.extend(manual_links)
            sub_links = list(set(sub_links))
        
        # 遍历子链接抓取
        for link in sub_links:
            try:
                response = requests.get(link, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, verify=False)
                response.encoding = response.apparent_encoding
                pure_text = re.sub(r'<[^>]+>', '', response.text).strip()
                content_hash = hash(pure_text[:1000])
                
                # 去重筛选
                if content_hash in st.session_state.sent_content_hash:
                    add_system_log(f"⏭️ 【{link}】内容已发送过，跳过", "info")
                    continue
                
                # 时间筛选
                publish_time = extract_publish_time(pure_text, link)
                if not is_within_time_range(publish_time):
                    add_system_log(f"⏳ 【{link}】内容超出{st.session_state.time_range_days}天，跳过", "info")
                    continue
                
                # 关键词筛选
                kw_list = [item["content"] for item in st.session_state.keywords]
                hit_keywords = [kw for kw in kw_list if kw.lower() in pure_text.lower()]
                if not hit_keywords:
                    add_system_log(f"🔍 【{link}】未命中关键词，跳过", "info")
                    continue
                
                # 记录有效数据
                result_data.append({
                    "主域名": domain_name,
                    "子链接URL": link,
                    "命中关键词": ",".join(hit_keywords),
                    "发布时间": publish_time.strftime('%Y-%m-%d'),
                    "监控时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "内容摘要": pure_text[:500]
                })
                
                st.session_state.sent_content_hash.add(content_hash)
                add_system_log(f"✅ 【{link}】命中关键词：{','.join(hit_keywords[:3])}...", "success")
                time.sleep(1)  # 反爬休眠
            
            except Exception as e:
                add_system_log(f"❌ 抓取【{link}】失败：{str(e)}", "error")
                continue
    
    add_system_log(f"🔍 监控任务完成，有效数据：{len(result_data)} 条", "info")
    return result_data

def monitor_loop():
    """监控主循环"""
    while st.session_state.monitor_running:
        monitor_data = crawl_and_filter()
        excel_path = generate_excel(monitor_data)
        send_email_with_excel(excel_path)
        
        # 倒计时等待下一次执行
        wait_time = st.session_state.monitor_interval
        for i in range(wait_time, 0, -1):
            if not st.session_state.monitor_running:
                break
            add_system_log(f"⏱️ 下次监控将在 {i} 秒后执行", "info")
            time.sleep(1)

# ===================== 4. 页面渲染函数 =====================
def render_sidebar():
    """渲染左侧导航栏"""
    with st.sidebar:
        st.markdown("<div style='text-align: center; padding: 20px 0;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: white;'>🚨 制裁监控平台</h3>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 导航项
        nav_items = ["监控面板", "配置中心", "报表管理", "系统日志"]
        for item in nav_items:
            is_active = st.session_state.active_module == item
            # 导航按钮
            if st.button(item, key=f"nav_{item}", 
                        on_click=lambda x=item: setattr(st.session_state, "active_module", x)):
                st.session_state.active_module = item
            # 激活样式
            if is_active:
                st.markdown(f"""
                <style>
                    div[data-testid="stButton"][key="nav_{item}"] button {{
                        background-color: #165DFF !important;
                        border-left: 3px solid #4096FF !important;
                    }}
                </style>
                """, unsafe_allow_html=True)

def render_monitor_panel():
    """渲染监控面板"""
    st.markdown("<div class='main-content'>", unsafe_allow_html=True)
    st.markdown("<div class='module-title'>🏠 监控面板</div>", unsafe_allow_html=True)
    
    # 核心指标（3列对称）
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='card metric-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-label'>监控主域名数</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{len(st.session_state.main_domains)}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>个</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card metric-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-label'>监控关键词数</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{len(st.session_state.keywords)}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>个</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='card metric-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-label'>监控频率</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{st.session_state.monitor_interval//60}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>分钟/次</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 监控控制（2列对称）
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>🎮 监控控制</div>", unsafe_allow_html=True)
        
        # 监控状态
        status_text = "🟢 监控运行中" if st.session_state.monitor_running else "🔴 监控已停止"
        status_color = "#00B42A" if st.session_state.monitor_running else "#F53F3F"
        st.markdown(f"<div style='font-size: 16px; color: {status_color}; margin-bottom: 16px;'>{status_text}</div>", unsafe_allow_html=True)
        
        # 控制按钮
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("▶️ 开启监控", key="start_monitor_success", 
                        disabled=st.session_state.monitor_running):
                st.session_state.monitor_running = True
                add_system_log("🚀 手动开启监控任务", "success")
                st.rerun()
        with btn_col2:
            if st.button("⏹️ 停止监控", key="stop_monitor_danger", 
                        disabled=not st.session_state.monitor_running):
                st.session_state.monitor_running = False
                add_system_log("🛑 手动停止监控任务", "info")
                st.rerun()
        
        # 监控参数展示
        st.markdown("<div style='margin-top: 16px;'>", unsafe_allow_html=True)
        st.write(f"• 监控时长范围：{st.session_state.time_range_days} 天")
        st.write(f"• 执行间隔：{st.session_state.monitor_interval//60} 分钟")
        st.write(f"• 日志条数：{len(st.session_state.system_logs)} 条")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>📋 监控参数快捷配置</div>", unsafe_allow_html=True)
        
        # 快捷配置
        time_range = st.selectbox("监控时长范围", ["1天", "3天", "7天", "30天"],
                                 index=["1天", "3天", "7天", "30天"].index(f"{st.session_state.time_range_days}天"))
        monitor_interval = st.slider("执行频率（分钟）", 1, 60, st.session_state.monitor_interval//60)
        
        if st.button("💾 保存参数", key="save_param_primary"):
            st.session_state.time_range_days = int(time_range.replace("天", ""))
            st.session_state.monitor_interval = monitor_interval * 60
            add_system_log(f"✅ 保存监控参数：时长{st.session_state.time_range_days}天，频率{monitor_interval}分钟", "success")
            st.success("✅ 参数保存成功！")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 实时监控日志
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-header'>📜 实时监控日志</div>", unsafe_allow_html=True)
    
    log_html = ""
    for log_entry, level in st.session_state.system_logs:
        if level == "success":
            log_html += f"<div class='log-success'>{log_entry}</div>"
        elif level == "error":
            log_html += f"<div class='log-error'>{log_entry}</div>"
        else:
            log_html += f"<div class='log-info'>{log_entry}</div>"
    
    st.markdown(f"<div class='log-container'>{log_html}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 启动监控循环
    if st.session_state.monitor_running:
        monitor_loop()

def render_config_center():
    """渲染配置中心"""
    st.markdown("<div class='main-content'>", unsafe_allow_html=True)
    st.markdown("<div class='module-title'>⚙️ 配置中心</div>", unsafe_allow_html=True)
    
    # 配置标签页
    tab1, tab2, tab3, tab4 = st.tabs(["🌐 主域名配置", "🔑 关键词配置", "📧 邮箱配置", "⏱️ 高级参数"])
    
    # 1. 主域名配置
    with tab1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>主域名管理</div>", unsafe_allow_html=True)
        
        # 新增主域名表单（修复：缩进正确）
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            new_domain_name = st.text_input("新增主域名名称", placeholder="如：商务部官网", key="new_domain_name")
        with col2:
            new_domain_url = st.text_input("新增主域名URL", placeholder="如：https://www.mofcom.gov.cn/", key="new_domain_url")
        with col3:
            new_domain_remark = st.text_input("备注（可选）", placeholder="手动子链接，逗号分隔", key="new_domain_remark")
        
        # 添加按钮（修复：在tab1的with块内）
        if st.button("➕ 添加主域名", key="add_domain_primary"):
            if new_domain_name and new_domain_url:
                st.session_state.main_domains.append({
                    "id": str(uuid.uuid4()),
                    "name": new_domain_name,
                    "url": new_domain_url,
                    "remark": new_domain_remark
                })
                add_system_log(f"✅ 新增主域名：{new_domain_name}", "success")
                st.success("✅ 主域名添加成功！")
                st.rerun()
            else:
                st.error("❌ 名称和URL不能为空！")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # 主域名列表
        if st.session_state.main_domains:
            # 构建表格数据
            table_data = []
            for idx, domain in enumerate(st.session_state.main_domains):
                op_buttons = f"""
                <button class='op-btn op-edit' onclick="document.getElementById('edit_btn_{domain['id']}').click()">✏️ 修改</button>
                <button class='op-btn op-delete' onclick="document.getElementById('del_btn_{domain['id']}').click()">🗑️ 删除</button>
                """
                table_data.append({
                    "序号": idx+1,
                    "主域名名称": domain["name"],
                    "URL": domain["url"],
                    "备注": domain["remark"],
                    "操作": op_buttons
                })
            
            # 显示表格
            df_domains = pd.DataFrame(table_data)
            st.markdown(df_domains.to_html(escape=False, index=False, classes="data-table"), unsafe_allow_html=True)
            
            # 修改/删除逻辑（修复：Expander缩进正确）
            for domain in st.session_state.main_domains:
                # 隐藏的修改触发按钮
                st.button("修改触发", key=f"edit_btn_{domain['id']}", style={"display": "none"})
                # 隐藏的删除触发按钮
                st.button("删除触发", key=f"del_btn_{domain['id']}", style={"display": "none"})
                
                # 修改Expander（修复：key简化+缩进正确）
                if st.session_state.get(f"edit_btn_{domain['id']}", False):
                    with st.expander(f"修改主域名：{domain['name']}", expanded=True):
                        edit_name = st.text_input("新名称", value=domain["name"], key=f"edit_name_{domain['id']}")
                        edit_url = st.text_input("新URL", value=domain["url"], key=f"edit_url_{domain['id']}")
                        edit_remark = st.text_input("新备注", value=domain["remark"], key=f"edit_remark_{domain['id']}")
                        
                        if st.button("保存修改", key=f"save_domain_{domain['id']}_primary"):
                            for item in st.session_state.main_domains:
                                if item["id"] == domain["id"]:
                                    item["name"] = edit_name
                                    item["url"] = edit_url
                                    item["remark"] = edit_remark
                                    break
                            add_system_log(f"✅ 修改主域名：{edit_name}", "success")
                            st.success("✅ 主域名修改成功！")
                            st.rerun()
                
                # 删除逻辑
                if st.session_state.get(f"del_btn_{domain['id']}", False):
                    if st.button(f"确认删除 {domain['name']}", key=f"confirm_del_{domain['id']}_danger"):
                        st.session_state.main_domains = [d for d in st.session_state.main_domains if d["id"] != domain["id"]]
                        add_system_log(f"🗑️ 删除主域名：{domain['name']}", "info")
                        st.success(f"✅ 删除主域名：{domain['name']}")
                        st.rerun()
        else:
            st.markdown("<div style='text-align: center; padding: 20px; color: #86909C;'>暂无主域名配置</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 2. 关键词配置
    with tab2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>关键词管理</div>", unsafe_allow_html=True)
        
        # 新增关键词
        col1, col2 = st.columns([3, 1])
        with col1:
            new_keyword = st.text_input("新增关键词", placeholder="如：制裁 / sanctions", key="new_keyword")
        with col2:
            if st.button("➕ 添加关键词", key="add_kw_primary"):
                if new_keyword and new_keyword not in [k["content"] for k in st.session_state.keywords]:
                    st.session_state.keywords.append({"id": str(uuid.uuid4()), "content": new_keyword})
                    add_system_log(f"✅ 新增关键词：{new_keyword}", "success")
                    st.success("✅ 关键词添加成功！")
                    st.rerun()
                elif new_keyword in [k["content"] for k in st.session_state.keywords]:
                    st.error("❌ 关键词已存在！")
                else:
                    st.error("❌ 关键词不能为空！")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # 关键词列表
        if st.session_state.keywords:
            table_data = []
            for idx, kw in enumerate(st.session_state.keywords):
                op_buttons = f"""
                <button class='op-btn op-edit' onclick="document.getElementById('edit_kw_btn_{kw['id']}').click()">✏️ 修改</button>
                <button class='op-btn op-delete' onclick="document.getElementById('del_kw_btn_{kw['id']}').click()">🗑️ 删除</button>
                """
                table_data.append({
                    "序号": idx+1,
                    "关键词内容": kw["content"],
                    "操作": op_buttons
                })
            
            df_kw = pd.DataFrame(table_data)
            st.markdown(df_kw.to_html(escape=False, index=False, classes="data-table"), unsafe_allow_html=True)
            
            # 修改/删除逻辑
            for kw in st.session_state.keywords:
                st.button("修改触发", key=f"edit_kw_btn_{kw['id']}", style={"display": "none"})
                st.button("删除触发", key=f"del_kw_btn_{kw['id']}", style={"display": "none"})
                
                if st.session_state.get(f"edit_kw_btn_{kw['id']}", False):
                    with st.expander(f"修改关键词：{kw['content']}", expanded=True):
                        edit_kw = st.text_input("新关键词", value=kw["content"], key=f"edit_kw_{kw['id']}")
                        if st.button("保存修改", key=f"save_kw_{kw['id']}_primary"):
                            if edit_kw:
                                for item in st.session_state.keywords:
                                    if item["id"] == kw["id"]:
                                        item["content"] = edit_kw
                                        break
                                add_system_log(f"✅ 修改关键词：{edit_kw}", "success")
                                st.success("✅ 关键词修改成功！")
                                st.rerun()
                
                if st.session_state.get(f"del_kw_btn_{kw['id']}", False):
                    if st.button(f"确认删除 {kw['content']}", key=f"confirm_del_kw_{kw['id']}_danger"):
                        st.session_state.keywords = [k for k in st.session_state.keywords if k["id"] != kw["id"]]
                        add_system_log(f"🗑️ 删除关键词：{kw['content']}", "info")
                        st.success(f"✅ 删除关键词：{kw['content']}")
                        st.rerun()
        else:
            st.markdown("<div style='text-align: center; padding: 20px; color: #86909C;'>暂无关键词配置</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 3. 邮箱配置
    with tab3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>邮箱配置</div>", unsafe_allow_html=True)
        
        # 邮箱配置表单
        col1, col2 = st.columns(2)
        with col1:
            smtp_server = st.text_input("SMTP服务器", value=st.session_state.email_config["smtp_server"], 
                                       placeholder="如：smtp.exmail.qq.com", key="smtp_server")
            smtp_port = st.number_input("SMTP端口", value=st.session_state.email_config["smtp_port"], 
                                       min_value=1, max_value=65535, key="smtp_port")
            sender_email = st.text_input("发件邮箱", value=st.session_state.email_config["sender_email"], 
                                        placeholder="your@company.com", key="sender_email")
        with col2:
            sender_password = st.text_input("SMTP授权码", type="password", 
                                           value=st.session_state.email_config["sender_password"], 
                                           placeholder="邮箱授权码（非登录密码）", key="sender_password")
            receiver_email = st.text_input("收件邮箱", value=st.session_state.email_config["receiver_email"], 
                                          placeholder="recipient@company.com", key="receiver_email")
            st.markdown("<br>", unsafe_allow_html=True)
        
        # 保存邮箱配置
        if st.button("💾 保存邮箱配置", key="save_email_primary"):
            st.session_state.email_config = {
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "sender_email": sender_email,
                "sender_password": sender_password,
                "receiver_email": receiver_email
            }
            add_system_log("✅ 保存邮箱配置", "success")
            st.success("✅ 邮箱配置保存成功！")
        
        # 配置提示
        st.markdown("<div style='margin-top: 16px; padding: 12px; background-color: #F7F8FA; border-radius: 6px;'>", unsafe_allow_html=True)
        st.write("📌 提示：")
        st.write("1. SMTP服务器：企业邮箱一般为 smtp.exmail.qq.com（腾讯）/ smtp.163.com（网易）")
        st.write("2. 端口：SSL加密默认465，非加密默认25")
        st.write("3. 授权码：需在邮箱后台开启SMTP服务并生成")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 4. 高级参数配置
    with tab4:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>高级监控参数</div>", unsafe_allow_html=True)
        
        # 高级参数
        col1, col2 = st.columns(2)
        with col1:
            timeout = st.number_input("请求超时时间（秒）", value=15, min_value=5, max_value=60, key="req_timeout")
            sleep_time = st.number_input("抓取间隔（秒）", value=1, min_value=0, max_value=10, key="sleep_time")
        with col2:
            log_keep = st.number_input("日志保留条数", value=200, min_value=50, max_value=1000, key="log_keep")
            excel_engine = st.selectbox("Excel引擎", ["openpyxl", "xlsxwriter"], key="excel_engine")
        
        if st.button("💾 保存高级参数", key="save_advanced_primary"):
            add_system_log("✅ 保存高级参数配置", "success")
            st.success("✅ 高级参数保存成功！")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_report_management():
    """渲染报表管理"""
    st.markdown("<div class='main-content'>", unsafe_allow_html=True)
    st.markdown("<div class='module-title'>📁 报表管理</div>", unsafe_allow_html=True)
    
    # 报表筛选
    col1, col2 = st.columns(2)
    with col1:
        date_filter = st.date_input("筛选日期", value=datetime.now(), key="report_date_filter")
    with col2:
        file_type = st.selectbox("文件类型", ["所有Excel", "制裁监控报表"], key="report_file_type")
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-header'>报表列表</div>", unsafe_allow_html=True)
    
    # 报表列表
    excel_files = [f for f in os.listdir(".") if f.endswith(".xlsx") and "制裁监控报表" in f]
    if excel_files:
        filtered_files = []
        for file in excel_files:
            file_date = datetime.fromtimestamp(os.path.getctime(file)).date()
            if file_date == date_filter or not date_filter:
                filtered_files.append(file)
        
        if filtered_files:
            table_data = []
            for idx, file in enumerate(filtered_files):
                file_size = round(os.path.getsize(file) / 1024, 2)
                create_time = datetime.fromtimestamp(os.path.getctime(file)).strftime('%Y-%m-%d %H:%M:%S')
                op_buttons = f"""
                <button class='op-btn op-edit' onclick="document.getElementById('download_file_{idx}').click()">📥 下载</button>
                <button class='op-btn op-delete' onclick="document.getElementById('del_file_{idx}').click()">🗑️ 删除</button>
                """
                table_data.append({
                    "序号": idx+1,
                    "文件名": file,
                    "大小(KB)": file_size,
                    "创建时间": create_time,
                    "操作": op_buttons
                })
            
            df_reports = pd.DataFrame(table_data)
            st.markdown(df_reports.to_html(escape=False, index=False, classes="data-table"), unsafe_allow_html=True)
            
            # 下载/删除逻辑
            for idx, file in enumerate(filtered_files):
                # 下载按钮
                with open(file, "rb") as f:
                    st.download_button(
                        label="下载",
                        data=f,
                        file_name=file,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_file_{idx}",
                        style={"display": "none"}
                    )
                
                # 删除按钮
                if st.button(f"删除文件_{idx}", key=f"del_file_{idx}_danger", style={"display": "none"}):
                    try:
                        os.remove(file)
                        add_system_log(f"🗑️ 删除报表文件：{file}", "info")
                        st.success(f"✅ 删除报表：{file}")
                        st.rerun()
                    except Exception as e:
                        add_system_log(f"❌ 删除报表失败：{str(e)}", "error")
                        st.error(f"❌ 删除失败：{str(e)}")
        else:
            st.markdown("<div style='text-align: center; padding: 20px; color: #86909C;'>暂无符合条件的报表</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align: center; padding: 20px; color: #86909C;'>暂无报表文件</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_system_logs():
    """渲染系统日志"""
    st.markdown("<div class='main-content'>", unsafe_allow_html=True)
    st.markdown("<div class='module-title'>📜 系统日志</div>", unsafe_allow_html=True)
    
    # 日志筛选
    col1, col2 = st.columns(2)
    with col1:
        log_level = st.selectbox("日志级别", ["所有", "成功", "错误", "信息"], key="log_level_filter")
    with col2:
        if st.button("🗑️ 清空日志", key="clear_logs_danger"):
            st.session_state.system_logs = []
            add_system_log("✅ 清空系统日志", "info")
            st.success("✅ 日志已清空！")
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-header'>日志列表</div>", unsafe_allow_html=True)
    
    # 日志展示
    filtered_logs = st.session_state.system_logs
    if log_level != "所有":
        level_map = {"成功": "success", "错误": "error", "信息": "info"}
        filtered_logs = [log for log in st.session_state.system_logs if log[1] == level_map.get(log_level, "")]
    
    log_html = ""
    for log_entry, level in filtered_logs:
        if level == "success":
            log_html += f"<div class='log-success'>{log_entry}</div>"
        elif level == "error":
            log_html += f"<div class='log-error'>{log_entry}</div>"
        else:
            log_html += f"<div class='log-info'>{log_entry}</div>"
    
    st.markdown(f"<div class='log-container'>{log_html if log_html else '<div style=\"text-align: center; color: #86909C;\">暂无日志</div>'}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ===================== 5. 程序入口 =====================
if __name__ == "__main__":
    # 渲染左侧导航
    render_sidebar()
    
    # 渲染对应模块
    if st.session_state.active_module == "监控面板":
        render_monitor_panel()
    elif st.session_state.active_module == "配置中心":
        render_config_center()
    elif st.session_state.active_module == "报表管理":
        render_report_management()
    elif st.session_state.active_module == "系统日志":
        render_system_logs()
