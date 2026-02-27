# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

# ------------------------------
# 页面配置
# ------------------------------
st.set_page_config(
    page_title="制裁监控平台",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------
# 科技冷灰UI样式（核心重构）
# ------------------------------
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

/* 侧边栏 - 科技深色 */
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

/* 按钮 - 科技蓝（统一大小+渐变） */
.stButton > button {
    width: 70px !important;
    height: 34px !important;
    font-size: 13px !important;
    padding: 0 !important;
    background: linear-gradient(90deg, #5E6AD2, #4FD1C5);
    color: white;
    border: none;
    border-radius: 8px;
    box-shadow: 0 3px 10px rgba(94,106,210,0.3);
}
.stButton > button:hover {
    background: linear-gradient(90deg, #4FD1C5, #5E6AD2);
    box-shadow: 0 3px 15px rgba(94,106,210,0.5);
}
/* 删除按钮样式 */
button[key*="del"] {
    background: linear-gradient(90deg, #FF4D4F, #FF7875) !important;
}
/* 大按钮（启动/停止监控） */
.big-btn > button {
    width: 140px !important;
    height: 42px !important;
    font-size: 15px !important;
}

/* 表格样式（科技感） */
.table-header {
    font-weight: bold;
    color: #4FD1C5;
    border-bottom: 2px solid #5E6AD2;
    padding-bottom: 8px;
    margin-bottom: 8px;
}
.table-row {
    border-bottom: 1px solid #33334F;
    padding: 8px 0;
}
.table-cell {
    padding: 8px 0;
}

/* 输入框 - 深色科技 */
.stTextInput input {
    background-color: #2A2A3A !important;
    color: white !important;
    border: 1px solid #5E6AD2 !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# 全局状态
# ------------------------------
if "active" not in st.session_state:
    st.session_state.active = "监控面板"

if "monitor_running" not in st.session_state:
    st.session_state.monitor_running = False

# 主域名 8个
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

# 关键词 20个
if "keywords" not in st.session_state:
    st.session_state.keywords = [
        {"id": str(uuid.uuid4()), "word": "制裁"},
        {"id": str(uuid.uuid4()), "word": "反制"},
        {"id": str(uuid.uuid4()), "word": "出口管制"},
        {"id": str(uuid.uuid4()), "word": "实体清单"},
        {"id": str(uuid.uuid4()), "word": "SDN List"},
        {"id": str(uuid.uuid4()), "word": "贸易限制"},
        {"id": str(uuid.uuid4()), "word": "禁运"},
        {"id": str(uuid.uuid4()), "word": "经济制裁"},
        {"id": str(uuid.uuid4()), "word": "贸易制裁"},
        {"id": str(uuid.uuid4()), "word": "单边制裁"},
        {"id": str(uuid.uuid4()), "word": "多边制裁"},
        {"id": str(uuid.uuid4()), "word": "出口管制清单"},
        {"id": str(uuid.uuid4()), "word": "BIS清单"},
        {"id": str(uuid.uuid4()), "word": "OFAC"},
        {"id": str(uuid.uuid4()), "word": "UN sanctions"},
        {"id": str(uuid.uuid4()), "word": "embargo"},
        {"id": str(uuid.uuid4()), "word": "economic sanctions"},
        {"id": str(uuid.uuid4()), "word": "实体清单更新"},
        {"id": str(uuid.uuid4()), "word": "限制性措施"},
        {"id": str(uuid.uuid4()), "word": "跨境制裁"},
    ]

# ------------------------------
# 侧边栏
# ------------------------------
with st.sidebar:
    st.markdown("<h1 style='color:#4FD1C5; text-align:center; margin:20px 0;'>🚨 制裁监控平台</h1>", unsafe_allow_html=True)
    st.markdown("---")
    nav_buttons = ["监控面板", "配置中心"]
    for btn in nav_buttons:
        if st.button(btn, use_container_width=True, key=f"nav_{btn}"):
            st.session_state.active = btn

# ------------------------------
# 监控面板（科技感重构）
# ------------------------------
if st.session_state.active == "监控面板":
    st.markdown("<div class='module-title'>🏠 监控面板</div>", unsafe_allow_html=True)
    
    # 3列对称指标卡片
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class='metric-box'>
            <div class='metric-label'>监控主域名数</div>
            <div class='metric-value'>{}</div>
            <div class='metric-label'>个</div>
        </div>
        """.format(len(st.session_state.domains)), unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='metric-box'>
            <div class='metric-label'>监控关键词数</div>
            <div class='metric-value'>{}</div>
            <div class='metric-label'>个</div>
        </div>
        """.format(len(st.session_state.keywords)), unsafe_allow_html=True)
    
    # 监控控制
    st.markdown("<div class='glass-card'><div class='card-title'>🎮 监控控制</div>", unsafe_allow_html=True)
    status_text = "🟢 监控运行中" if st.session_state.monitor_running else "🔴 监控已停止"
    st.markdown(f"<div style='font-size:16px; color:#4FD1C5; margin-bottom:15px;'>状态：{status_text}</div>", unsafe_allow_html=True)
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("▶️ 启动监控", key="start_monitor", disabled=st.session_state.monitor_running, use_container_width=True):
            st.session_state.monitor_running = True
            st.rerun()
    with btn_col2:
        if st.button("⏹️ 停止监控", key="stop_monitor", disabled=not st.session_state.monitor_running, use_container_width=True):
            st.session_state.monitor_running = False
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------
# 配置中心（科技感重构）
# ------------------------------
elif st.session_state.active == "配置中心":
    st.markdown("<div class='module-title'>⚙️ 配置中心</div>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🌐 主域名配置", "🔑 关键词配置"])

    # ======================
    # 1. 主域名配置
    # ======================
    with tab1:
        st.markdown("<div class='glass-card'><div class='card-title'>主域名管理</div>", unsafe_allow_html=True)

        # 新增域名
        c1, c2, c3 = st.columns([2,3,1], vertical_alignment="bottom")
        with c1:
            n_name = st.text_input("域名名称", label_visibility="collapsed", placeholder="如：美国OFAC官网")
        with c2:
            n_url = st.text_input("域名URL", label_visibility="collapsed", placeholder="https://...")
        with c3:
            if st.button("➕ 添加", key="add_domain"):
                if n_name and n_url:
                    st.session_state.domains.append({
                        "id": str(uuid.uuid4()),
                        "name": n_name,
                        "url": n_url
                    })
                    st.rerun()

        st.markdown("---")

        # 表格表头
        h1, h2, h3, h4 = st.columns([0.8,2,4,1.5])
        with h1: st.markdown('<div class="table-header">序号</div>', unsafe_allow_html=True)
        with h2: st.markdown('<div class="table-header">名称</div>', unsafe_allow_html=True)
        with h3: st.markdown('<div class="table-header">URL</div>', unsafe_allow_html=True)
        with h4: st.markdown('<div class="table-header">操作</div>', unsafe_allow_html=True)

        # 表格内容
        for i, item in enumerate(st.session_state.domains):
            st.markdown('<div class="table-row">', unsafe_allow_html=True)
            a1,a2,a3,a4 = st.columns([0.8,2,4,1.5])
            with a1: st.text(i+1)
            with a2: st.text(item["name"])
            with a3: st.text(item["url"])
            with a4:
                b1,b2 = st.columns(2)
                with b1:
                    if st.button("修改", key=f"ed_{item['id']}"):
                        st.session_state["edit_domain_id"] = item["id"]
                with b2:
                    if st.button("删除", key=f"del_{item['id']}"):
                        st.session_state.domains = [d for d in st.session_state.domains if d["id"] != item["id"]]
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # 修改弹窗
        if "edit_domain_id" in st.session_state:
            domain = next((d for d in st.session_state.domains if d["id"] == st.session_state.edit_domain_id), None)
            if domain:
                with st.expander(f"修改域名：{domain['name']}", expanded=True):
                    new_name = st.text_input("新名称", value=domain["name"])
                    new_url = st.text_input("新URL", value=domain["url"])
                    if st.button("保存修改", key="save_domain"):
                        domain["name"] = new_name
                        domain["url"] = new_url
                        del st.session_state.edit_domain_id
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ======================
    # 2. 关键词配置
    # ======================
    with tab2:
        st.markdown("<div class='glass-card'><div class='card-title'>关键词管理</div>", unsafe_allow_html=True)

        # 新增关键词
        c1, c2 = st.columns([4,1], vertical_alignment="bottom")
        with c1:
            n_word = st.text_input("新增关键词", label_visibility="collapsed", placeholder="如：合规审查 / trade sanctions")
        with c2:
            if st.button("➕ 添加", key="add_kw"):
                if n_word and n_word not in [k["word"] for k in st.session_state.keywords]:
                    st.session_state.keywords.append({
                        "id": str(uuid.uuid4()),
                        "word": n_word
                    })
                    st.rerun()
                elif n_word in [k["word"] for k in st.session_state.keywords]:
                    st.warning("⚠️ 关键词已存在！")

        st.markdown("---")

        # 关键词表格表头
        kh1, kh2, kh3 = st.columns([0.8,4,1.5])
        with kh1: st.markdown('<div class="table-header">序号</div>', unsafe_allow_html=True)
        with kh2: st.markdown('<div class="table-header">关键词</div>', unsafe_allow_html=True)
        with kh3: st.markdown('<div class="table-header">操作</div>', unsafe_allow_html=True)

        # 关键词表格内容
        for i, item in enumerate(st.session_state.keywords):
            st.markdown('<div class="table-row">', unsafe_allow_html=True)
            k1,k2,k3 = st.columns([0.8,4,1.5])
            with k1: st.text(i+1)
            with k2: st.text(item["word"])
            with k3:
                b1,b2 = st.columns(2)
                with b1:
                    if st.button("修改", key=f"ekw_{item['id']}"):
                        st.session_state["edit_kw_id"] = item["id"]
                with b2:
                    if st.button("删除", key=f"delkw_{item['id']}"):
                        st.session_state.keywords = [k for k in st.session_state.keywords if k["id"] != item["id"]]
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # 修改关键词弹窗
        if "edit_kw_id" in st.session_state:
            kw = next((k for k in st.session_state.keywords if k["id"] == st.session_state.edit_kw_id), None)
            if kw:
                with st.expander(f"修改关键词：{kw['word']}", expanded=True):
                    new_word = st.text_input("新关键词内容", value=kw["word"])
                    if st.button("保存修改", key="save_kw"):
                        if new_word and new_word not in [k["word"] for k in st.session_state.keywords if k["id"] != kw["id"]]:
                            kw["word"] = new_word
                            del st.session_state.edit_kw_id
                            st.rerun()
                        elif new_word in [k["word"] for k in st.session_state.keywords if k["id"] != kw["id"]]:
                            st.warning("⚠️ 关键词已存在！")

        st.markdown("</div>", unsafe_allow_html=True)
