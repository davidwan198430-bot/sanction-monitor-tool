# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import re
import uuid
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin

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
# 科技冷灰样式（表格不宽 + 按钮统一大小）
# ------------------------------
st.markdown("""
<style>
.stApp {
    background-color: #121212;
    color: #e0e0e0;
}
section[data-testid="stSidebar"] {
    background-color: #1a1a2d;
    border-right: 1px solid #33334f;
}
.glass {
    background: rgba(30,30,46,0.7);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 16px;
    border: 1px solid #33334f;
    max-width: 1000px; /* 限制卡片宽度，表格不再过宽 */
    margin-left: auto;
    margin-right: auto;
}
.title {
    font-size: 20px;
    font-weight: 600;
    color: #4fd1c5;
    margin-bottom: 12px;
}

/* 表格：表头 + 线条 + 不超宽 */
.table-header {
    font-weight: bold;
    color: #4fd1c5;
    border-bottom: 2px solid #5E6AD2;
    padding-bottom: 6px;
    font-size: 14px;
}
.table-row {
    border-bottom: 1px solid #33334f;
    padding: 6px 0;
    font-size: 14px;
}

/* 按钮统一大小（核心修复）*/
.stButton > button {
    width: 70px !important;       /* 统一宽度 */
    height: 34px !important;      /* 统一高度 */
    font-size: 13px !important;
    padding: 0 !important;
    background: linear-gradient(90deg, #5E6AD2, #4FD1C5);
    color: white;
    border: none;
    border-radius: 6px;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #4FD1C5, #5E6AD2);
}
button[key*="del"] {
    background: linear-gradient(90deg, #FF4D4F, #FF7875) !important;
}
/* 大按钮（启动/停止监控）*/
.big-btn > button {
    width: 140px !important;
    height: 42px !important;
    font-size: 15px !important;
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
    st.markdown("## 🚨 制裁监控平台")
    if st.button("📊 监控面板", use_container_width=True):
        st.session_state.active = "监控面板"
    if st.button("⚙️ 配置中心", use_container_width=True):
        st.session_state.active = "配置中心"

# ------------------------------
# 监控面板（恢复：开启/关闭监控按钮）
# ------------------------------
if st.session_state.active == "监控面板":
    st.markdown("# 监控面板")
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("监控域名", len(st.session_state.domains))
    with col2:
        st.metric("监控关键词", len(st.session_state.keywords))
    
    st.markdown("---")
    
    # 开启/关闭监控按钮（已恢复）
    status = "🟢 监控运行中" if st.session_state.monitor_running else "🔴 监控已停止"
    st.markdown(f"### 状态：{status}")
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("▶️ 启动监控", use_container_width=True, disabled=st.session_state.monitor_running, key="start"):
            st.session_state.monitor_running = True
            st.rerun()
    with btn_col2:
        if st.button("⏹️ 停止监控", use_container_width=True, disabled=not st.session_state.monitor_running, key="stop"):
            st.session_state.monitor_running = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------
# 配置中心（表格不宽 + 按钮统一 + 操作列在表格内）
# ------------------------------
elif st.session_state.active == "配置中心":
    st.markdown("# 配置中心")
    tab1, tab2 = st.tabs(["🌐 主域名配置", "🔑 关键词配置"])

    # ======================
    # 1. 主域名配置（表格收紧 + 按钮统一）
    # ======================
    with tab1:
        st.markdown('<div class="title">主域名管理</div>', unsafe_allow_html=True)
        st.markdown('<div class="glass">', unsafe_allow_html=True)

        # 新增：输入框 + 按钮对齐
        c1, c2, c3 = st.columns([2,3,1], vertical_alignment="bottom")
        with c1:
            n_name = st.text_input("名称", label_visibility="collapsed", placeholder="名称")
        with c2:
            n_url = st.text_input("URL", label_visibility="collapsed", placeholder="https://...")
        with c3:
            st.button("➕ 添加", key="add_domain")

        if st.session_state.get("add_domain"):
            if n_name and n_url:
                st.session_state.domains.append({"id": str(uuid.uuid4()), "name": n_name, "url": n_url})
                st.rerun()

        st.markdown("---")

        # 表格表头（窄版）
        h1, h2, h3, h4 = st.columns([0.8,2,4,1.5])
        with h1: st.markdown('<div class="table-header">序号</div>', unsafe_allow_html=True)
        with h2: st.markdown('<div class="table-header">名称</div>', unsafe_allow_html=True)
        with h3: st.markdown('<div class="table-header">URL</div>', unsafe_allow_html=True)
        with h4: st.markdown('<div class="table-header">操作</div>', unsafe_allow_html=True)

        # 表格行（收紧宽度）
        for i, item in enumerate(st.session_state.domains):
            st.markdown('<div class="table-row">', unsafe_allow_html=True)
            a1,a2,a3,a4 = st.columns([0.8,2,4,1.5])
            with a1: st.text(i+1)
            with a2: st.text(item["name"])
            with a3: st.text(item["url"])
            with a4:
                b1,b2 = st.columns(2)
                with b1: st.button("修改", key=f"ed_{item['id']}")
                with b2: st.button("删除", key=f"del_{item['id']}")
            st.markdown('</div>', unsafe_allow_html=True)

        # 修改逻辑
        for item in st.session_state.domains:
            if st.session_state.get(f"ed_{item['id']}"):
                with st.expander("修改", expanded=True):
                    t1 = st.text_input("名称", value=item["name"])
                    t2 = st.text_input("URL", value=item["url"])
                    if st.button("保存"):
                        item["name"] = t1
                        item["url"] = t2
                        st.rerun()
            if st.session_state.get(f"del_{item['id']}"):
                st.session_state.domains = [d for d in st.session_state.domains if d["id"] != item["id"]]
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ======================
    # 2. 关键词配置（20个 + 表格收紧 + 按钮统一）
    # ======================
    with tab2:
        st.markdown('<div class="title">关键词管理</div>', unsafe_allow_html=True)
        st.markdown('<div class="glass">', unsafe_allow_html=True)

        c1, c2 = st.columns([4,1], vertical_alignment="bottom")
        with c1:
            n_word = st.text_input("关键词", label_visibility="collapsed", placeholder="关键词")
        with c2:
            st.button("➕ 添加", key="add_kw")

        if st.session_state.get("add_kw") and n_word:
            if n_word not in [k["word"] for k in st.session_state.keywords]:
                st.session_state.keywords.append({"id": str(uuid.uuid4()), "word": n_word})
                st.rerun()

        st.markdown("---")

        # 关键词表头
        kh1, kh2, kh3 = st.columns([0.8,4,1.5])
        with kh1: st.markdown('<div class="table-header">序号</div>', unsafe_allow_html=True)
        with kh2: st.markdown('<div class="table-header">关键词</div>', unsafe_allow_html=True)
        with kh3: st.markdown('<div class="table-header">操作</div>', unsafe_allow_html=True)

        # 关键词行
        for i, item in enumerate(st.session_state.keywords):
            st.markdown('<div class="table-row">', unsafe_allow_html=True)
            k1,k2,k3 = st.columns([0.8,4,1.5])
            with k1: st.text(i+1)
            with k2: st.text(item["word"])
            with k3:
                b1,b2 = st.columns(2)
                with b1: st.button("修改", key=f"ekw_{item['id']}")
                with b2: st.button("删除", key=f"delkw_{item['id']}")
            st.markdown('</div>', unsafe_allow_html=True)

        # 修改关键词
        for item in st.session_state.keywords:
            if st.session_state.get(f"ekw_{item['id']}"):
                with st.expander("修改关键词", expanded=True):
                    new_w = st.text_input("内容", value=item["word"])
                    if st.button("保存关键词"):
                        item["word"] = new_w
                        st.rerun()
            if st.session_state.get(f"delkw_{item['id']}"):
                st.session_state.keywords = [k for k in st.session_state.keywords if k["id"] != item["id"]]
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
