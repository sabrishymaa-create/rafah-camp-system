import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse

# 1. إعدادات الصفحة (حل مشكلة القائمة الجانبية في الهواتف)
st.set_page_config(page_title="مخيم رفح السلام", layout="wide", initial_sidebar_state="collapsed")

# 2. تنسيق الواجهة (CSS) لدعم العربية والجمالية
st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #2E7D32; color: white; font-weight: bold; height: 3em; }
    .news-ticker { background: #b71c1c; color: white; padding: 12px; font-weight: bold; overflow: hidden; white-space: nowrap; border-radius: 8px; margin-bottom: 20px; border-right: 5px solid #ffeb3b; }
    .ticker-text { display: inline-block; padding-right: 100%; animation: ticker 25s linear infinite; font-size: 1.1rem; }
    @keyframes ticker { 0% { transform: translate(0, 0); } 100% { transform: translate(100%, 0); } }
    [data-testid="stSidebar"] { direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# 3. قاعدة البيانات (SQLite)
conn = sqlite3.connect('rafah_camp_system_2026.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS residents (id_num TEXT PRIMARY KEY, full_name TEXT, phone TEXT, health TEXT, social TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
conn.commit()

# إعداد الخبر الافتراضي
c.execute("INSERT OR IGNORE INTO settings VALUES ('news', 'مرحباً بكم في مخيم رفح السلام - بإدارة د. أكرم السدودي - يرجى تسجيل البيانات بدقة لضمان وصول الخدمات.')")
conn.commit()

# تهيئة حالة الجلسة (Session State)
if 'wives' not in st.session_state: st.session_state.wives = []
if 'kids' not in st.session_state: st.session_state.kids = []
if 'auth' not in st.session_state: st.session_state.auth = False

# --- شريط الأخبار المتحرك ---
c.execute("SELECT value FROM settings WHERE key='news'")
msg_news = c.fetchone()[0]
st.markdown(f'<div class="news-ticker"><div class="ticker-text">{msg_news}</div></div>', unsafe_allow_html=True)

# --- الهيدر الرئيسي ---
st.title("🏥 منظومة مخيم رفح السلام الرقمية")
st.markdown(f"#### إدارة الدكتور أكرم السدودي | حقوق الملكية: ابوسفيان")
st.write(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d')} | 🕒 الوقت: {datetime.now().strftime('%H:%M:%S')}")

# --- قائمة التنقل الرئيسية (لتجنب مشاكل القائمة الجانبية) ---
choice = st.selectbox("📌 اختر الإجراء المطلـوب:", ["📝 تسجيل بيانات نازح جديد", "🔐 لوحة تحكم الإدارة (Admin)"])

if choice == "📝 تسجيل بيانات نازح جديد":
    st.header("📋 استمارة التسجيل")
    with st.container():
        col1, col2 = st.columns(2)
        f_name = col1.text_input("الاسم الرباعي الكامل")
        id_num = col2.text_input("رقم الهوية")
        phone = col1.text_input("رقم الجوال")
        
        health_opts = ["سليم", "مزمن", "اعاقة حركية", "اعاقة سمعية", "اعاقة بصرية"]
        health = col2.selectbox("الحالة الصحية", health_opts)
        
        social_opts = ["متزوج/ة", "مطلق/ه", "ارمل/ه", "منفصل", "مهجور/ه", "اعزب"]
        social = col1.selectbox("الحالة الاجتماعية", social_opts)

        st.divider()
        # إضافة الزوجات (+)
        st.subheader("💍 بيانات الزوجات")
        if st.button("➕ أضف زوجة"): st.session_state.wives.append("")
        for i, _ in enumerate(st.session_state.wives):
            st.session_state.wives[i] = st.text_input(f"اسم وهوية الزوجة {i+1}", key=f"w_{i}")

        st.divider()
        # إضافة الأبناء (+)
        st.subheader("👶 بيانات الأبناء")
        if st.button("➕ أضف ابن/ابنة"): st.session_state.kids.append({"n": "", "i": "", "d": datetime.now()})
        for i, _ in enumerate(st.session_state.kids):
            k1, k2, k3 = st.columns(3)
            st.session_state.kids[i]['n'] = k1.text_input(f"اسم الابن {i+1}", key=f"kn_{i}")
            st.session_state.kids[i]['i'] = k2.text_input(f"هوية {i+1}", key=f"ki_{i}")
            st.session_state.kids[i]['d'] = k3.date_input(f"تاريخ ميلاد {i+1}", key=f"kd_{i}")

        if st.button("💾 حفظ كافة البيانات"):
            if f_name and id_num:
                c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?)", (id_num, f_name, phone, health, social, "نشط"))
                conn.commit()
                st.success(f"✅ تم حفظ بيانات {f_name} بنجاح!")
                st.session_state.wives, st.session_state.kids = [], [] # تفريغ القوائم
            else:
                st.error("⚠️ يرجى التأكد من كتابة الاسم ورقم الهوية.")

elif choice == "🔐 لوحة تحكم الإدارة (Admin)":
    if not st.session_state.auth:
        st.subheader("🔐 دخول المسؤول")
        user = st.text_input("اسم المستخدم")
        pw = st.text_input("كلمة المرور", type="password")
        if st.button("تسجيل الدخول"):
            if user == "admin" and pw == "admin123":
                st.session_state.auth = True
                st.rerun()
            else: st.error("❌ بيانات الدخول خاطئة")
    else:
        st.header("🛠 لوحة الإدارة - د. أكرم السدودي")
        if st.button("🔓 تسجيل الخروج"):
            st.session_state.auth = False
            st.rerun()

        # تعديل شريط الأخبار
        with st.expander("📢 تعديل الخبر المتحرك"):
            new_news = st.text_area("الخبر الحالي:", msg_news)
            if st.button("تحديث الخبر"):
                c.execute("UPDATE settings SET value=? WHERE key='news'", (new_news,))
                conn.commit()
                st.rerun()

        # عرض البيانات والفرز
        df = pd.read_sql("SELECT * FROM residents", conn)
        
        col_f1, col_f2 = st.columns(2)
        search = col_f1.text_input("🔍 بحث (اسم أو هوية)")
        f_health = col_f2.selectbox("فرز حسب الصحة:", ["الكل"] + health_opts)
        
        if search: df = df[df['full_name'].str.contains(search) | df['id_num'].str.contains(search)]
        if f_health != "الكل": df = df[df['health'] == f_health]
        
        st.dataframe(df, use_container_width=True)

        # الإجراءات والتصدير
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            target = st.selectbox("اختر شخصاً للحذف:", [""] + df['id_num'].tolist())
            if st.button("🗑 حذف السجل"):
                c.execute("DELETE FROM residents WHERE id_num=?", (target,))
                conn.commit()
                st.rerun()
        with col_b:
            towrite = io.BytesIO()
            df.to_excel(towrite, index=False)
            st.download_button("📥 تصدير Excel", towrite.getvalue(), "Camp_Data_2026.xlsx")
        with col_c:
            selected_name = st.selectbox("مراسلة واتساب:", [""] + df['full_name'].tolist())
            if selected_name:
                u_phone = df[df['full_name']==selected_name]['phone'].values[0]
                st.markdown(f"[💬 اضغط لمراسلة {selected_name}](wa.me{u_phone})")

st.markdown("---")
st.write("© 2026 | منظومة مخيم رفح السلام | حقوق الملكية محفوظة باسم **ابوسفيان**")
