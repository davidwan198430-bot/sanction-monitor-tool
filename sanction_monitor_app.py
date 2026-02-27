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

# ===================== 全局配置与初始化 =====================
# 设置页面配置，优化UI
st.set_page_config(
    page_title="制裁监控工具",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS，让界面更像桌面工具
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .status-card {
        background-color: #262730;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 5px solid #FF4B4B;
    }
    .config-card {
        background-color: #262730;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: bold;
    }
    .stDownloadButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #4CAF50;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if "monitor_running" not in st.session_state:
    st.session_state.monitor_running = False
if "monitor_interval" not in st.session_state:
    st.session_state.monitor_interval = 900  # 默认15分钟
if "time_range_days" not in st.session_state:
    st.session_state.time_range_days = 30
if "sent_content_hash" not in st.session_state:
    st.session_state.sent_content_hash = set()

# 1. 内置全量默认主域名+子域名
if "monitor_urls" not in st.session_state:
    st.session_state.monitor_urls = {
        # 国内主域名+核心子域名
        "【主】商务部条约法律司": "https://trb.mofcom.gov.cn/",
        "【子】商务部条约法律司-政策解读": "https://trb.mofcom.gov.cn/article/zcyj/",
        "【主】商务部进出口管制局": "https://ec.mofcom.gov.cn/",
        "【子】商务部进出口管制局-公告": "https://ec.mofcom.gov.cn/article/gonggao/",
        "【主】中国出口管制信息网": "https://www.ecrc.org.cn/",
        "【子】中国出口管制信息网-政策法规": "https://www.ecrc.org.cn/zcfg/",
        "【主】外交部国际经济司": "https://www.mfa.gov.cn/web/guojijingsiji_674821/",
        "【主】海关总署进出口管制": "https://www.customs.gov.cn/col/col3022/index.html",
        "【主】外交部发言人谈话": "https://www.mfa.gov.cn/web/fyrth/",
        # 国外主域名+核心子域名
        "【主】美国OFAC": "https://ofac.treasury.gov/",
        "【子】美国OFAC-制裁名单": "https://ofac.treasury.gov/sanctions-programs-and-country-information",
        "【主】美国BIS": "https://www.bis.doc.gov/",
        "【子】美国BIS-实体清单": "https://www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern/entity-list",
        "【子】美国BIS-航空国防管制": "https://www.bis.doc.gov/index.php/policy-guidance/aviation-and-defense",
        "【主】欧盟EEAS制裁": "https://eeas.europa.eu/topics/sanctions_en",
        "【主】英国OFSI": "https://www.gov.uk/government/organisations/office-of-financial-sanctions-implementation",
        "【主】联合国安理会制裁": "https://www.un.org/securitycouncil/committees/index.html",
        "【主】澳大利亚DFAT制裁": "https://www.dfat.gov.au/international-relations/sanctions",
        "【主】加拿大Global Affairs制裁": "https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/index.aspx",
        "【主】欧盟航空安全局制裁": "https://www.easa.europa.eu/topics/safety-and-environment/sanctions"
    }

# 2. 内置全量默认中英文关键词
if "keywords" not in st.session_state:
    st.session_state.keywords = [
        # 中文全量关键词
        "制裁", "反制", "出口管制", "实体清单", "未核实清单", "军事最终用户",
        "制裁清单", "出口许可", "技术出口限制", "制裁措施", "贸易限制", "经济制裁",
        "定向制裁", "制裁名单", "禁运", "限制性措施", "长臂管辖", "出口禁令",
        "最终用户核查", "两用物项", "无人机管制", "航空制造管制", "导航系统管制",
        "飞行控制管制", "遥感技术管制",
        # 英文全量关键词
        "sanctions", "countermeasures", "export control", "entity list",
        "unverified list", "military end user", "sanctions list", "export license",
        "technology export restrictions", "sanctions measures", "trade restrictions",
        "economic sanctions", "targeted sanctions", "embargo", "restrictive measures",
        "extraterritorial jurisdiction", "export ban", "end-user verification",
        "dual-use items", "UAV", "aviation manufacturing"
    ]

# ===================== 核心功能函数 =====================
def extract_publish_time(text, url):
    """提取网页内容的发布时间"""
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

def is_within_time_range(publish_time):
    """判断内容是否在监控时长内"""
    cutoff_time = datetime.now() - timedelta(days=st.session_state.time_range_days)
    return publish_time >= cutoff_time

def send_email_with_excel(excel_path):
    """发送带Excel附件的邮件"""
    if not excel_path or not SENDER_EMAIL or not RECEIVER_EMAIL or not SENDER_PASSWORD:
        st.warning("⚠️ 邮箱配置不完整或无Excel，跳过发邮件")
        return

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"【制裁监控报表】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    body = f"""
本次监控覆盖 {len(st.session_state.monitor_urls)} 个域名（含子域名），
筛选出近{st.session_state.time_range_days}天内命中关键词的内容，详见附件。
监控频率：{monitor_interval_min}分钟
    """
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
        st.success("✅ 邮件发送成功！")
    except Exception as e:
        st.error(f"❌ 邮件发送失败：{str(e)}")

def crawl_and_filter(log_container):
    """抓取网页并筛选内容"""
    result_data = []
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for site_name, url in st.session_state.monitor_urls.items():
        log_container.info(f"🔍 正在抓取：{site_name} - {url}")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
            }
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            response.encoding = response.apparent_encoding
            pure_text = re.sub(r'<[^>]+>', '', response.text).strip()
            content_hash = hash(pure_text[:1000])

            # 去重判断
            if content_hash in st.session_state.sent_content_hash:
                log_container.info(f"⏭️ {site_name}：内容已发送过，跳过")
                continue

            # 时间筛选
            publish_time = extract_publish_time(pure_text, url)
            if not is_within_time_range(publish_time):
                log_container.info(f"⏳ {site_name}：内容发布时间超出{st.session_state.time_range_days}天，跳过")
                continue

            # 关键词筛选
            hit_keywords = [kw for kw in st.session_state.keywords if kw.lower() in pure_text.lower()]
            if not hit_keywords:
                log_container.info(f"🔍 {site_name}：未命中关键词，跳过")
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
            log_container.success(f"✅ {site_name}：命中关键词[{','.join(hit_keywords)}]")
            time.sleep(1)

        except Exception as e:
            log_container.error(f"❌ {site_name}：抓取失败 - {str(e)}")
            continue

    return result_data

def generate_excel(data):
    """生成Excel报表"""
    if not data:
        st.info("ℹ️ 未抓取到符合条件的内容，不生成Excel")
        return None

    df = pd.DataFrame(data)
    excel_filename = f"制裁监控报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(excel_filename, index=False, engine='openpyxl')
    st.success(f"📊 Excel生成成功：{excel_filename}")
    return excel_filename

def monitor_loop():
    """监控主循环"""
    while st.session_state.monitor_running:
        st.subheader(f"📊 监控执行中 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
        log_container = st.empty()
        
        # 1. 抓取筛选数据
        monitor_data = crawl_and_filter(log_container)
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

# ===================== 主界面布局 =====================
# 顶部标题
st.markdown("<h1 class='main-header'>🚨 制裁监控工具</h1>", unsafe_allow_html=True)

# 左侧边栏：配置区
with st.sidebar:
    st.header("⚙️ 系统配置")
    
    with st.expander("📧 邮箱设置", expanded=True):
        SMTP_SERVER = st.text_input("SMTP服务器", value="smtp.exmail.qq.com")
        SMTP_PORT = st.number_input("SMTP端口", value=465)
        SENDER_EMAIL = st.text_input("发件邮箱")
        SENDER_PASSWORD = st.text_input("SMTP授权码", type="password")
        RECEIVER_EMAIL = st.text_input("收件邮箱")

    with st.expander("🔍 监控参数", expanded=True):
        time_range_options = {"1天": 1, "3天": 3, "7天": 7, "30天": 30}
        selected_time_range = st.selectbox("监控内容时长", options=list(time_range_options.keys()))
        st.session_state.time_range_days = time_range_options[selected_time_range]

        monitor_interval_min = st.slider("监控频率（分钟）", 1, 60, 15)
        st.session_state.monitor_interval = monitor_interval_min * 60

    with st.expander("🌐 域名管理", expanded=True):
        st.subheader("新增域名")
        new_domain_name = st.text_input("域名名称（如：【主】新网站）")
        new_domain_url = st.text_input("域名URL")
        if st.button("➕ 添加域名"):
            if new_domain_name and new_domain_url:
                st.session_state.monitor_urls[new_domain_name] = new_domain_url
                st.success(f"✅ 添加成功：{new_domain_name}")
            else:
                st.error("❌ 名称和URL不能为空")

        st.subheader("删除域名")
        domain_to_delete = st.selectbox("选择要删除的域名", options=list(st.session_state.monitor_urls.keys()))
        if st.button("🗑️ 删除域名"):
            del st.session_state.monitor_urls[domain_to_delete]
            st.success(f"✅ 删除成功：{domain_to_delete}")

    with st.expander("🔑 关键词管理", expanded=True):
        st.subheader("新增关键词")
        new_keyword = st.text_input("关键词")
        if st.button("➕ 添加关键词"):
            if new_keyword:
                st.session_state.keywords.append(new_keyword)
                st.success(f"✅ 添加关键词：{new_keyword}")
            else:
                st.error("❌ 关键词不能为空")

# 右侧主区域：控制与状态区
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("<div class='status-card'>", unsafe_allow_html=True)
    st.subheader("当前监控状态")
    if st.session_state.monitor_running:
        st.markdown("<h2 style='color: #4CAF50;'>🟢 运行中</h2>", unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='color: #FF4B4B;'>🔴 已停止</h2>", unsafe_allow_html=True)
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("▶️ 开启监控", disabled=st.session_state.monitor_running, type="primary"):
            st.session_state.monitor_running = True
            st.rerun()
    with btn_col2:
        if st.button("⏹️ 停止监控", disabled=not st.session_state.monitor_running, type="secondary"):
            st.session_state.monitor_running = False
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='config-card'>", unsafe_allow_html=True)
    st.subheader("📋 当前配置摘要")
    st.write(f"**监控时长**: {st.session_state.time_range_days}天")
    st.write(f"**监控频率**: {monitor_interval_min}分钟")
    st.write(f"**监控域名**: {len(st.session_state.monitor_urls)}个")
    st.write(f"**监控关键词**: {len(st.session_state.keywords)}个")
    st.markdown("</div>", unsafe_allow_html=True)

# 监控日志与报表下载区
st.markdown("---")
st.subheader("📁 报表与日志")

# 报表下载
excel_files = [f for f in os.listdir(".") if f.endswith(".xlsx") and "制裁监控报表" in f]
if excel_files:
    selected_excel = st.selectbox("选择报表文件", excel_files)
    with open(selected_excel, "rb") as f:
        st.download_button("📥 下载Excel报表", f, file_name=selected_excel)
else:
    st.info("ℹ️ 暂无报表文件")

# 如果监控正在运行，启动监控循环
if st.session_state.monitor_running:
    monitor_loop()
