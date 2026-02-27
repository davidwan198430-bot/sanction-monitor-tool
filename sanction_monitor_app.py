# -*- coding: utf-8 -*-
import streamlit as st
import uuid

# ------------------------------
# 页面基础配置（极简稳定）
# ------------------------------
st.set_page_config(
    page_title="制裁监控平台",
    layout="wide"
)

# ------------------------------
# 全局状态（稳定初始化）
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
# 侧边栏（原生导航）
# ------------------------------
with st.sidebar:
    st.title("制裁监控平台")
    if st.button("监控面板"):
        st.session_state.page = "监控"
    if st.button("配置中心"):
        st.session_state.page = "config"
    st.session_state.setdefault("page", "监控")

# ------------------------------
# 监控面板（原生组件）
# ------------------------------
if st.session_state.page == "监控":
    st.header("监控面板")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("监控域名数", len(st.session_state.domains))
    with col2:
        st.metric("监控关键词数", len(st.session_state.keywords))
    
    st.divider()
    
    status = "🟢 运行中" if st.session_state.monitor_running else "🔴 已停止"
    st.subheader(f"监控状态：{status}")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("启动监控", disabled=st.session_state.monitor_running):
            st.session_state.monitor_running = True
            st.rerun()
    with col_btn2:
        if st.button("停止监控", disabled=not st.session_state.monitor_running):
            st.session_state.monitor_running = False
            st.rerun()

# ------------------------------
# 配置中心（核心：按钮内嵌表格行内）
# ------------------------------
elif st.session_state.page == "config":
    st.header("配置中心")
    tab1, tab2 = st.tabs(["主域名配置", "关键词配置"])

    # 1. 主域名配置（按钮内嵌表格行）
    with tab1:
        st.subheader("主域名管理")
        
        # 新增域名
        new_name = st.text_input("域名名称", placeholder="如：中国商务部官网")
        new_url = st.text_input("域名URL", placeholder="https://...")
        if st.button("添加域名"):
            if new_name and new_url:
                st.session_state.domains.append({"id": str(uuid.uuid4()), "name": new_name, "url": new_url})
                st.rerun()
            else:
                st.warning("名称和URL不能为空")
        
        st.divider()
        
        # 表格表头
        header_col1, header_col2, header_col3, header_col4 = st.columns([0.8, 2, 4, 2])
        header_col1.write("**序号**")
        header_col2.write("**域名名称**")
        header_col3.write("**URL**")
        header_col4.write("**操作**")
        st.divider()  # 表头分隔线
        
        # 表格内容（每行包含按钮，内嵌最后一列）
        for idx, domain in enumerate(st.session_state.domains):
            # 每行的列布局（和表头对应）
            row_col1, row_col2, row_col3, row_col4 = st.columns([0.8, 2, 4, 2])
            
            # 第一列：序号
            row_col1.write(idx + 1)
            
            # 第二列：域名名称
            row_col2.write(domain["name"])
            
            # 第三列：URL
            row_col3.write(domain["url"])
            
            # 第四列：操作按钮（内嵌行内，对应本行）
            btn_col1, btn_col2 = row_col4.columns(2)
            with btn_col1:
                if st.button(f"修改", key=f"edit_domain_{domain['id']}"):
                    st.session_state.edit_domain = domain
            with btn_col2:
                if st.button(f"删除", key=f"del_domain_{domain['id']}"):
                    st.session_state.domains = [d for d in st.session_state.domains if d["id"] != domain["id"]]
                    st.rerun()
        
        # 修改域名弹窗
        if "edit_domain" in st.session_state:
            d = st.session_state.edit_domain
            with st.form(f"form_edit_domain_{d['id']}"):
                st.subheader(f"修改域名：{d['name']}")
                edit_name = st.text_input("新名称", value=d["name"])
                edit_url = st.text_input("新URL", value=d["url"])
                if st.form_submit_button("保存修改"):
                    d["name"] = edit_name
                    d["url"] = edit_url
                    del st.session_state.edit_domain
                    st.rerun()

    # 2. 关键词配置（按钮内嵌表格行）
    with tab2:
        st.subheader("关键词管理")
        
        # 新增关键词
        new_kw = st.text_input("新增关键词", placeholder="如：制裁、sanctions")
        if st.button("添加关键词"):
            if new_kw:
                st.session_state.keywords.append({"id": str(uuid.uuid4()), "word": new_kw})
                st.rerun()
            else:
                st.warning("关键词不能为空")
        
        st.divider()
        
        # 表格表头
        kw_header1, kw_header2, kw_header3 = st.columns([0.8, 5, 2])
        kw_header1.write("**序号**")
        kw_header2.write("**关键词**")
        kw_header3.write("**操作**")
        st.divider()  # 表头分隔线
        
        # 表格内容（每行包含按钮）
        for idx, kw in enumerate(st.session_state.keywords):
            # 每行的列布局
            row_col1, row_col2, row_col3 = st.columns([0.8, 5, 2])
            
            # 第一列：序号
            row_col1.write(idx + 1)
            
            # 第二列：关键词
            row_col2.write(kw["word"])
            
            # 第三列：操作按钮（内嵌行内）
            btn_col1, btn_col2 = row_col3.columns(2)
            with btn_col1:
                if st.button(f"修改", key=f"edit_kw_{kw['id']}"):
                    st.session_state.edit_kw = kw
            with btn_col2:
                if st.button(f"删除", key=f"del_kw_{kw['id']}"):
                    st.session_state.keywords = [k for k in st.session_state.keywords if k["id"] != kw["id"]]
                    st.rerun()
        
        # 修改关键词弹窗
        if "edit_kw" in st.session_state:
            k = st.session_state.edit_kw
            with st.form(f"form_edit_kw_{k['id']}"):
                st.subheader(f"修改关键词：{k['word']}")
                edit_kw = st.text_input("新关键词", value=k["word"])
                if st.form_submit_button("保存修改"):
                    k["word"] = edit_kw
                    del st.session_state.edit_kw
                    st.rerun()
