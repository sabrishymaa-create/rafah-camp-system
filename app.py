import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse

# 1. إعدادات الصفحة والتنسيق (UI)
st.set_page_config(page_title="مخيم رفح السلام", layout="wide")

st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { border-radius: 10px; font-weight: bold; }
    /* شريط الأخبار */
    .news-ticker { background: #b71c1c; color: white; padding: 10px; font-weight: bold; overflow: hidden; white-space: nowrap; border-radius: 8px; margin-bottom: 20px; }
    .ticker-text { display: inline-block; padding-right: 100%; animation: ticker 30s linear infinite; }
    @keyframes ticker { 0% { transform: translate(0, 0); } 100% { transform: translate(100%, 0); } }
    /* حقوق الملكية بالأسفل */
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8f9fa; color: #333; text-align: center; padding: 10px; font-weight: bold; border-top: 2px solid #2E7D32; z-index: 1000; }
    /* تنسيق زر الدخول في أعلى اليسار */
    .login-trigger { float: left; }
    </style>
    """, unsafe_allow_html=True)

# 2. قاعدة البيانات
conn = sqlite3.connect('rafah_camp_system_2026.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS residents (id_num TEXT PRIMARY KEY, f1 TEXT, f2 TEXT, f3 TEXT, f4 TEXT, phone TEXT, health TEXT, social TEXT, wives TEXT, kids TEXT, status TEXT)''')
conn.commit()

# 3. إدارة حالة الجلسة
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'show_login' not in st.session_state: st.session_state.show_login = False

# --- شريط الأخبار المتحرك ---
st.markdown('<div class="news-ticker"><div class="ticker-text">مرحباً بكم في مخيم رفح السلام - إدارة د. أكرم السدودي - يرجى تسجيل البيانات بدقة لضمان جودة الخدمة.</div></div>', unsafe_allow_html=True)

# --- الهيدر العلوي ---
header_col1, header_col2 = st.columns([8, 2])
with header_col1:
    st.title("🏥 منظومة مخيم رفح السلام")
    st.markdown("#### إدارة الدكتور أكرم السدودي")
with header_col2:
    # زر تسجيل الدخول في أعلى اليسار
    if not st.session_state.logged_in:
        if st.button("🔐 تسجيل الدخول للإدارة"):
            st.session_state.show_login = not st.session_state.show_login
    else:
        if st.button("🚪 تسجيل الخروج"):
            st.session_state.logged_in = False
            st.session_state.show_login = False
            st.rerun()

# --- واجهة الدخول (تظهر فقط عند الضغط على الزر وتختفي عند النجاح) ---
if st.session_state.show_login and not st.session_state.logged_in:
    with st.container():
        st.markdown("---")
        l_col1, l_col2 = st.columns(2)
        u = l_col1.text_input("اسم المستخدم")
        p = l_col2.text_input("كلمة المرور", type="password")
        if st.button("دخول الآن"):
            if u == "admin" and p == "admin123":
                st.session_state.logged_in = True
                st.session_state.show_login = False
                st.rerun()
            else:
                st.error("خطأ في البيانات")
    st.markdown("---")

# --- محتوى الصفحة (يتغير حسب الحالة) ---
if st.session_state.logged_in:
    st.header("🛠 لوحة تحكم الإدارة المركزية")
    df = pd.read_sql("SELECT * FROM residents", conn)
    
    # خيارات الفرز والبحث
    st.subheader("🔍 البحث والفرز")
    f_col1, f_col2, f_col3 = st.columns(3)
    q = f_col1.text_input("بحث بالاسم أو الهوية")
    h_filter = f_col2.selectbox("فرز بالحالة الصحية", ["الكل", "سليم", "مزمن", "اعاقة حركية", "اعاقة سمعية", "اعاقة بصرية"])
    s_filter = f_col3.selectbox("فرز بالحالة الاجتماعية", ["الكل", "متزوج", "مطلق/ه", "ارمل/ه", "منفصل"])
    
    if q: df = df[df['id_num'].str.contains(q) | df['f1'].str.contains(q)]
    if h_filter != "الكل": df = df[df['health'] == h_filter]
    
    st.dataframe(df, use_container_width=True)
    
    # مراسلة وحذف
    st.subheader("📱 التواصل والتحكم")
    target = st.selectbox("اختر اسماً من الجدول:", [""] + df['f1'].tolist())
    if target:
        sel = df[df['f1'] == target].iloc[0]
        c1, c2, c3 = st.columns(3)
        msg = urllib.parse.quote(f"مرحباً {target}، يرجى مراجعة إدارة مخيم رفح السلام.")
        c1.markdown(f'<a href="wa.me{sel["phone"]}?text={msg}" target="_blank"><button style="width:100%; background:#25D366; color:white; border:none; padding:10px; border-radius:5px;">واتساب WhatsApp</button></a>', unsafe_allow_html=True)
        c2.markdown(f'<a href="sms:{sel["phone"]}?body={msg}"><button style="width:100%; background:#007AFF; color:white; border:none; padding:10px; border-radius:5px;">رسالة نصية SMS</button></a>', unsafe_allow_html=True)
        if c3.button("🗑 حذف السجل"):
            c.execute("DELETE FROM residents WHERE id_num=?", (sel['id_num'],))
            conn.commit(); st.rerun()
            
    # تصدير Excel
    towrite = io.BytesIO()
    df.to_excel(towrite, index=False)
    st.download_button("📥 تحميل كافة البيانات Excel", towrite.getvalue(), "Report_2026.xlsx")

else:
    # واجهة تسجيل النازحين
    st.header("📝 استمارة تسجيل نازح وعائلة جديدة")
    with st.form("reg_form"):
        col1, col2, col3, col4 = st.columns(4)
        fn1 = col1.text_input("الاسم الأول")
        fn2 = col2.text_input("الثاني")
        fn3 = col3.text_input("الثالث")
        fn4 = col4.text_input("الرابع")
        id_num = st.text_input("رقم الهوية")
        phone = st.text_input("رقم الجوال")
        
        health = st.selectbox("الحالة الصحية", ["سليم", "مزمن", "اعاقة حركية", "اعاقة سمعية", "اعاقة بصرية"])
        social = st.selectbox("الحالة الاجتماعية", ["متزوج", "مطلق/ه", "ارمل/ه", "منفصل", "مهجور/ه"])
        
        st.subheader("💍 بيانات الزوجات")
        wives = st.text_area("الاسم رباعي ورقم الهوية (استخدم زر + في نسخة الجوال لإضافة المزيد)")
        
        st.subheader("👶 بيانات الأبناء")
        kids = st.text_area("الاسم رباعي، الهوية، تاريخ الميلاد، الحالة الصحية، اليتم")
        
        if st.form_submit_button("💾 حفظ البيانات وإرسال الطلب"):
            if fn1 and id_num:
                c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                          (id_num, fn1, fn2, fn3, fn4, phone, health, social, wives, kids, "نشط"))
                conn.commit()
                st.success(f"✅ تم حفظ بيانات عائلة {fn1} بنجاح")
            else: st.error("⚠️ يجب إدخال الاسم الأول ورقم الهوية")

# حقوق الملكية بالأسفل
st.markdown('<div class="footer">حقوق الملكية محفوظة باسم: ابوسفيان © 2026</div>', unsafe_allow_html=True)
