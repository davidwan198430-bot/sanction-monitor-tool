# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import re
import os
import uuid
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
# 科技冷灰样式
# ------------------------------
st.markdown("""
<style>
.stApp {
    background-color: #121212;
    color: #e0e0e0;
}
section[data-testid="stSidebar"] {
    background-color: #1a1a2d;
}
.glass {
    background: rgba(30,30,46,0.7);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 16px;
    border: 1px solid #33334f;
}
.title {
    font-size: 20px;
    font-weight: 600;
    color: #4fd1c5;
    margin-bottom: 12px;
}
/* 按钮样式优化（科技感） */
.stButton > button {
    background: linear-gradient(90deg, #5E6AD2, #4FD1C5);
    color: white;
    border: none;
    border-radius: 6px;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #4FD1C5, #5E6AD2);
}
/* 删除按钮特殊样式 */
.stButton > button[data-testid*="del"] {
    background: linear-gradient(90deg, #FF4D4F, #FF7875);
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# 全局状态（核心：扩充关键词至20个）
# ------------------------------
if "active" not in st.session_state:
    st.session_state.active = "监控面板"

if "domains" not in st.session_state:
    st.session_state.domains = [
        {"id": str(uuid.uuid4()), "name": "商务部官网", "url": "https://www.mofcom.gov.cn/"},
        {"id": str(uuid.uuid4()), "name": "美国财政部官网", "url": "https://www.treasury.gov/"},
        {"id": str(uuid.uuid4()), "name": "欧盟EEAS官网", "url": "https://eeas.europa.eu/"},
        {"id": str(uuid.uuid4()), "name": "中国出口管制信息网", "url": "https://www.ecrc.org.cn/"},
        {"id": str(uuid.uuid4()), "name": "美国商务部BIS官网", "url": "https://www.bis.doc.gov/"},
    ]

# 扩充至20个关键词（覆盖中英文/多场景）
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
# 监控面板
# ------------------------------
if st.session_state.active == "监控面板":
    st.markdown("# 监控面板")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.metric("监控主域名数", len(st.session_state.domains))
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.metric("监控关键词数", len(st.session_state.keywords))
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------
# 配置中心（表格内操作列 · 无报错版）
# ------------------------------
elif st.session_state.active == "配置中心":
    st.markdown("# 配置中心")

    tab1, tab2 = st.tabs(["🌐 主域名配置", "🔑 关键词配置"])

    # ======================
    # 1. 主域名配置（表格 + 操作列）
    # ======================
    with tab1:
        st.markdown('<div class="title">主域名管理</div>', unsafe_allow_html=True)
        st.markdown('<div class="glass">', unsafe_allow_html=True)

        # 新增：输入框 + 按钮 对齐
        c1, c2, c3 = st.columns([3,3,1], vertical_alignment="bottom")
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

        # 表格 + 操作列（原生，无错）
        for i, item in enumerate(st.session_state.domains):
            col_a, col_b, col_c, col_d = st.columns([1,3,5,2])
            with col_a:
                st.text(f"{i+1}")
            with col_b:
                st.text(item["name"])
            with col_c:
                st.text(item["url"])
            with col_d:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("修改", key=f"ed_{item['id']}"):
                        st.session_state["edit_domain_id"] = item["id"]
                with btn_col2:
                    if st.button("删除", key=f"del_{item['id']}"):
                        st.session_state.domains = [d for d in st.session_state.domains if d["id"] != item["id"]]
                        st.rerun()

        # 修改弹窗（极简）
        if "edit_domain_id" in st.session_state:
            domain = next((d for d in st.session_state.domains if d["id"] == st.session_state.edit_domain_id), None)
            if domain:
                with st.expander("修改域名", expanded=True):
                    new_name = st.text_input("新名称", value=domain["name"])
                    new_url = st.text_input("新URL", value=domain["url"])
                    if st.button("保存域名修改", key="save_domain"):
                        domain["name"] = new_name
                        domain["url"] = new_url
                        del st.session_state.edit_domain_id
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ======================
    # 2. 关键词配置（表格 + 操作列 + 20个默认关键词）
    # ======================
    with tab2:
        st.markdown('<div class="title">关键词管理</div>', unsafe_allow_html=True)
        st.markdown('<div class="glass">', unsafe_allow_html=True)

        # 新增：输入框 + 按钮 对齐
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

        # 表格 + 操作列（原生，无错）
        for i, item in enumerate(st.session_state.keywords):
            col_a, col_b, col_c = st.columns([1,6,2])
            with col_a:
                st.text(f"{i+1}")
            with col_b:
                st.text(item["word"])
            with col_c:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("修改", key=f"ekw_{item['id']}"):
                        st.session_state["edit_kw_id"] = item["id"]
                with btn_col2:
                    if st.button("删除", key=f"delkw_{item['id']}"):
                        st.session_state.keywords = [k for k in st.session_state.keywords if k["id"] != item["id"]]
                        st.rerun()

        # 修改关键词弹窗
        if "edit_kw_id" in st.session_state:
            kw = next((k for k in st.session_state.keywords if k["id"] == st.session_state.edit_kw_id), None)
            if kw:
                with st.expander("修改关键词", expanded=True):
                    new_word = st.text_input("新关键词内容", value=kw["word"])
                    if st.button("保存关键词修改", key="save_kw"):
                        if new_word and new_word not in [k["word"] for k in st.session_state.keywords if k["id"] != kw["id"]]:
                            kw["word"] = new_word
                            del st.session_state.edit_kw_id
                            st.rerun()
                        elif new_word in [k["word"] for k in st.session_state.keywords if k["id"] != kw["id"]]:
                            st.warning("⚠️ 关键词已存在！")

        st.markdown('</div>', unsafe_allow_html=True)
