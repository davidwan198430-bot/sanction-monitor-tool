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

# ===================== 1. 页面基础配置（工具风格UI） =====================
st.set_page_config(
    page_title="制裁监控工具",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed"  # 隐藏侧边栏，改用设置页
)

# 自定义CSS（桌面工具风格）
st.markdown("""
<style>
    /* 全局样式 */
    .main {background-color: #f8f9fa; padding: 20px;}
    .tool-title {font-size: 2.8rem; color: #2c3e50; text-align: center; margin-bottom: 30px; font-weight: bold;}
    .status-card {background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px;}
    .btn-primary {background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-size: 1rem; cursor: pointer;}
    .btn-secondary {background-color: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-size: 1rem; cursor: pointer;}
    .config-page {background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);}
    .table-container {margin: 20px 0;}
    .stTable {width: 100%; border-collapse: collapse;}
    .stTable th {background-color: #007bff; color: white; padding: 10px; text-align: left;}
    .stTable td {padding: 10px; border-bottom: 1px solid #dee2e6;}
    .operation-btn {padding: 5px 10px; border-radius: 3px; border: none; cursor: pointer; margin: 0 2px;}
    .add-btn {background-color: #28a745; color: white;}
    .edit-btn {background-color: #ffc107; color: black;}
    .delete-btn {background-color: #dc3545; color: white;}
</style>
""", unsafe_allow_html=True)

# ===================== 2. 全局会话状态初始化 =====================
# 初始化核心状态
if "page" not in st.session_state:
    st.session_state.page = "main"  # main:主界面, config:设置页
if "monitor_running" not in st.session_state:
    st.session_state.monitor_running = False
if "monitor_interval" not in st.session_state:
    st.session_state.monitor_interval = 900  # 默认15分钟（900秒）
if "time_range_days" not in st.session_state:
    st.session_state.time_range_days = 30  # 默认监控近30天
if "sent_content_hash" not in st.session_state:
    st.session_state.sent_content_hash = set()  # 去重缓存

# 初始化顶级主域名（仅展示根域名，默认数据）
if "main_domains" not in st.session_state:
    st.session_state.main_domains = [
        {"name": "商务部官网", "url": "https://www.mofcom.gov.cn/", "remark": ""},
        {"name": "美国财政部官网", "url": "https://www.treasury.gov/", "remark": ""},
        {"name": "欧盟EEAS官网", "url": "https://eeas.europa.eu/", "remark": ""},
        {"name": "中国出口管制信息网", "url": "https://www.ecrc.org.cn/", "remark": ""},
        {"name": "外交部官网", "url": "https://www.mfa.gov.cn/", "remark": ""},
        {"name": "海关总署官网", "url": "https://www.customs.gov.cn/", "remark": ""},
        {"name": "英国OFSI官网", "url": "https://www.gov.uk/government/organisations/office-of-financial-sanctions-implementation", "remark": ""},
        {"name": "联合国安理会官网", "url": "https://www.un.org/securitycouncil/committees/index.html", "remark": ""},
        {"name": "澳大利亚DFAT官网", "url": "https://www.dfat.gov.au/international-relations/sanctions", "remark": ""},
        {"name": "加拿大Global Affairs官网", "url": "https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/index.aspx", "remark": ""}
    ]

# 初始化全量关键词（默认数据）
if "keywords" not in st.session_state:
    st.session_state.keywords = [
        # 中文关键词
        "制裁", "反制", "出口管制", "实体清单", "未核实清单", "军事最终用户",
        "制裁清单", "出口许可", "技术出口限制", "制裁措施", "贸易限制", "经济制裁",
        "定向制裁", "制裁名单", "禁运", "限制性措施", "长臂管辖", "出口禁令",
        "最终用户核查", "两用物项", "无人机管制", "航空制造管制", "导航系统管制",
        "飞行控制管制", "遥感技术管制",
        # 英文关键词
        "sanctions", "countermeasures", "export control", "entity list",
        "unverified list", "military end user", "sanctions list", "export license",
        "technology export restrictions", "sanctions measures", "trade restrictions",
        "economic sanctions", "targeted sanctions", "embargo", "restrictive measures",
        "extraterritorial jurisdiction", "export ban", "end-user verification",
        "dual-use items", "UAV", "aviation manufacturing"
    ]

