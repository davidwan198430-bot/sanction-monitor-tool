# -*- coding: utf-8 -*-
import streamlit as st
import uuid
from datetime import datetime

# ------------------------------
# 页面基础配置
# ------------------------------
st.set_page_config(
    page_title="制裁监控平台",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------
# 简洁深色表格样式（核心：合法隐藏触发按钮）
# ------------------------------
st.markdown("""
<style>
/* 全局深色适配 */
.stApp {
    background-color: #1E1E1E;
    color: #F0F0F0;
    font-family: Arial, sans-serif;
}

/* 侧边栏简洁样式 */
section[data-testid="stSidebar"] {
    background-color: #2D2D2D;
    border-right: 1px solid #444;
}

/* 标准表格核心样式（带完整边框、表头区分） */
.table-container {
    border: 1px solid #444;
    border-radius: 6px;
    overflow: hidden;
    margin: 10px 0 20px 0;
}
.table-header {
    display: grid;
    grid-template-columns: 0.8fr 2fr 4fr 1.5fr;
    background-color: #3A3A3A;
    font-weight: bold;
    padding: 10px;
    border-bottom: 1px solid #444;
}
.table-header-kw {
    grid-template-columns: 0.8fr 5fr 1.5fr !important;
}
.table-row {
    display: grid;
    grid-template-columns: 0.8fr 2fr 4fr 1.5fr;
    padding: 10px;
    border-bottom: 1px solid #444;
    align-items: center;
}
.table-row-kw {
    grid-template-columns: 0.8fr 5fr 1.5fr !important;
}
.table-row:hover {
    background-color: #2A2A2A;
}

/* 按钮统一大小（标准表格内按钮） */
.stButton > button {
    width: 65px !important;
    height: 32px !important;
    font-size: 12px !important;
    padding: 0 !important;
    border-radius: 4px !important;
    border: none !important;
}
/* 功能区分按钮颜色 */
.btn-edit {
    background-color: #0078D4 !important;
    color: white !important;
}
.btn-del {
    background-color: #E81123 !important;
    color: white !important;
}
.btn-add, .btn-big {
    width: auto !important;
    height: 36px !important;
    font-size: 14px !important;
}

/* 输入框简洁适配 */
.stTextInput input {
    background-color: #2D2D2D !important;
    color: #F0F0F0 !important;
    border: 1px solid #444 !important;
    border-radius: 4px !important;
}

/* 标签页简洁样式 */
.stTabs [data-baseweb="tab-list"] {
    background-color: #2D2D2D;
    border-bottom: 1px solid #444;
}
.stTabs [data-baseweb="tab"] {
    color: #CCCCCC !important;
}
.stTabs [aria-selected="true"] {
    color: #0078D4 !important;
    font-weight: bold;
}

/* 核心修复：合法隐藏触发按钮（替代非法的style参数） */
button[data-testid="baseButton-secondary"][key^="edit_"],
button[data-testid="baseButton-secondary"][key^="del_"],
button[data-testid="baseButton-secondary"][key^="edit_kw_"],
button[data-testid="baseButton-secondary"][key^="del_kw_"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# 全局状态（核心功能保留）
# ------------------------------
if "active_page" not in st.session_state:
    st.session_state.active_page = "监控面板"
if "monitor_running" not in st.session_state:
    st.session_state.monitor_running = False

# 8个核心主域名（保留）
if "domains" not in st.session_state:
    st.session_state.domains = [
        {"id": str(uuid.uuid4()), "name": "中国商务部", "url": "https://www.mofcom.gov.cn/"},
        {"id": str(uuid.uuid4()), "name": "美国OFAC", "url": "https://home.treasury.gov/sanctions"},
        {"id": str(uuid.uuid4()), "name": "欧盟EEAS", "url": "https://eeas.europa.eu/sanctions"},
        {"id": str(uuid.uuid4()), "name": "出口管制网", "url": "https://www.ecrc.org.cn/"},
        {"id": str(uuid.uuid4()), "name": "联合国制裁", "url": "https://www.un.org/securitycouncil/sanctions"},
        {"id": str(uuid.uuid4()), "name": "美国BIS", "url": "https://www.bis.doc.gov/"},
        {"id": str(uuid.uuid4()), "name": "英国制裁", "url": "https://www.gov.uk/government/collections/financial-sanctions"},
        {"id": str(uuid.uuid4()), "name": "日本制裁", "url": "https://www.mof.go.jp/english/sanctions/"}
    ]

# 20个核心关键词（保留）
if "keywords" not in st.session_state:
    st.session_state.keywords = [
        {"id": str(uuid.uuid4()), "word": "制裁"}, {"id": str(uuid.uuid4()), "word": "反制"},
        {"id": str(uuid.uuid4()), "word": "出口管制"}, {"id": str(uuid.uuid4()), "word": "实体清单"},
        {"id": str(uuid.uuid4()), "word": "SDN List"}, {"id": str(uuid.uuid4()), "word": "贸易限制"},
        {"id": str(uuid.uuid4()), "word": "禁运"}, {"id": str(uuid.uuid4()), "word": "经济制裁"},
        {"id": str(uuid.uuid4()), "word": "贸易制裁"}, {"id": str(uuid.uuid4()), "word": "单边制裁"},
        {"id": str(uuid.uuid4()), "word": "多边制裁"}, {"id": str(uuid.uuid4()), "word": "出口管制清单"},
        {"id": str(uuid.uuid4()), "word": "BIS清单"}, {"id": str(uuid.uuid4()), "word": "OFAC"},
        {"id": str(uuid.uuid4()), "word": "UN sanctions"}, {"id": str(uuid.uuid4()), "word": "embargo"},
        {"id": str(uuid.uuid4()), "word": "economic sanctions"}, {"id": str(uuid.uuid4()), "word": "实体清单更新"},
        {"id": str(uuid.uuid4()), "word": "限制性措施"}, {"id": str(uuid.uuid4()), "word": "跨境制裁"},
    ]

# ------------------------------
# 侧边栏（简洁导航）
# ------------------------------
with st.sidebar:
    st.title("制裁监控平台")
    st.divider()
    if st.button("📊 监控面板", use_container_width=True):
        st.session_state.active_page = "监控面板"
    if st.button("⚙️ 配置中心", use_container_width=True):
        st.session_state.active_page = "配置中心"

# ------------------------------
# 监控面板（标准布局，按钮正常）
# ------------------------------
if st.session_state.active_page == "监控面板":
    st.header("监控面板")
    st.divider()

    # 核心指标（简洁卡片）
    col1, col2 = st.columns(2)
    with col1:
        st.metric("监控主域名数量", len(st.session_state.domains))
    with col2:
        st.metric("监控关键词数量", len(st.session_state.keywords))

    st.divider()

    # 监控控制（标准按钮）
    status = "🟢 运行中" if st.session_state.monitor_running else "🔴 已停止"
    st.subheader(f"监控状态：{status}")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("▶️ 启动监控", key="start", disabled=st.session_state.monitor_running, type="primary"):
            st.session_state.monitor_running = True
            st.rerun()
    with col_btn2:
        if st.button("⏹️ 停止监控", key="stop", disabled=not st.session_state.monitor_running):
            st.session_state.monitor_running = False
            st.rerun()

# ------------------------------
# 配置中心（标准表格核心：带边框、表头、操作列）
# ------------------------------
elif st.session_state.active_page == "配置中心":
    st.header("配置中心")
    tab1, tab2 = st.tabs(["🌐 主域名配置", "🔑 关键词配置"])

    # ======================
    # 1. 主域名配置（标准表格）
    # ======================
    with tab1:
        st.subheader("主域名管理")
        st.caption("支持添加/修改/删除需监控的制裁相关官网")

        # 新增输入（对齐，无偏上）
        col1, col2, col3 = st.columns([2, 3, 1], vertical_alignment="bottom")
        with col1:
            new_name = st.text_input("域名名称", placeholder="如：美国OFAC官网")
        with col2:
            new_url = st.text_input("域名URL", placeholder="https://...")
        with col3:
            if st.button("➕ 添加", key="add_domain", type="primary"):
                if new_name and new_url:
                    st.session_state.domains.append({"id": str(uuid.uuid4()), "name": new_name, "url": new_url})
                    st.rerun()
                else:
                    st.warning("名称和URL不能为空！")

        # 标准表格（核心：带完整边框、固定表头、规整列）
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        # 表头
        st.markdown("""
        <div class="table-header">
            <div>序号</div>
            <div>域名名称</div>
            <div>URL</div>
            <div>操作</div>
        </div>
        """, unsafe_allow_html=True)
        # 表格内容
        for idx, domain in enumerate(st.session_state.domains):
            st.markdown(f"""
            <div class="table-row">
                <div>{idx+1}</div>
                <div>{domain['name']}</div>
                <div>{domain['url']}</div>
                <div style="display: flex; gap: 5px;">
                    <button onclick="document.getElementById('edit_{domain['id']}').click()" class="btn-edit">修改</button>
                    <button onclick="document.getElementById('del_{domain['id']}').click()" class="btn-del">删除</button>
                </div>
            </div>
            """, unsafe_allow_html=True)
            # 修复：移除非法的style参数，改用CSS隐藏（无报错）
            st.button("触发修改", key=f"edit_{domain['id']}")
            st.button("触发删除", key=f"del_{domain['id']}")
        st.markdown('</div>', unsafe_allow_html=True)

        # 修改逻辑（标准弹窗）
        for domain in st.session_state.domains:
            if st.session_state.get(f"edit_{domain['id']}"):
                with st.form(f"form_domain_{domain['id']}"):
                    st.subheader(f"修改域名：{domain['name']}")
                    edit_name = st.text_input("新名称", value=domain["name"])
                    edit_url = st.text_input("新URL", value=domain["url"])
                    if st.form_submit_button("保存修改"):
                        if edit_name and edit_url:
                            domain["name"] = edit_name
                            domain["url"] = edit_url
                            st.rerun()
                        else:
                            st.warning("名称和URL不能为空！")
            # 删除逻辑
            if st.session_state.get(f"del_{domain['id']}"):
                st.session_state.domains = [d for d in st.session_state.domains if d["id"] != domain["id"]]
                st.rerun()

    # ======================
    # 2. 关键词配置（标准表格）
    # ======================
    with tab2:
        st.subheader("关键词管理")
        st.caption("支持添加/修改/删除制裁相关监控关键词")

        # 新增输入（对齐）
        col1, col2 = st.columns([4, 1], vertical_alignment="bottom")
        with col1:
            new_word = st.text_input("新增关键词", placeholder="如：sanctions / 实体清单")
        with col2:
            if st.button("➕ 添加", key="add_kw", type="primary"):
                if new_word:
                    if new_word not in [k["word"] for k in st.session_state.keywords]:
                        st.session_state.keywords.append({"id": str(uuid.uuid4()), "word": new_word})
                        st.rerun()
                    else:
                        st.warning("关键词已存在！")
                else:
                    st.warning("关键词不能为空！")

        # 标准表格（关键词专用列宽）
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        # 表头
        st.markdown("""
        <div class="table-header table-header-kw">
            <div>序号</div>
            <div>关键词内容</div>
            <div>操作</div>
        </div>
        """, unsafe_allow_html=True)
        # 表格内容
        for idx, kw in enumerate(st.session_state.keywords):
            st.markdown(f"""
            <div class="table-row table-row-kw">
                <div>{idx+1}</div>
                <div>{kw['word']}</div>
                <div style="display: flex; gap: 5px;">
                    <button onclick="document.getElementById('edit_kw_{kw['id']}').click()" class="btn-edit">修改</button>
                    <button onclick="document.getElementById('del_kw_{kw['id']}').click()" class="btn-del">删除</button>
                </div>
            </div>
            """, unsafe_allow_html=True)
            # 修复：移除非法的style参数，改用CSS隐藏（无报错）
            st.button("触发修改kw", key=f"edit_kw_{kw['id']}")
            st.button("触发删除kw", key=f"del_kw_{kw['id']}")
        st.markdown('</div>', unsafe_allow_html=True)

        # 修改逻辑
        for kw in st.session_state.keywords:
            if st.session_state.get(f"edit_kw_{kw['id']}"):
                with st.form(f"form_kw_{kw['id']}"):
                    st.subheader(f"修改关键词：{kw['word']}")
                    edit_word = st.text_input("新关键词", value=kw["word"])
                    if st.form_submit_button("保存修改"):
                        if edit_word:
                            if edit_word not in [k["word"] for k in st.session_state.keywords if k["id"] != kw["id"]]:
                                kw["word"] = edit_word
                                st.rerun()
                            else:
                                st.warning("关键词已存在！")
                        else:
                            st.warning("关键词不能为空！")
            # 删除逻辑
            if st.session_state.get(f"del_kw_{kw['id']}"):
                st.session_state.keywords = [k for k in st.session_state.keywords if k["id"] != kw["id"]]
                st.rerun()
