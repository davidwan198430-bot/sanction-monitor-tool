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

# ===================== 1. 页面基础配置（专业工具UI） =====================
st.set_page_config(
    page_title="制裁监控工具",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS（企业级工具风格）
st.markdown("""
<style>
    /* 全局重置 */
    * {margin: 0; padding: 0; box-sizing: border-box;}
    .stApp {background-color: #F5F7FA; font-family: "Microsoft YaHei", sans-serif;}
    
    /* 顶部导航栏 */
    .navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 24px;
        background-color: #165DFF;
        border-radius: 8px;
        margin-bottom: 24px;
        color: white;
    }
    .navbar-title {font-size: 24px; font-weight: 600;}
    .navbar-right {display: flex; align-items: center; gap: 16px;}
    .status-tag {
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 14px;
        font-weight: 500;
    }
    .status-running {background-color: #00B42A;}
    .status-stopped {background-color: #F53F3F;}
    
    /* 卡片样式 */
    .card {
        background-color: white;
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 24px;
    }
    .card-title {
        font-size: 18px;
        font-weight: 600;
        color: #1D2129;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid #E5E6EB;
    }
    
    /* 按钮样式 */
    .btn {
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    .btn-primary {background-color: #165DFF; color: white;}
    .btn-primary:hover {background-color: #0E42CC;}
    .btn-secondary {background-color: #86909C; color: white;}
    .btn-secondary:hover {background-color: #6B7785;}
    .btn-danger {background-color: #F53F3F; color: white;}
    .btn-danger:hover {background-color: #D92D20;}
    .btn-success {background-color: #00B42A; color: white;}
    .btn-success:hover {background-color: #009A22;}
    .btn-warning {background-color: #FF7D00; color: white;}
    .btn-warning:hover {background-color: #E06F00;}
    
    /* 表格样式 */
    .dataframe {width: 100%; border-collapse: collapse;}
    .dataframe th {
        background-color: #F7F8FA;
        color: #1D2129;
        font-weight: 600;
        padding: 12px 8px;
        text-align: left;
        border-bottom: 2px solid #E5E6EB;
    }
    .dataframe td {
        padding: 12px 8px;
        border-bottom: 1px solid #E5E6EB;
        color: #4E5969;
    }
    .dataframe tr:hover {background-color: #F7F8FA;}
    
    /* 操作按钮 */
    .op-btn {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        border: none;
        cursor: pointer;
    }
    .op-edit {background-color: #FF7D00; color: white;}
    .op-delete {background-color: #F53F3F; color: white;}
    
    /* 日志区域 */
    .log-area {
        height: 300px;
        overflow-y: auto;
        background-color: #F7F8FA;
        border-radius: 6px;
        padding: 16px;
        font-size: 14px;
        color: #4E5969;
        line-height: 1.6;
    }
    .log-success {color: #00B42A;}
    .log-error {color: #F53F3F;}
    .log-info {color: #165DFF;}
</style>
""", unsafe_allow_html=True)

# ===================== 2. 全局会话状态初始化 =====================
# 核心状态
if "page" not in st.session_state:
    st.session_state.page = "main"
if "monitor_running" not in st.session_state:
    st.session_state.monitor_running = False
if "monitor_interval" not in st.session_state:
    st.session_state.monitor_interval = 900
if "time_range_days" not in st.session_state:
    st.session_state.time_range_days = 30
if "sent_content_hash" not in st.session_state:
    st.session_state.sent_content_hash = set()
if "logs" not in st.session_state:
    st.session_state.logs = []  # 实时日志缓存

# 主域名（默认数据）
if "main_domains" not in st.session_state:
    st.session_state.main_domains = [
        {"id": str(uuid.uuid4()), "name": "商务部官网", "url": "https://www.mofcom.gov.cn/", "remark": ""},
        {"id": str(uuid.uuid4()), "name": "美国财政部官网", "url": "https://www.treasury.gov/", "remark": ""},
        {"id": str(uuid.uuid4()), "name": "欧盟EEAS官网", "url": "https://eeas.europa.eu/", "remark": ""},
        {"id": str(uuid.uuid4()), "name": "中国出口管制信息网", "url": "https://www.ecrc.org.cn/", "remark": ""},
        {"id": str(uuid.uuid4()), "name": "外交部官网", "url": "https://www.mfa.gov.cn/", "remark": ""},
        {"id": str(uuid.uuid4()), "name": "海关总署官网", "url": "https://www.customs.gov.cn/", "remark": ""}
    ]

# 关键词（默认数据）
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

# ===================== 3. 工具函数 =====================
# 日志函数
def add_log(message, level="info"):
    """添加实时日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    st.session_state.logs.append((log_entry, level))
    # 保留最新100条日志
    if len(st.session_state.logs) > 100:
        st.session_state.logs = st.session_state.logs[-100:]

# 提取子链接
def extract_sub_links(main_url):
    filter_keywords = ["制裁", "反制", "出口管制", "实体清单", "公告", "政策", "sanctions", "export control"]
    invalid_patterns = [".jpg", ".png", ".pdf", ".doc", ".xls", "login", "register"]
    
    sub_links = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
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
        
        add_log(f"✅ 从【{main_url}】提取到 {len(sub_links)} 个相关子链接", "success")
        return sub_links
    
    except Exception as e:
        add_log(f"❌ 提取【{main_url}】子链接失败：{str(e)}", "error")
        return [main_url]

# 提取发布时间
def extract_publish_time(text, url):
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

# 时间筛选
def is_within_time_range(publish_time):
    cutoff_time = datetime.now() - timedelta(days=st.session_state.time_range_days)
    return publish_time >= cutoff_time

# 发送邮件
def send_email_with_excel(excel_path):
    if not excel_path:
        add_log("⚠️ 无Excel文件，跳过发邮件", "info")
        return
    if not all([st.session_state.email_config["sender_email"], st.session_state.email_config["receiver_email"], st.session_state.email_config["sender_password"]]):
        add_log("⚠️ 邮箱配置不完整，跳过发邮件", "info")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = st.session_state.email_config["sender_email"]
        msg['To'] = st.session_state.email_config["receiver_email"]
        msg['Subject'] = f"【制裁监控报表】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        body = f"""本次制裁监控结果：
1. 监控主域名数量：{len(st.session_state.main_domains)} 个
2. 监控时长：近 {st.session_state.time_range_days} 天
3. 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        with open(excel_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(excel_path)}"')
            msg.attach(part)
        
        with smtplib.SMTP_SSL(st.session_state.email_config["smtp_server"], st.session_state.email_config["smtp_port"]) as server:
            server.login(st.session_state.email_config["sender_email"], st.session_state.email_config["sender_password"])
            server.sendmail(st.session_state.email_config["sender_email"], st.session_state.email_config["receiver_email"], msg.as_string())
        
        add_log("✅ 邮件发送成功！", "success")
        st.success("✅ 邮件发送成功！")
    
    except Exception as e:
        add_log(f"❌ 邮件发送失败：{str(e)}", "error")
        st.error(f"❌ 邮件发送失败：{str(e)}")

# 生成Excel
def generate_excel(data):
    if not data:
        add_log("ℹ️ 未抓取到符合条件的内容，不生成Excel", "info")
        return None
    
    df = pd.DataFrame(data)
    excel_filename = f"制裁监控报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(excel_filename, index=False, engine='openpyxl')
    
    add_log(f"📊 Excel报表生成成功：{excel_filename}", "success")
    return excel_filename

# 抓取筛选
def crawl_and_filter():
    result_data = []
    add_log("🔍 开始执行监控任务...", "info")
    
    for domain in st.session_state.main_domains:
        domain_name = domain["name"]
        main_url = domain["url"]
        remark = domain["remark"]
        
        add_log(f"🔍 正在监控主域名：{domain_name}", "info")
        sub_links = extract_sub_links(main_url)
        
        if remark:
            manual_links = [link.strip() for link in remark.split(",") if link.strip()]
            sub_links.extend(manual_links)
            sub_links = list(set(sub_links))
        
        for link in sub_links:
            try:
                response = requests.get(link, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, verify=False)
                response.encoding = response.apparent_encoding
                pure_text = re.sub(r'<[^>]+>', '', response.text).strip()
                content_hash = hash(pure_text[:1000])
                
                if content_hash in st.session_state.sent_content_hash:
                    add_log(f"⏭️ 【{link}】内容已发送过，跳过", "info")
                    continue
                
                publish_time = extract_publish_time(pure_text, link)
                if not is_within_time_range(publish_time):
                    add_log(f"⏳ 【{link}】内容超出{st.session_state.time_range_days}天，跳过", "info")
                    continue
                
                kw_list = [item["content"] for item in st.session_state.keywords]
                hit_keywords = [kw for kw in kw_list if kw.lower() in pure_text.lower()]
                if not hit_keywords:
                    add_log(f"🔍 【{link}】未命中关键词，跳过", "info")
                    continue
                
                result_data.append({
                    "主域名": domain_name,
                    "子链接": link,
                    "命中关键词": ",".join(hit_keywords),
                    "发布时间": publish_time.strftime('%Y-%m-%d'),
                    "监控时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "内容摘要": pure_text[:500]
                })
                
                st.session_state.sent_content_hash.add(content_hash)
                add_log(f"✅ 【{link}】命中关键词：{','.join(hit_keywords[:3])}...", "success")
                time.sleep(1)
            
            except Exception as e:
                add_log(f"❌ 抓取【{link}】失败：{str(e)}", "error")
                continue
    
    add_log(f"🔍 监控任务执行完成，共抓取到 {len(result_data)} 条有效数据", "info")
    return result_data

# 监控循环
def monitor_loop():
    while st.session_state.monitor_running:
        monitor_data = crawl_and_filter()
        excel_path = generate_excel(monitor_data)
        send_email_with_excel(excel_path)
        
        wait_time = st.session_state.monitor_interval
        for i in range(wait_time, 0, -1):
            if not st.session_state.monitor_running:
                break
            add_log(f"⏱️ 下次监控将在 {i} 秒后执行", "info")
            time.sleep(1)

# ===================== 4. 页面渲染 =====================
# 4.1 主页渲染
def render_main_page():
    # 顶部导航栏
    st.markdown(f"""
    <div class="navbar">
        <div class="navbar-title">🚨 制裁监控工具</div>
        <div class="navbar-right">
            <div class="status-tag {'status-running' if st.session_state.monitor_running else 'status-stopped'}">
                {'🟢 监控运行中' if st.session_state.monitor_running else '🔴 监控已停止'}
            </div>
            <button class="btn btn-secondary" onclick="window.location.reload(true)">
                ⚙️ 配置管理
            </button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 监控状态同步（解决按钮点击后状态不刷新）
    if st.session_state.monitor_running:
        st.session_state.page = "main"
    
    # 中部核心区
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🎮 监控控制</div>', unsafe_allow_html=True)
        
        # 控制按钮
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("▶️ 开启监控", key="start_btn", use_container_width=True):
                st.session_state.monitor_running = True
                add_log("🚀 监控已启动", "success")
                st.rerun()
        with btn_col2:
            if st.button("⏹️ 停止监控", key="stop_btn", use_container_width=True, disabled=not st.session_state.monitor_running):
                st.session_state.monitor_running = False
                add_log("🛑 监控已停止", "info")
                st.rerun()
        
        # 监控参数
        st.markdown("### 📋 监控参数")
        st.write(f"• 监控时长：{st.session_state.time_range_days} 天")
        st.write(f"• 执行频率：{st.session_state.monitor_interval//60} 分钟")
        st.write(f"• 主域名数量：{len(st.session_state.main_domains)} 个")
        st.write(f"• 关键词数量：{len(st.session_state.keywords)} 个")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">📊 配置摘要</div>', unsafe_allow_html=True)
        
        # 配置摘要卡片
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        with stat_col1:
            st.markdown(f"""
            <div style="background: #E8F3FF; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 28px; font-weight: 600; color: #165DFF;">{len(st.session_state.main_domains)}</div>
                <div style="font-size: 14px; color: #4E5969;">监控主域名</div>
            </div>
            """, unsafe_allow_html=True)
        with stat_col2:
            st.markdown(f"""
            <div style="background: #E8F3FF; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 28px; font-weight: 600; color: #165DFF;">{len(st.session_state.keywords)}</div>
                <div style="font-size: 14px; color: #4E5969;">监控关键词</div>
            </div>
            """, unsafe_allow_html=True)
        with stat_col3:
            st.markdown(f"""
            <div style="background: #E8F3FF; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 28px; font-weight: 600; color: #165DFF;">{st.session_state.monitor_interval//60}</div>
                <div style="font-size: 14px; color: #4E5969;">执行频率(分钟)</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 报表下载区
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📁 报表下载</div>', unsafe_allow_html=True)
    
    excel_files = [f for f in os.listdir(".") if f.endswith(".xlsx") and "制裁监控报表" in f]
    if excel_files:
        file_data = []
        for idx, file in enumerate(excel_files):
            file_data.append({
                "序号": idx+1,
                "文件名": file,
                "创建时间": datetime.fromtimestamp(os.path.getctime(file)).strftime('%Y-%m-%d %H:%M:%S'),
                "操作": f"<a href='#' download='{file}'><button class='btn btn-success'>📥 下载</button></a>"
            })
        df_files = pd.DataFrame(file_data)
        st.markdown(df_files.to_html(escape=False, index=False, classes="dataframe"), unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align: center; padding: 24px; color: #86909C;'>暂无报表文件</div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 日志区域
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📜 实时日志</div>', unsafe_allow_html=True)
    
    log_html = ""
    for log_entry, level in st.session_state.logs:
        if level == "success":
            log_html += f"<div class='log-success'>{log_entry}</div>"
        elif level == "error":
            log_html += f"<div class='log-error'>{log_entry}</div>"
        else:
            log_html += f"<div class='log-info'>{log_entry}</div>"
    
    st.markdown(f"<div class='log-area'>{log_html}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 启动监控循环
    if st.session_state.monitor_running:
        monitor_loop()

# 4.2 配置页渲染
def render_config_page():
    # 顶部导航
    st.markdown("""
    <div class="navbar">
        <button class="btn btn-secondary" onclick="window.location.reload(true)">⬅️ 返回主界面</button>
        <div class="navbar-title">⚙️ 制裁监控工具 - 配置中心</div>
        <div></div>
    </div>
    """, unsafe_allow_html=True)
    
    # 标签页
    tab1, tab2, tab3, tab4 = st.tabs(["🌐 主域名配置", "🔑 关键词配置", "📧 邮箱配置", "⏱️ 监控参数"])
    
    # 4.2.1 主域名配置
    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">主域名管理</div>', unsafe_allow_html=True)
        
        # 新增按钮
        st.markdown("""
        <div style="margin-bottom: 16px;">
            <button class="btn btn-primary" id="add-domain-btn">➕ 添加主域名</button>
        </div>
        """, unsafe_allow_html=True)
        
        # 新增表单
        with st.expander("新增主域名", expanded=False):
            new_name = st.text_input("主域名名称")
            new_url = st.text_input("主域名URL")
            new_remark = st.text_input("备注（可选：手动子链接，逗号分隔）")
            if st.button("保存新增", key="add_domain_save"):
                if new_name and new_url:
                    st.session_state.main_domains.append({
                        "id": str(uuid.uuid4()),
                        "name": new_name,
                        "url": new_url,
                        "remark": new_remark
                    })
                    add_log(f"✅ 新增主域名：{new_name}", "success")
                    st.rerun()
                else:
                    st.error("❌ 名称和URL不能为空！")
        
        # 主域名表格
        if st.session_state.main_domains:
            table_data = []
            for idx, domain in enumerate(st.session_state.main_domains):
                # 操作列按钮
                op_buttons = f"""
                <button class="op-btn op-edit" onclick="document.getElementById('edit-{domain['id']}').click()">✏️ 修改</button>
                <button class="op-btn op-delete" onclick="document.getElementById('del-{domain['id']}').click()">🗑️ 删除</button>
                """
                
                table_data.append({
                    "序号": idx+1,
                    "主域名名称": domain["name"],
                    "URL": domain["url"],
                    "备注": domain["remark"],
                    "操作": op_buttons
                })
            
            # 显示表格
            df = pd.DataFrame(table_data)
            st.markdown(df.to_html(escape=False, index=False, classes="dataframe"), unsafe_allow_html=True)
            
            # 修改/删除逻辑
            for domain in st.session_state.main_domains:
                # 修改表单
                with st.expander(f"修改：{domain['name']}", expanded=False, key=f"edit-{domain['id']}"):
                    edit_name = st.text_input("新名称", value=domain["name"], key=f"edit_name_{domain['id']}")
                    edit_url = st.text_input("新URL", value=domain["url"], key=f"edit_url_{domain['id']}")
                    edit_remark = st.text_input("新备注", value=domain["remark"], key=f"edit_remark_{domain['id']}")
                    if st.button("保存修改", key=f"save_edit_{domain['id']}"):
                        for item in st.session_state.main_domains:
                            if item["id"] == domain["id"]:
                                item["name"] = edit_name
                                item["url"] = edit_url
                                item["remark"] = edit_remark
                                break
                        add_log(f"✅ 修改主域名：{edit_name}", "success")
                        st.rerun()
                
                # 删除按钮
                if st.button(f"删除 {domain['name']}", key=f"del-{domain['id']}", style={"display": "none"}):
                    st.session_state.main_domains = [item for item in st.session_state.main_domains if item["id"] != domain["id"]]
                    add_log(f"🗑️ 删除主域名：{domain['name']}", "info")
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 4.2.2 关键词配置
    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">关键词管理</div>', unsafe_allow_html=True)
        
        # 新增按钮
        st.markdown("""
        <div style="margin-bottom: 16px;">
            <button class="btn btn-primary">➕ 添加关键词</button>
        </div>
        """, unsafe_allow_html=True)
        
        # 新增表单
        with st.expander("新增关键词", expanded=False):
            new_kw = st.text_input("关键词内容")
            if st.button("保存关键词", key="add_kw_save"):
                if new_kw:
                    st.session_state.keywords.append({
                        "id": str(uuid.uuid4()),
                        "content": new_kw
                    })
                    add_log(f"✅ 新增关键词：{new_kw}", "success")
                    st.rerun()
                else:
                    st.error("❌ 关键词不能为空！")
        
        # 关键词表格
        if st.session_state.keywords:
            table_data = []
            for idx, kw in enumerate(st.session_state.keywords):
                op_buttons = f"""
                <button class="op-btn op-edit" onclick="document.getElementById('edit-kw-{kw['id']}').click()">✏️ 修改</button>
                <button class="op-btn op-delete" onclick="document.getElementById('del-kw-{kw['id']}').click()">🗑️ 删除</button>
                """
                
                table_data.append({
                    "序号": idx+1,
                    "关键词内容": kw["content"],
                    "操作": op_buttons
                })
            
            df = pd.DataFrame(table_data)
            st.markdown(df.to_html(escape=False, index=False, classes="dataframe"), unsafe_allow_html=True)
            
            # 修改/删除逻辑
            for kw in st.session_state.keywords:
                with st.expander(f"修改：{kw['content']}", expanded=False, key=f"edit-kw-{kw['id']}"):
                    edit_kw = st.text_input("新关键词", value=kw["content"], key=f"edit_kw_{kw['id']}")
                    if st.button("保存修改", key=f"save_kw_{kw['id']}"):
                        if edit_kw:
                            for item in st.session_state.keywords:
                                if item["id"] == kw["id"]:
                                    item["content"] = edit_kw
                                    break
                            add_log(f"✅ 修改关键词：{edit_kw}", "success")
                            st.rerun()
                
                if st.button(f"删除 {kw['content']}", key=f"del-kw-{kw['id']}", style={"display": "none"}):
                    st.session_state.keywords = [item for item in st.session_state.keywords if item["id"] != kw["id"]]
                    add_log(f"🗑️ 删除关键词：{kw['content']}", "info")
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 4.2.3 邮箱配置
    with tab3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">邮箱配置</div>', unsafe_allow_html=True)
        
        # 邮箱配置表单
        col1, col2 = st.columns(2)
        with col1:
            smtp_server = st.text_input("SMTP服务器", value=st.session_state.email_config["smtp_server"])
            smtp_port = st.number_input("SMTP端口", value=st.session_state.email_config["smtp_port"])
            sender_email = st.text_input("发件邮箱", value=st.session_state.email_config["sender_email"])
        with col2:
            sender_password = st.text_input("SMTP授权码", type="password", value=st.session_state.email_config["sender_password"])
            receiver_email = st.text_input("收件邮箱", value=st.session_state.email_config["receiver_email"])
        
        if st.button("💾 保存邮箱配置", key="save_email", class_="btn btn-primary"):
            st.session_state.email_config = {
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "sender_email": sender_email,
                "sender_password": sender_password,
                "receiver_email": receiver_email
            }
            add_log("✅ 邮箱配置保存成功", "success")
            st.success("✅ 邮箱配置保存成功！")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 4.2.4 监控参数
    with tab4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">监控参数配置</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            time_range = st.selectbox(
                "监控时长范围",
                ["1天", "3天", "7天", "30天"],
                index=["1天", "3天", "7天", "30天"].index(f"{st.session_state.time_range_days}天")
            )
            st.session_state.time_range_days = int(time_range.replace("天", ""))
        
        with col2:
            monitor_interval = st.slider(
                "监控频率（分钟）",
                1, 60,
                st.session_state.monitor_interval//60
            )
            st.session_state.monitor_interval = monitor_interval * 60
        
        if st.button("💾 保存参数配置", key="save_param", class_="btn btn-primary"):
            add_log("✅ 监控参数保存成功", "success")
            st.success("✅ 监控参数保存成功！")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ===================== 5. 程序入口 =====================
if __name__ == "__main__":
    # 处理页面切换
    query_params = st.query_params
    if "page" in query_params and query_params["page"] == "config":
        st.session_state.page = "config"
    else:
        st.session_state.page = "main"
    
    # 渲染对应页面
    if st.session_state.page == "main":
        render_main_page()
    else:
        render_config_page()
    
    # 页面切换JS
    st.markdown("""
    <script>
        // 配置按钮点击事件
        document.querySelector('.navbar-right .btn-secondary').addEventListener('click', function() {
            window.location.href = window.location.href.split('?')[0] + '?page=config';
        });
        
        // 返回按钮点击事件
        document.querySelector('.navbar .btn-secondary').addEventListener('click', function() {
            window.location.href = window.location.href.split('?')[0];
        });
        
        // 新增按钮点击事件
        document.getElementById('add-domain-btn').addEventListener('click', function() {
            document.querySelector('div[data-testid="stExpander"] button').click();
        });
    </script>
    """, unsafe_allow_html=True)
