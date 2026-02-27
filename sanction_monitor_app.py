# -*- coding: utf-8 -*-
import streamlit as st
import uuid
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ------------------------------
# 页面基础配置（极简稳定）
# ------------------------------
st.set_page_config(
    page_title="制裁监控平台",
    layout="wide"
)

# ------------------------------
# 全局状态
# ------------------------------
# 监控状态
if "monitor_running" not in st.session_state:
    st.session_state.monitor_running = False

# 主域名
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

# 关键词
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

# 邮箱配置
if "email_config" not in st.session_state:
    st.session_state.email_config = {
        "smtp_server": "",    # SMTP服务器（如smtp.qq.com、smtp.163.com）
        "smtp_port": 465,     # SMTP端口（QQ/163邮箱默认465）
        "sender_email": "",   # 发件人邮箱
        "sender_auth_code": "",# 发件人邮箱授权码（非登录密码）
        "receiver_email": ""  # 收件人邮箱（多个用逗号分隔）
    }

# ------------------------------
# 邮箱工具函数
# ------------------------------
def send_test_email():
    """测试邮箱配置是否可用，发送测试邮件"""
    try:
        # 提取配置
        config = st.session_state.email_config
        if not all([config["smtp_server"], config["sender_email"], config["sender_auth_code"], config["receiver_email"]]):
            return False, "请先填写完整的邮箱配置！"
        
        # 构建测试邮件
        msg = MIMEText("这是制裁监控平台的测试邮件，配置成功！", 'plain', 'utf-8')
        msg['From'] = Header(config["sender_email"], 'utf-8')
        msg['To'] = Header(config["receiver_email"], 'utf-8')
        msg['Subject'] = Header("制裁监控平台 - 邮箱配置测试", 'utf-8')
        
        # 连接SMTP服务器并发送
        with smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"]) as server:
            server.login(config["sender_email"], config["sender_auth_code"])
            server.sendmail(config["sender_email"], config["receiver_email"].split(","), msg.as_string())
        
        return True, "测试邮件发送成功！请查接收件邮箱。"
    except Exception as e:
        return False, f"发送失败：{str(e)}"

# ------------------------------
# 侧边栏（仅保留监控面板、配置中心）
# ------------------------------
with st.sidebar:
    st.title("制裁监控平台")
    st.divider()
    # 页面导航按钮（移除单独的邮箱配置按钮）
    if st.button("📊 监控面板", use_container_width=True):
        st.session_state.page = "监控"
    if st.button("⚙️ 配置中心", use_container_width=True):
        st.session_state.page = "config"
    # 默认页面
    st.session_state.setdefault("page", "监控")

# ------------------------------
# 1. 监控面板
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
# 2. 配置中心（新增邮箱配置标签页，三标签同级）
# ------------------------------
elif st.session_state.page == "config":
    st.header("配置中心")
    # 调整为三个标签页：主域名、关键词、邮箱配置（同级）
    tab1, tab2, tab3 = st.tabs(["🌐 主域名配置", "🔑 关键词配置", "📧 邮箱配置"])

    # 2.1 主域名配置
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
        st.divider()
        
        # 表格内容
        for idx, domain in enumerate(st.session_state.domains):
            row_col1, row_col2, row_col3, row_col4 = st.columns([0.8, 2, 4, 2])
            row_col1.write(idx + 1)
            row_col2.write(domain["name"])
            row_col3.write(domain["url"])
            
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

    # 2.2 关键词配置
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
        st.divider()
        
        # 表格内容
        for idx, kw in enumerate(st.session_state.keywords):
            row_col1, row_col2, row_col3 = st.columns([0.8, 5, 2])
            row_col1.write(idx + 1)
            row_col2.write(kw["word"])
            
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

    # 2.3 邮箱配置（归到配置中心第三个标签页，和前两个同级）
    with tab3:
        st.subheader("邮件告警配置（监控触发时自动发送邮件）")
        st.divider()
        
        # 加载已保存的配置
        config = st.session_state.email_config
        
        # 配置表单（分组布局，清晰易填）
        with st.form("email_config_form"):
            col1, col2 = st.columns(2)
            
            # 左侧：SMTP服务器配置
            with col1:
                st.write("### 发件人邮箱配置")
                smtp_server = st.text_input(
                    "SMTP服务器", 
                    value=config["smtp_server"],
                    placeholder="如：smtp.qq.com / smtp.163.com"
                )
                smtp_port = st.number_input(
                    "SMTP端口", 
                    value=config["smtp_port"],
                    min_value=1, max_value=65535, step=1
                )
                sender_email = st.text_input(
                    "发件人邮箱", 
                    value=config["sender_email"],
                    placeholder="如：your_email@qq.com"
                )
                sender_auth_code = st.text_input(
                    "邮箱授权码", 
                    value=config["sender_auth_code"],
                    type="password",
                    placeholder="注意：不是登录密码，需在邮箱设置中开启SMTP并获取"
                )
            
            # 右侧：收件人配置
            with col2:
                st.write("### 收件人配置")
                receiver_email = st.text_input(
                    "收件人邮箱", 
                    value=config["receiver_email"],
                    placeholder="多个邮箱用英文逗号分隔，如：a@163.com,b@qq.com"
                )
                st.write("### 配置说明")
                st.info("""
                1. QQ邮箱：SMTP服务器=smtp.qq.com，端口=465，需开启POP3/SMTP并获取授权码
                2. 163邮箱：SMTP服务器=smtp.163.com，端口=465，需开启SMTP并获取授权码
                3. 企业邮箱：请联系邮箱管理员获取SMTP信息
                """)
            
            # 表单按钮
            st.divider()
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                save_btn = st.form_submit_button("💾 保存配置", type="primary")
            with col_btn2:
                test_btn = st.form_submit_button("📤 测试发送邮件")
        
        # 保存配置逻辑
        if save_btn:
            st.session_state.email_config = {
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "sender_email": sender_email,
                "sender_auth_code": sender_auth_code,
                "receiver_email": receiver_email
            }
            st.success("邮箱配置保存成功！")
        
        # 测试邮件发送逻辑
        if test_btn:
            with st.spinner("正在发送测试邮件..."):
                success, msg = send_test_email()
            if success:
                st.success(msg)
            else:
                st.error(msg)
        
        # 显示当前配置（方便核对）
        st.divider()
        st.write("### 当前已保存的配置")
        st.write(f"- SMTP服务器：{config['smtp_server'] or '未配置'}")
        st.write(f"- SMTP端口：{config['smtp_port']}")
        st.write(f"- 发件人邮箱：{config['sender_email'] or '未配置'}")
        st.write(f"- 收件人邮箱：{config['receiver_email'] or '未配置'}")