# 初始化邮箱配置
if "email_config" not in st.session_state:
    st.session_state.email_config = {
        "smtp_server": "smtp.exmail.qq.com",
        "smtp_port": 465,
        "sender_email": "",
        "sender_password": "",
        "receiver_email": ""
    }

# ===================== 3. 核心功能函数 =====================
# 3.1 提取主域名下所有相关子链接（无数量限制）
def extract_sub_links(main_url):
    """从主域名首页提取所有相关子域名/子页面链接"""
    # 相关关键词过滤
    filter_keywords = ["制裁", "反制", "出口管制", "实体清单", "公告", "政策", "清单", "管制",
                       "sanctions", "countermeasures", "export control", "entity list", 
                       "notice", "policy", "list", "restrictions"]
    # 无效链接过滤
    invalid_patterns = [".jpg", ".png", ".pdf", ".doc", ".xls", "login", "register", "logout", 
                        "advertisement", "banner", "css", "js", "ico", "svg"]
    
    sub_links = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }
    
    try:
        # 抓取主域名首页
        response = requests.get(main_url, headers=headers, timeout=15, verify=False)
        response.encoding = response.apparent_encoding
        
        # 提取所有链接
        all_links = re.findall(r'href=["\'](.*?)["\']', response.text)
        
        for link in all_links:
            # 拼接完整URL
            full_link = urljoin(main_url, link)
            # 过滤无效链接
            if any(invalid in full_link.lower() for invalid in invalid_patterns):
                continue
            # 过滤相关链接
            if any(kw in full_link.lower() or kw in response.text.lower() for kw in filter_keywords):
                sub_links.append(full_link)
        
        # 去重（无数量限制）
        sub_links = list(set(sub_links))
        
        # 兜底：无结果则抓取主域名本身
        if not sub_links:
            sub_links = [main_url]
            
        st.info(f"✅ 从【{main_url}】提取到 {len(sub_links)} 个相关子链接")
        return sub_links
    
    except Exception as e:
        st.warning(f"❌ 提取【{main_url}】子链接失败：{str(e)}，仅抓取主域名本身")
        return [main_url]

# 3.2 提取发布时间
def extract_publish_time(text, url):
    """从网页内容提取发布时间"""
    time_patterns = [
        r'(\d{4})[-/年](\d{2})[-/月](\d{2})日?',
        r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})'
    ]
    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                year, month, day = match.groups()[:3]
                return datetime(int(year), int(month), int(day))
            except:
                continue
    return datetime.now()

# 3.3 时间范围筛选
def is_within_time_range(publish_time):
    """判断是否在监控时长内"""
    cutoff_time = datetime.now() - timedelta(days=st.session_state.time_range_days)
    return publish_time >= cutoff_time

