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

# ===================== 页面配置 =====================
st.set_page_config(
    page_title="制裁监控工具",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义UI样式
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #FF4B4B; text-align: center; margin-bottom: 2rem;}
    .status-card {background-color: #262730; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 5px solid #FF4B4B;}
    .config-card {background-color: #262730; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;}
    .stButton>button {width: 100%; border-radius: 8px; height: 3rem; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ===================== 初始化（全部默认数据已内置） =====================
if "monitor_running" not in st.session_state:
    st.session_state.monitor_running = False
if "monitor_interval" not in st.session_state:
    st.session_state.monitor_interval = 900
if "time_range_days" not in st.session_state:
    st.session_state.time_range_days = 30
if "sent_content_hash" not in st.session_state:
    st.session_state.sent_content_hash = set()

# --------------- 默认全部域名 ---------------
if "monitor_urls" not in st.session_state:
    st.session_state.monitor_urls = {
        "【主】商务部条约法律司": "https://trb.mofcom.gov.cn/",
        "【子】商务部条约法律司-政策解读": "https://trb.mofcom.gov.cn/article/zcyj/",
        "【主】商务部进出口管制局": "https://ec.mofcom.gov.cn/",
        "【子】商务部进出口管制局-公告": "https://ec.mofcom.gov.cn/article/gonggao/",
        "【主】中国出口管制信息网": "https://www.ecrc.org.cn/",
        "【子】中国出口管制信息网-政策法规": "https://www.ecrc.org.cn/zcfg/",
        "【主】外交部国际经济司": "https://www.mfa.gov.cn/web/guojijingsiji_674821/",
        "【主】海关总署进出口管制": "https://www.customs.gov.cn/col/col3022/index.html",
        "【主】外交部发言人谈话": "https://www.mfa.gov.cn/web/fyrth/",
        "【主】美国OFAC": "https://ofac.treasury.gov/",
        "【子】美国OFAC-制裁名单": "https://ofac.treasury.gov/sanctions-programs-and-country-information",
        "【主】美国BIS": "https://www.bis.doc.gov/",
        "【子】美国BIS-实体清单": "https://www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern/entity-list",
        "【子】美国BIS-航空国防管制": "https://www.bis.doc.gov/index.php/policy-guidance/aviation-and-defense",
        "【主】欧盟EEAS制裁": "https://eeas.europa.eu/topics/sanctions_en",
        "【主】英国OFSI": "https://www.gov.uk/government/organisations/office-of-financial-sanctions-implementation",
        "【主】联合国安理会制裁": "https://www.un.org/securitycouncil/committees/index.html",
        "【主】澳大利亚DFAT制裁": "https://www.dfat.gov.au/international-relations/sanctions",
        "【主】加拿大Global Affairs制裁": "https://internationale.gc.ca/world-monde/international_relations-relations_internationales/sanctions/index.aspx",
        "【主】欧盟航空安全局制裁": "https://www.easa.europa.eu/topics/safety-and-environment/sanctions"
    }

# --------------- 默认全部关键词（现在会显示！）---------------
if "keywords" not in st.session_state:
    st.session_state.keywords = [
        # 中文
        "制裁","反制","出口管制","实体清单","未核实清单","军事最终用户",
        "制裁清单","出口许可","技术出口限制","制裁措施","贸易限制","经济制裁",
        "定向制裁","制裁名单","禁运","限制性措施","长臂管辖","出口禁令",
        "最终用户核查","两用物项","无人机管制","航空制造管制","导航系统管制",
        "飞行控制管制","遥感技术管制",
        # 英文
        "sanctions","countermeasures","export control","entity list",
        "unverified list","military end user","sanctions list","export license",
        "technology export restrictions","sanctions measures","trade restrictions",
        "economic sanctions","targeted sanctions","embargo","restrictive measures",
        "extraterritorial jurisdiction","export ban","end-user verification",
        "dual-use items","UAV","aviation manufacturing"
    ]

# ===================== 核心功能函数 =====================
def extract_publish_time(text, url):
    time_patterns = [r'(\d{4})[-/年](\d{2})[-/月](\d{2})', r'(\d{4})-(\d{2})-(\d{2})\s+\d{2}:\d{2}']
    for p in time_patterns:
        m = re.search(p, text)
        if m:
            try: return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except: pass
    return datetime.now()

def is_within_time_range(publish_time):
    return publish_time >= datetime.now() - timedelta(days=st.session_state.time_range_days)

def send_email_with_excel(excel_path):
    if not excel_path or not all([SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL]):
        st.warning("邮箱配置不完整或无数据，不发邮件")
        return
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = f"制裁监控报表 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        msg.attach(MIMEText(f"监控域名：{len(st.session_state.monitor_urls)}个\n关键词：{len(st.session_state.keywords)}个\n时段：近{st.session_state.time_range_days}天", "plain", "utf-8"))
        
        with open(excel_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(excel_path)}")
            msg.attach(part)
        
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as s:
            s.login(SENDER_EMAIL, SENDER_PASSWORD)
            s.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        st.success("✅ 邮件发送成功")
    except Exception as e:
        st.error(f"❌ 发邮件失败：{str(e)}")

def crawl_and_filter(log_box):
    res = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for name, url in st.session_state.monitor_urls.items():
        log_box.info(f"抓取：{name}")
        try:
            r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15, verify=False)
            r.encoding = r.apparent_encoding
            txt = re.sub(r"<[^>]+>", "", r.text).strip()
            h = hash(txt[:1000])
            if h in st.session_state.sent_content_hash:
                log_box.info("已去重，跳过")
                continue
            t = extract_publish_time(txt, url)
            if not is_within_time_range(t):
                log_box.info("超出时间范围，跳过")
                continue
            hits = [kw for kw in st.session_state.keywords if kw.lower() in txt.lower()]
            if not hits:
                log_box.info("未命中关键词，跳过")
                continue
            res.append({
                "网站":name,"网址":url,"关键词":",".join(hits),
                "发布时间":t.strftime("%Y-%m-%d"),"监控时间":now_str,"摘要":txt[:500]
            })
            st.session_state.sent_content_hash.add(h)
            log_box.success(f"✅ 命中：{','.join(hits[:3])}...")
            time.sleep(1)
        except Exception as e:
            log_box.error(f"失败：{str(e)}")
    return res

def make_excel(data):
    if not data: return None
    fn = f"制裁监控_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    pd.DataFrame(data).to_excel(fn, index=False, engine="openpyxl")
    return fn

def monitor_task():
    while st.session_state.monitor_running:
        st.subheader(f"📅 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        log_area = st.empty()
        data = crawl_and_filter(log_area)
        f = make_excel(data)
        send_email_with_excel(f)
        for i in range(st.session_state.monitor_interval, 0, -1):
            if not st.session_state.monitor_running: break
            st.info(f"下一次执行：{i} 秒")
            time.sleep(1)

# ===================== 界面 =====================
st.markdown("<h1 class='main-header'>🚨 制裁监控工具</h1>", unsafe_allow_html=True)

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置区")
    with st.expander("📧 邮箱", expanded=True):
        SMTP_SERVER = st.text_input("SMTP", value="smtp.exmail.qq.com")
        SMTP_PORT = st.number_input("端口", value=465)
        SENDER_EMAIL = st.text_input("发件邮箱")
        SENDER_PASSWORD = st.text_input("授权码", type="password")
        RECEIVER_EMAIL = st.text_input("收件邮箱")

    with st.expander("⏱️ 监控参数", expanded=True):
        period = st.selectbox("监控时段", ["1天","3天","7天","30天"])
        st.session_state.time_range_days = {"1天":1,"3天":3,"7天":7,"30天":30}[period]
        mins = st.slider("执行间隔(分钟)",1,60,15)
        st.session_state.monitor_interval = mins*60

    with st.expander("🌐 域名管理", expanded=True):
        st.markdown("#### 新增域名")
        n_name = st.text_input("名称（如【主】XXX）")
        n_url = st.text_input("URL")
        if st.button("➕ 添加域名"):
            if n_name and n_url:
                st.session_state.monitor_urls[n_name] = n_url
                st.success("添加成功")
        st.markdown("#### 删除域名")
        del_d = st.selectbox("选择删除", list(st.session_state.monitor_urls.keys()))
        if st.button("🗑️ 删除域名"):
            del st.session_state.monitor_urls[del_d]
            st.success("删除成功")

    # ===================== 关键词：现在能看见了！=====================
    with st.expander("🔑 关键词管理", expanded=True):
        st.markdown("### 📋 当前关键词列表")
        st.write(", ".join(st.session_state.keywords))
        
        st.markdown("---")
        st.markdown("#### 新增关键词")
        new_kw = st.text_input("关键词")
        if st.button("➕ 添加关键词"):
            if new_kw and new_kw not in st.session_state.keywords:
                st.session_state.keywords.append(new_kw)
                st.success(f"已添加：{new_kw}")
        st.markdown("#### 删除关键词")
        del_kw = st.selectbox("选择要删除的关键词", st.session_state.keywords)
        if st.button("🗑️ 删除关键词"):
            st.session_state.keywords.remove(del_kw)
            st.success(f"已删除：{del_kw}")

# 主界面：状态 + 控制
c1, c2 = st.columns(2)
with c1:
    st.markdown("<div class='status-card'>", unsafe_allow_html=True)
    st.subheader("监控状态")
    if st.session_state.monitor_running:
        st.markdown("<h2 style='color:green'>🟢 运行中</h2>", unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='color:red'>🔴 已停止</h2>", unsafe_allow_html=True)
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("▶️ 开启监控", type="primary", disabled=st.session_state.monitor_running):
            st.session_state.monitor_running = True
            st.rerun()
    with bc2:
        if st.button("⏹️ 停止监控", disabled=not st.session_state.monitor_running):
            st.session_state.monitor_running = False
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='config-card'>", unsafe_allow_html=True)
    st.subheader("配置摘要")
    st.write(f"时段：{period}")
    st.write(f"间隔：{mins} 分钟")
    st.write(f"域名：{len(st.session_state.monitor_urls)} 个")
    st.write(f"关键词：{len(st.session_state.keywords)} 个")
    st.markdown("</div>", unsafe_allow_html=True)

# 报表下载
st.markdown("---")
st.subheader("📁 报表下载")
xls = [x for x in os.listdir(".") if x.endswith(".xlsx") and "制裁监控" in x]
if xls:
    sel = st.selectbox("选择报表", xls)
    with open(sel, "rb") as f:
        st.download_button("📥 下载", f, sel)
else:
    st.info("暂无报表")

# 运行监控
if st.session_state.monitor_running:
    monitor_task()
