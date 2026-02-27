# -*- coding: utf-8 -*-
import streamlit as st
import uuid

# ------------------------------
# 页面基础配置（极简+稳定）
# ------------------------------
st.set_page_config(
    page_title="制裁监控平台",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------
# 核心样式（仅保留必要深色适配，无复杂CSS）
# ------------------------------
st.markdown("""
<style>
/* 全局深色 */
.stApp {background: #121212; color: #f0f0f0;}
section[data-testid="stSidebar"] {background: #222222; border-right: 1px solid #444;}
/* 按钮统一样式 */
.stButton > button {width: 70px; height: 30px; margin: 2px;}
.del-btn {background: #ff4444 !important; color: white !important;}
/* 表格样式 */
.dataframe {border: 1px solid #444; border-radius: 4px;}
.dataframe th {background: #333333; color: #4fd1c5;}
.dataframe td {border-bottom: 1px solid #444;}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# 全局状态（极简初始化，无冗余）
# ------------------------------
if "monitor_running" not in st.session_state:
    st.session_state.monitor_running = False
if "domains" not in st.session_state:
    st.session_state.domains = [
        {"id": str(uuid.uuid4()), "name": "中国商务部", "url": "https://www.mofcom.gov.cn/"},
        {"id": str(uuid.uuid4()), "name": "美国OFAC", "url": "https://home.treasury.gov/sanctions"},
        {"id": str(uuid.uuid4()), "name": "欧盟EEAS", "url": "https://eeas.europa.eu/sanctions"},
        {"id": str(uuid.uuid4()), "name": "出口管制网", "url": "https://www.ecrc.org.cn/"},
        {"id": str(uuid.uuid4()), "name": "联合国制裁", "url": "https://www.un.org/securitycouncil/sanctions"},
        {"id": str(uuid.uuid4()), "name": "美国BIS", "url": "https://www.bis.doc.gov/"},
        {"id": str(uuid.uuid4()), "name": "英国制裁", "url": "https://www.gov.uk/financial-sanctions"}
    ]
if "keywords" not in st.session_state:
    st.session_state.keywords = [
        {"id": str(uuid.uuid4()), "word": "制裁"},{"id": str(uuid.uuid4()), "word": "反制"},
        {"id": str(uuid.uuid4()), "word": "出口管制"},{"id": str(uuid.uuid4()), "word": "实体清单"},
        {"id": str(uuid.uuid4()), "word": "SDN List"},{"id": str(uuid.uuid4()), "word": "贸易限制"},
        {"id": str(uuid.uuid4()), "word": "禁运"},{"id": str(uuid.uuid4()), "word": "经济制裁"},
        {"id": str(uuid.uuid4()), "word": "OFAC"},{"id": str(uuid.uuid4()), "word": "UN sanctions"},
        {"id": str(uuid.uuid4()), "word": "embargo"},{"id": str(uuid.uuid4()), "word": "跨境制裁"},
        {"id": str(uuid.uuid4()), "word": "BIS清单"},{"id": str(uuid.uuid4()), "word": "实体清单更新"},
        {"id": str(uuid.uuid4()), "word": "sanctions"},{"id": str(uuid.uuid4()), "word": "export control"},
        {"id": str(uuid.uuid4()), "word": "单边制裁"},{"id": str(uuid.uuid4()), "word": "多边制裁"},
        {"id": str(uuid.uuid4()), "word": "限制性措施"},{"id": str(uuid.uuid4()), "word": "合规审查"}
    ]

# ------------------------------
# 侧边栏（原生，无冗余）
# ------------------------------
with st.sidebar:
    st.title("制裁监控平台")
    if st.button("📊 监控面板", use_container_width=True):
        st.session_state.page = "监控"
    if st.button("⚙️ 配置中心", use_container_width=True):
        st.session_state.page = "config"
    st.session_state.setdefault("page", "监控")

# ------------------------------
# 监控面板（原生，稳定）
# ------------------------------
if st.session_state.page == "监控":
    st.header("监控面板")
    col1, col2 = st.columns(2)
    with col1: st.metric("监控域名数", len(st.session_state.domains))
    with col2: st.metric("监控关键词数", len(st.session_state.keywords))
    
    st.divider()
    status = "🟢 运行中" if st.session_state.monitor_running else "🔴 已停止"
    st.subheader(f"监控状态：{status}")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("▶️ 启动监控", disabled=st.session_state.monitor_running):
            st.session_state.monitor_running = True
            st.rerun()
    with col_btn2:
        if st.button("⏹️ 停止监控", disabled=not st.session_state.monitor_running):
            st.session_state.monitor_running = False
            st.rerun()

# ------------------------------
# 配置中心（核心：原生表格+原生按钮，无任何冗余）
# ------------------------------
elif st.session_state.page == "config":
    st.header("配置中心")
    tab1, tab2 = st.tabs(["🌐 主域名配置", "🔑 关键词配置"])

    # 1. 主域名配置（原生表格+原生按钮，无冗余）
    with tab1:
        st.subheader("主域名管理")
        # 新增行（原生对齐）
        c1, c2, c3 = st.columns([2,3,1])
        new_name = c1.text_input("域名名称", placeholder="如：商务部官网")
        new_url = c2.text_input("域名URL", placeholder="https://...")
        if c3.button("➕ 添加") and new_name and new_url:
            st.session_state.domains.append({"id":str(uuid.uuid4()), "name":new_name, "url":new_url})
            st.rerun()

        # 原生表格（无HTML，无冗余）
        df_domain = st.dataframe(
            [[i+1, d["name"], d["url"]] for i,d in enumerate(st.session_state.domains)],
            column_labels=["序号", "名称", "URL"],
            use_container_width=True
        )

        # 操作按钮（与表格行一一对应，无冗余文字）
        st.subheader("操作区")
        for i, d in enumerate(st.session_state.domains):
            col1, col2, col3 = st.columns([1,1,1])
            with col1: st.write(f"域名：{d['name']}")
            with col2:
                if st.button(f"修改_{d['id']}"):
                    st.session_state.edit_domain = d
            with col3:
                if st.button(f"删除_{d['id']}", type="primary"):
                    st.session_state.domains = [x for x in st.session_state.domains if x["id"] != d["id"]]
                    st.rerun()

        # 修改逻辑（原生，无冗余）
        if "edit_domain" in st.session_state:
            d = st.session_state.edit_domain
            with st.form(f"form_edit_{d['id']}"):
                new_name = st.text_input("新名称", value=d["name"])
                new_url = st.text_input("新URL", value=d["url"])
                if st.form_submit_button("保存修改"):
                    d["name"] = new_name
                    d["url"] = new_url
                    del st.session_state.edit_domain
                    st.rerun()

    # 2. 关键词配置（和主域名逻辑一致，稳定无冗余）
    with tab2:
        st.subheader("关键词管理")
        c1, c2 = st.columns([4,1])
        new_kw = c1.text_input("新增关键词", placeholder="如：sanctions/实体清单")
        if c2.button("➕ 添加") and new_kw:
            st.session_state.keywords.append({"id":str(uuid.uuid4()), "word":new_kw})
            st.rerun()

        # 原生表格
        st.dataframe(
            [[i+1, k["word"]] for i,k in enumerate(st.session_state.keywords)],
            column_labels=["序号", "关键词"],
            use_container_width=True
        )

        # 操作按钮（一一对应，无冗余）
        st.subheader("操作区")
        for k in st.session_state.keywords:
            col1, col2 = st.columns([1,1])
            with col1: st.write(f"关键词：{k['word']}")
            with col2:
                if st.button(f"改_{k['id']}"):
                    st.session_state.edit_kw = k
                if st.button(f"删_{k['id']}", type="primary"):
                    st.session_state.keywords = [x for x in st.session_state.keywords if x["id"] != k["id"]]
                    st.rerun()

        # 关键词修改逻辑
        if "edit_kw" in st.session_state:
            kw = st.session_state.edit_kw
            with st.form(f"form_kw_{kw['id']}"):
                new_kw = st.text_input("新关键词", value=kw["word"])
                if st.form_submit_button("保存") and new_kw:
                    kw["word"] = new_kw
                    del st.session_state.edit_kw
                    st.rerun()