# 3.4 发送带Excel的邮件
def send_email_with_excel(excel_path):
    """发送邮件（带Excel附件）"""
    # 检查配置完整性
    if not excel_path:
        st.warning("⚠️ 无Excel文件，跳过发邮件")
        return
    if not all([st.session_state.email_config["sender_email"], 
                st.session_state.email_config["receiver_email"], 
                st.session_state.email_config["sender_password"]]):
        st.warning("⚠️ 邮箱配置不完整，跳过发邮件")
        return
    
    try:
        # 构建邮件
        msg = MIMEMultipart()
        msg['From'] = st.session_state.email_config["sender_email"]
        msg['To'] = st.session_state.email_config["receiver_email"]
        msg['Subject'] = f"【制裁监控报表】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 邮件正文
        body = f"""
本次制裁监控结果如下：
1. 监控主域名数量：{len(st.session_state.main_domains)} 个
2. 监控时长范围：近 {st.session_state.time_range_days} 天
3. 监控执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
4. 报表文件：{os.path.basename(excel_path)}

详情请查看附件。
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 添加Excel附件
        with open(excel_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(excel_path)}"')
            msg.attach(part)
        
        # 发送邮件
        with smtplib.SMTP_SSL(st.session_state.email_config["smtp_server"], 
                              st.session_state.email_config["smtp_port"]) as server:
            server.login(st.session_state.email_config["sender_email"], 
                         st.session_state.email_config["sender_password"])
            server.sendmail(st.session_state.email_config["sender_email"], 
                            st.session_state.email_config["receiver_email"], 
                            msg.as_string())
        
        st.success("✅ 邮件发送成功！")
    
    except Exception as e:
        st.error(f"❌ 邮件发送失败：{str(e)}")

# 3.5 生成Excel报表
def generate_excel(data):
    """生成Excel报表"""
    if not data:
        st.info("ℹ️ 未抓取到符合条件的内容，不生成Excel")
        return None
    
    # 构建DataFrame
    df = pd.DataFrame(data)
    # 生成文件名
    excel_filename = f"制裁监控报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    # 保存Excel
    df.to_excel(excel_filename, index=False, engine='openpyxl')
    
    st.success(f"📊 Excel报表生成成功：{excel_filename}")
    return excel_filename

# 3.6 核心抓取筛选逻辑
def crawl_and_filter():
    """抓取所有主域名+子链接，筛选符合条件的内容"""
    result_data = []
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 遍历所有主域名
    for domain in st.session_state.main_domains:
        domain_name = domain["name"]
        main_url = domain["url"]
        remark = domain["remark"]
        
        st.subheader(f"🔍 正在监控：{domain_name}")
        
        # 1. 提取子链接（含手动备注的链接）
        sub_links = extract_sub_links(main_url)
        # 添加手动备注的链接（如果有）
        if remark:
            manual_links = [link.strip() for link in remark.split(",") if link.strip()]
            sub_links.extend(manual_links)
            sub_links = list(set(sub_links))  # 去重
        
        # 2. 遍历所有子链接抓取内容
        for link in sub_links:
            try:
                # 抓取页面内容
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = requests.get(link, headers=headers, timeout=15, verify=False)
                response.encoding = response.apparent_encoding
                # 提取纯文本（去掉HTML标签）
                pure_text = re.sub(r'<[^>]+>', '', response.text).strip()
                # 内容去重哈希
                content_hash = hash(pure_text[:1000])
                
                # 3. 去重筛选
                if content_hash in st.session_state.sent_content_hash:
                    st.info(f"⏭️ 【{link}】内容已发送过，跳过")
                    continue
                
                # 4. 时间筛选
                publish_time = extract_publish_time(pure_text, link)
                if not is_within_time_range(publish_time):
                    st.info(f"⏳ 【{link}】内容发布时间超出{st.session_state.time_range_days}天，跳过")
                    continue
                
                # 5. 关键词筛选
                hit_keywords = [kw for kw in st.session_state.keywords if kw.lower() in pure_text.lower()]
                if not hit_keywords:
                    st.info(f"🔍 【{link}】未命中关键词，跳过")
                    continue
                
                # 6. 记录有效数据
                result_data.append({
                    "主域名名称": domain_name,
                    "子链接URL": link,
                    "命中关键词": ",".join(hit_keywords),
                    "发布时间": publish_time.strftime('%Y-%m-%d'),
                    "监控时间": current_time,
                    "内容摘要": pure_text[:500]  # 仅保留前500字摘要
                })
                
                # 加入去重缓存
                st.session_state.sent_content_hash.add(content_hash)
                st.success(f"✅ 【{link}】命中关键词：{','.join(hit_keywords[:3])}...")
                
                # 休眠1秒（避免反爬）
                time.sleep(1)
            
            except Exception as e:
                st.error(f"❌ 抓取【{link}】失败：{str(e)}")
                continue
    
    return result_data

# 3.7 监控主循环
def monitor_loop():
    """监控主循环"""
    while st.session_state.monitor_running:
        # 1. 抓取筛选数据
        monitor_data = crawl_and_filter()
        # 2. 生成Excel
        excel_path = generate_excel(monitor_data)
        # 3. 发送邮件
        send_email_with_excel(excel_path)
        
        # 4. 倒计时等待下一次执行
        wait_time = st.session_state.monitor_interval
        for i in range(wait_time, 0, -1):
            if not st.session_state.monitor_running:
                break
            st.info(f"⏱️ 下次监控将在 {i} 秒后执行（点击「停止监控」可终止）")
            time.sleep(1)

# ===================== 4. 界面设计 =====================
# 4.1 主界面
def render_main_page():
    """渲染主界面"""
    # 标题
    st.markdown("<h1 class='tool-title'>🚨 制裁监控工具</h1>", unsafe_allow_html=True)
    
    # 状态卡片
    st.markdown("<div class='status-card'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    # 监控状态
    with col1:
        st.subheader("监控状态")
        if st.session_state.monitor_running:
            st.markdown("<h3 style='color: #28a745;'>🟢 运行中</h3>", unsafe_allow_html=True)
        else:
            st.markdown("<h3 style='color: #dc3545;'>🔴 已停止</h3>", unsafe_allow_html=True)
    
    # 核心按钮
    with col2:
        st.subheader("操作控制")
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("▶️ 开启监控", type="primary", disabled=st.session_state.monitor_running):
                st.session_state.monitor_running = True
                st.rerun()
        with btn_col2:
            if st.button("⏹️ 停止监控", disabled=not st.session_state.monitor_running):
                st.session_state.monitor_running = False
                st.rerun()
    
    # 设置按钮
    with col3:
        st.subheader("系统设置")
        if st.button("⚙️ 配置管理", type="secondary"):
            st.session_state.page = "config"
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 配置摘要
    st.markdown("<div class='status-card'>", unsafe_allow_html=True)
    st.subheader("📋 当前配置摘要")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("监控主域名数", len(st.session_state.main_domains))
    with col2:
        st.metric("监控关键词数", len(st.session_state.keywords))
    with col3:
        st.metric("监控时长", f"{st.session_state.time_range_days}天")
    with col4:
        st.metric("监控频率", f"{st.session_state.monitor_interval//60}分钟")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 报表下载区
    st.markdown("<div class='status-card'>", unsafe_allow_html=True)
    st.subheader("📁 报表下载")
    excel_files = [f for f in os.listdir(".") if f.endswith(".xlsx") and "制裁监控报表" in f]
    if excel_files:
        selected_excel = st.selectbox("选择要下载的报表", excel_files)
        with open(selected_excel, "rb") as f:
            st.download_button("📥 下载Excel报表", f, file_name=selected_excel)
    else:
        st.info("ℹ️ 暂无报表文件")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 监控日志区
    st.markdown("<div class='status-card'>", unsafe_allow_html=True)
    st.subheader("📜 监控日志")
    st.info("监控启动后，日志将在此处实时显示...")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 运行监控循环
    if st.session_state.monitor_running:
        monitor_loop()

# 4.2 设置页（表格化配置）
def render_config_page():
    """渲染配置页"""
    # 标题 + 返回按钮
    st.markdown("<h1 class='tool-title'>⚙️ 制裁监控工具 - 配置中心</h1>", unsafe_allow_html=True)
    if st.button("⬅️ 返回主界面", type="secondary"):
        st.session_state.page = "main"
        st.rerun()
    
    # 配置标签页
    tab1, tab2, tab3, tab4 = st.tabs(["🌐 主域名配置", "🔑 关键词配置", "📧 邮箱配置", "⏱️ 监控参数"])
    
    # 4.2.1 主域名配置（表格）
    with tab1:
        st.markdown("<div class='config-page'>", unsafe_allow_html=True)
        st.subheader("主域名列表（仅展示顶级根域名）")
        
        # 显示主域名表格
        if st.session_state.main_domains:
            # 准备表格数据
            domain_data = []
            for idx, domain in enumerate(st.session_state.main_domains):
                domain_data.append({
                    "序号": idx+1,
                    "主域名名称": domain["name"],
                    "主域名URL": domain["url"],
                    "备注（手动子链接）": domain["remark"],
                    "操作": ""
                })
            
            # 显示表格
            df_domains = pd.DataFrame(domain_data)
            st.dataframe(df_domains, use_container_width=True)
            
            # 操作区：修改/删除
            st.subheader("操作主域名")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 修改主域名")
                domain_idx = st.number_input("选择要修改的序号", 1, len(st.session_state.main_domains), 1) - 1
                new_name = st.text_input("新名称", value=st.session_state.main_domains[domain_idx]["name"])
                new_url = st.text_input("新URL", value=st.session_state.main_domains[domain_idx]["url"])
                new_remark = st.text_input("新备注（多个链接用逗号分隔）", value=st.session_state.main_domains[domain_idx]["remark"])
                if st.button("✏️ 保存修改", key="edit_domain"):
                    st.session_state.main_domains[domain_idx] = {
                        "name": new_name,
                        "url": new_url,
                        "remark": new_remark
                    }
                    st.success("✅ 主域名修改成功！")
                    st.rerun()
            
            with col2:
                st.markdown("### 删除主域名")
                del_idx = st.number_input("选择要删除的序号", 1, len(st.session_state.main_domains), 1) - 1
                if st.button("🗑️ 删除选中主域名", key="del_domain"):
                    del st.session_state.main_domains[del_idx]
                    st.success("✅ 主域名删除成功！")
                    st.rerun()
        
        # 添加新主域名
        st.subheader("添加新主域名")
        new_domain_name = st.text_input("主域名名称（如：商务部官网）")
        new_domain_url = st.text_input("主域名URL（如：https://www.mofcom.gov.cn/）")
        new_domain_remark = st.text_input("备注（可选：手动补充的子链接，多个用逗号分隔）")
        if st.button("➕ 添加主域名", key="add_domain"):
            if new_domain_name and new_domain_url:
                st.session_state.main_domains.append({
                    "name": new_domain_name,
                    "url": new_domain_url,
                    "remark": new_domain_remark
                })
                st.success(f"✅ 新增主域名：{new_domain_name}")
                st.rerun()
            else:
                st.error("❌ 名称和URL不能为空！")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 4.2.2 关键词配置（表格）
    with tab2:
        st.markdown("<div class='config-page'>", unsafe_allow_html=True)
        st.subheader("关键词列表")
        
        # 显示关键词表格
        if st.session_state.keywords:
            keyword_data = []
            for idx, kw in enumerate(st.session_state.keywords):
                keyword_data.append({
                    "序号": idx+1,
                    "关键词内容": kw,
                    "操作": ""
                })
            df_kw = pd.DataFrame(keyword_data)
            st.dataframe(df_kw, use_container_width=True)
            
            # 操作区
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 修改关键词")
                kw_idx = st.number_input("选择要修改的序号", 1, len(st.session_state.keywords), 1) - 1
                new_kw = st.text_input("新关键词", value=st.session_state.keywords[kw_idx])
                if st.button("✏️ 保存修改", key="edit_kw"):
                    if new_kw:
                        st.session_state.keywords[kw_idx] = new_kw
                        st.success("✅ 关键词修改成功！")
                        st.rerun()
                    else:
                        st.error("❌ 关键词不能为空！")
            
            with col2:
                st.markdown("### 删除关键词")
                del_kw_idx = st.number_input("选择要删除的序号", 1, len(st.session_state.keywords), 1) - 1
                if st.button("🗑️ 删除选中关键词", key="del_kw"):
                    del st.session_state.keywords[del_kw_idx]
                    st.success("✅ 关键词删除成功！")
                    st.rerun()
        
        # 添加新关键词
        st.subheader("添加新关键词")
        new_keyword = st.text_input("输入新关键词（中文/英文均可）")
        if st.button("➕ 添加关键词", key="add_kw"):
            if new_keyword and new_keyword not in st.session_state.keywords:
                st.session_state.keywords.append(new_keyword)
                st.success(f"✅ 新增关键词：{new_keyword}")
                st.rerun()
            elif new_keyword in st.session_state.keywords:
                st.error("❌ 该关键词已存在！")
            else:
                st.error("❌ 关键词不能为空！")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 4.2.3 邮箱配置（表格）
    with tab3:
        st.markdown("<div class='config-page'>", unsafe_allow_html=True)
        st.subheader("邮箱配置")
        
        # 显示邮箱配置表格
        email_data = [
            {"配置项": "SMTP服务器", "值": st.session_state.email_config["smtp_server"], "说明": "如：smtp.exmail.qq.com"},
            {"配置项": "SMTP端口", "值": st.session_state.email_config["smtp_port"], "说明": "企业邮箱默认465"},
            {"配置项": "发件邮箱", "值": st.session_state.email_config["sender_email"], "说明": "你的企业邮箱地址"},
            {"配置项": "SMTP授权码", "值": "●●●●●●●●" if st.session_state.email_config["sender_password"] else "", "说明": "邮箱SMTP授权码（非登录密码）"},
            {"配置项": "收件邮箱", "值": st.session_state.email_config["receiver_email"], "说明": "接收报表的邮箱地址"}
        ]
        df_email = pd.DataFrame(email_data)
        st.dataframe(df_email, use_container_width=True)
        
        # 编辑邮箱配置
        st.subheader("修改邮箱配置")
        col1, col2 = st.columns(2)
        
        with col1:
            smtp_server = st.text_input("SMTP服务器", value=st.session_state.email_config["smtp_server"])
            smtp_port = st.number_input("SMTP端口", value=st.session_state.email_config["smtp_port"])
            sender_email = st.text_input("发件邮箱", value=st.session_state.email_config["sender_email"])
        
        with col2:
            sender_password = st.text_input("SMTP授权码", type="password", value=st.session_state.email_config["sender_password"])
            receiver_email = st.text_input("收件邮箱", value=st.session_state.email_config["receiver_email"])
        
        if st.button("💾 保存邮箱配置", key="save_email"):
            st.session_state.email_config = {
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "sender_email": sender_email,
                "sender_password": sender_password,
                "receiver_email": receiver_email
            }
            st.success("✅ 邮箱配置保存成功！")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 4.2.4 监控参数配置（表格）
    with tab4:
        st.markdown("<div class='config-page'>", unsafe_allow_html=True)
        st.subheader("监控参数配置")
        
        # 显示参数表格
        param_data = [
            {"配置项": "监控时长范围", "值": f"{st.session_state.time_range_days}天", "说明": "仅抓取近X天的内容"},
            {"配置项": "监控执行频率", "值": f"{st.session_state.monitor_interval//60}分钟", "说明": "每隔X分钟执行一次监控"}
        ]
        df_param = pd.DataFrame(param_data)
        st.dataframe(df_param, use_container_width=True)
        
        # 编辑监控参数
        st.subheader("修改监控参数")
        col1, col2 = st.columns(2)
        
        with col1:
            time_range = st.selectbox("监控时长范围", ["1天", "3天", "7天", "30天"], 
                                     index=["1天", "3天", "7天", "30天"].index(f"{st.session_state.time_range_days}天"))
            st.session_state.time_range_days = int(time_range.replace("天", ""))
        
        with col2:
            monitor_interval = st.slider("监控执行频率（分钟）", 1, 60, st.session_state.monitor_interval//60)
            st.session_state.monitor_interval = monitor_interval * 60
        
        if st.button("💾 保存监控参数", key="save_param"):
            st.success("✅ 监控参数保存成功！")
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

# ===================== 5. 程序入口 =====================
if __name__ == "__main__":
    # 根据当前页面状态渲染对应界面
    if st.session_state.page == "main":
        render_main_page()
    elif st.session_state.page == "config":
        render_config_page()
