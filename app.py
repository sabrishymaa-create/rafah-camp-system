import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="مخيم رفح السلام", layout="wide")

# تنسيق اللغة العربية والواجهة (CSS)
st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #007bff; color: white; font-weight: bold; }
    .news-ticker { background: #b71c1c; color: white; padding: 10px; font-weight: bold; overflow: hidden; white-space: nowrap; border-radius: 5px; }
    .ticker-text { display: inline-block; padding-right: 100%; animation: ticker 25s linear infinite; }
    @keyframes ticker { 0% { transform: translate(0, 0); } 100% { transform: translate(100%, 0); } }
    </style>
    """, unsafe_allow_html=True)

# 2. إنشاء وقاعدة البيانات والجداول
conn = sqlite3.connect('camp_final_v3.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS residents (id_num TEXT PRIMARY KEY, full_name TEXT, phone TEXT, health TEXT, social TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS family (parent_id TEXT, name TEXT, id_num TEXT, type TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
conn.commit()

# إعداد شريط الأخبار الافتراضي
c.execute("INSERT OR IGNORE INTO settings VALUES ('news', 'مرحباً بكم في مخيم رفح السلام - بإدارة د. أكرم السدودي - يرجى تسجيل البيانات بدقة')")
conn.commit()

# 3. تهيئة حالة الجلسة (Session State) لضمان عدم تعليق الأزرار
if 'wives' not in st.session_state: st.session_state.wives = []
if 'kids' not in st.session_state: st.session_state.kids = []
if 'auth' not in st.session_state: st.session_state.auth = False

# --- شريط الأخبار المتحرك ---
c.execute("SELECT value FROM settings WHERE key='news'")
msg = c.fetchone()[0]
st.markdown(f'<div class="news-ticker"><div class="ticker-text">{msg}</div></div>', unsafe_allow_html=True)

st.title("🏥 مخيم رفح السلام")
st.markdown("### إدارة الدكتور أكرم السدودي")

menu = ["📝 تسجيل البيانات", "🔐 لوحة الإدارة"]
choice = st.sidebar.selectbox("القائمة", menu)

if choice == "📝 تسجيل البيانات":
    st.header("📋 استمارة التسجيل")
    
    # نموذج البيانات الأساسية
    f_name = st.text_input("الاسم الرباعي الكامل")
    id_num = st.text_input("رقم الهوية")
    phone = st.text_input("رقم الجوال")
    health = st.selectbox("الحالة الصحية", ["سليم", "مزمن", "اعاقة حركية", "اعاقة سمعية", "اعاقة بصرية"])
    social = st.selectbox("الحالة الاجتماعية", ["متزوج/ة", "مطلق/ه", "ارمل/ه", "منفصل", "مهجور/ه", "اعزب"])

    st.divider()
    
    # إضافة الزوجات ديناميكياً
    st.subheader("💍 بيانات الزوجات")
    if st.button("➕ أضف زوجة جديدة"):
        st.session_state.wives.append("")
    
    for i, _ in enumerate(st.session_state.wives):
        st.session_state.wives[i] = st.text_input(f"اسم وهوية الزوجة {i+1}", key=f"w_{i}")

    # إضافة الأبناء ديناميكياً
    st.subheader("👶 بيانات الأبناء")
    if st.button("➕ أضف ابن/ابنة"):
        st.session_state.kids.append({"name": "", "id": ""})
    
    for i, _ in enumerate(st.session_state.kids):
        col_k1, col_k2 = st.columns(2)
        st.session_state.kids[i]['name'] = col_k1.text_input(f"اسم الابن {i+1}", key=f"kn_{i}")
        st.session_state.kids[i]['id'] = col_k2.text_input(f"هوية الابن {i+1}", key=f"ki_{i}")

    if st.button("💾 حفظ البيانات النهائية"):
        if f_name and id_num:
            c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?)", (id_num, f_name, phone, health, social))
            for w in st.session_state.wives:
                if w: c.execute("INSERT INTO family VALUES (?,?,?,'زوجة')", (id_num, w, ""))
            for k in st.session_state.kids:
                if k['name']: c.execute("INSERT INTO family VALUES (?,?,?,'ابن')", (id_num, k['name'], k['id']))
            conn.commit()
            st.success("✅ تم الحفظ بنجاح!")
            # تفريغ القوائم بعد الحفظ
            st.session_state.wives = []
            st.session_state.kids = []
        else:
            st.error("⚠️ يرجى إدخال الاسم والهوية")

elif choice == "🔐 لوحة الإدارة":
    if not st.session_state.auth:
        st.subheader("🔐 دخول المسؤول")
        user = st.text_input("اسم المستخدم")
        pw = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if user == "admin" and pw == "admin123":
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("بيانات خاطئة")
    else:
        st.header("🛠 لوحة الإدارة - د. أكرم السدودي")
        if st.button("🔓 خروج"):
            st.session_state.auth = False
            st.rerun()

        # تعديل الأخبار
        with st.expander("📢 تعديل شريط الأخبار"):
            new_msg = st.text_area("الخبر الحالي:", msg)
            if st.button("تحديث"):
                c.execute("UPDATE settings SET value=? WHERE key='news'", (new_msg,))
                conn.commit()
                st.rerun()

        # عرض البيانات والفرز
        df = pd.read_sql("SELECT * FROM residents", conn)
        search = st.text_input("🔍 بحث بالاسم أو الهوية")
        if search:
            df = df[df['full_name'].str.contains(search) | df['id_num'].str.contains(search)]
        
        st.dataframe(df, use_container_width=True)

        # التصدير والتواصل
        if not df.empty:
            towrite = io.BytesIO()
            df.to_excel(towrite, index=False)
            st.download_button("📥 تحميل ملف Excel", towrite.getvalue(), "Camp_2026.xlsx")
            
            st.divider()
            sel = st.selectbox("تواصل سريع مع:", df['full_name'].tolist())
            phone_num = df[df['full_name']==sel]['phone'].values[0]
            st.markdown(f"[💬 مراسلة واتساب](wa.me{phone_num})")

st.sidebar.markdown("---")
st.sidebar.write("© 2026 | حقوق الملكية: **ابوسفيان**")
