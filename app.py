import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse

# 1. إعدادات الصفحة والتصميم المتطور
st.set_page_config(page_title="مخيم رفح السلام", layout="wide", initial_sidebar_state="expanded")

# تصميم واجهة احترافية (UI)
st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 12px; background-image: linear-gradient(to right, #1e88e5, #1565c0); color: white; font-weight: bold; border: none; padding: 10px; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    .news-ticker { background: linear-gradient(90deg, #b71c1c, #d32f2f); color: white; padding: 12px; font-weight: bold; overflow: hidden; white-space: nowrap; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 25px; border-right: 5px solid #ffeb3b; }
    .ticker-text { display: inline-block; padding-right: 100%; animation: ticker 30s linear infinite; font-size: 1.1rem; }
    @keyframes ticker { 0% { transform: translate(0, 0); } 100% { transform: translate(100%, 0); } }
    .main-card { background-color: #f8f9fa; padding: 20px; border-radius: 15px; border: 1px solid #dee2e6; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. ربط قاعدة البيانات
conn = sqlite3.connect('camp_system_2026.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS residents (id_num TEXT PRIMARY KEY, full_name TEXT, phone TEXT, health TEXT, social TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
conn.commit()

c.execute("INSERT OR IGNORE INTO settings VALUES ('news', 'أهلاً بكم في منظومة مخيم رفح السلام الرقمية - تحت إشراف د. أكرم السدودي - نسعى لخدمتكم وتسهيل بياناتكم.')")
conn.commit()

# حالة الجلسة
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'wives_count' not in st.session_state: st.session_state.wives_count = 0
if 'kids_count' not in st.session_state: st.session_state.kids_count = 0

# --- عرض شريط الأخبار الاحترافي ---
c.execute("SELECT value FROM settings WHERE key='news'")
current_news = c.fetchone()[0]
st.markdown(f'<div class="news-ticker"><div class="ticker-text">{current_news}</div></div>', unsafe_allow_html=True)

# --- الهيدر العلوي ---
col_logo, col_title = st.columns([1, 4])
with col_title:
    st.title("🏥 مخيم رفح السلام")
    st.markdown("#### إدارة الدكتور أكرم السدودي | نظام إدارة البيانات 2026")
with col_logo:
    st.write(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
    st.write(f" حقوق الملكية: **ابوسفيان**")

# --- القائمة الجانبية للتنقل ---
st.sidebar.image("cdn-icons-png.flaticon.com", width=100)
st.sidebar.title("القائمة الرئيسية")
choice = st.sidebar.radio("انتقل إلى:", ["🏠 الصفحة الرئيسية", "📝 تسجيل البيانات", "🔐 لوحة الإدارة"])

if choice == "🏠 الصفحة الرئيسية":
    st.markdown("""
    <div class='main-card'>
    <h3>مرحباً بكم في مخيم رفح السلام</h3>
    <p>هذا النظام مخصص لتنظيم بيانات النازحين وتسهيل وصول المساعدات والخدمات الصحية تحت إشراف مباشر من الدكتور أكرم السدودي.</p>
    <ul>
        <li>يرجى تسجيل البيانات بدقة.</li>
        <li>تأكد من إضافة جميع أفراد العائلة (الزوجات والأبناء).</li>
        <li>يتم الاحتفاظ بالبيانات بسرية تامة.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

elif choice == "📝 تسجيل البيانات":
    st.header("📝 استمارة تسجيل نازح جديد")
    with st.form("main_form", clear_on_submit=False):
        st.subheader("👤 البيانات الشخصية")
        c1, c2 = st.columns(2)
        f_name = c1.text_input("الاسم الرباعي الكامل")
        id_num = c2.text_input("رقم الهوية")
        phone = c1.text_input("رقم الجوال (مثال: 059XXXXXXX)")
        health = c2.selectbox("الحالة الصحية", ["سليم", "مزمن", "اعاقة حركية", "اعاقة سمعية", "اعاقة بصرية"])
        social = c1.selectbox("الحالة الاجتماعية", ["متزوج/ة", "مطلق/ه", "ارمل/ه", "منفصل", "مهجور/ه", "اعزب"])

        # استخدام Tabs لتنظيم العائلة
        tab_wives, tab_kids = st.tabs(["💍 الزوجات", "👶 الأبناء"])
        
        with tab_wives:
            st.button("➕ إضافة زوجة", on_click=lambda: st.session_state.update(wives_count=st.session_state.wives_count+1))
            for i in range(st.session_state.wives_count):
                st.text_input(f"اسم الزوجة {i+1} وهويتها", key=f"w_{i}")

        with tab_kids:
            st.button("➕ إضافة ابن/ابنة", on_click=lambda: st.session_state.update(kids_count=st.session_state.kids_count+1))
            for j in range(st.session_state.kids_count):
                kc1, kc2, kc3 = st.columns(3)
                kc1.text_input(f"اسم الابن {j+1}", key=f"kn_{j}")
                kc2.text_input(f"هوية {j+1}", key=f"ki_{j}")
                kc3.date_input(f"تاريخ الميلاد {j+1}", key=f"kd_{j}")

        if st.form_submit_button("💾 إرسال وحفظ البيانات"):
            if f_name and id_num:
                c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?)", (id_num, f_name, phone, health, social, "نشط"))
                conn.commit()
                st.success(f"✅ تم تسجيل بيانات {f_name} بنجاح!")
            else:
                st.error("⚠️ يرجى إكمال الحقول الأساسية (الاسم والهوية)")

elif choice == "🔐 لوحة الإدارة":
    if not st.session_state.authenticated:
        st.subheader("🔐 تسجيل دخول الإدارة")
        with st.container():
            user_in = st.text_input("اسم المستخدم")
            pass_in = st.text_input("كلمة المرور", type="password")
            if st.button("تسجيل الدخول"):
                if user_in == "admin" and pass_in == "admin123":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ البيانات غير صحيحة")
    else:
        st.header("🛠 لوحة الإدارة المركزية")
        if st.button("🔓 تسجيل الخروج"):
            st.session_state.authenticated = False
            st.rerun()

        # أدوات الإدارة في Tabs
        t_data, t_news = st.tabs(["📊 البيانات والفرز", "📢 إدارة الأخبار"])
        
        with t_news:
            new_txt = st.text_area("تعديل شريط الأخبار العلوي:", current_news)
            if st.button("تحديث الشريط"):
                c.execute("UPDATE settings SET value=? WHERE key='news'", (new_txt,))
                conn.commit()
                st.success("تم التحديث بنجاح!")

        with t_data:
            df = pd.read_sql("SELECT * FROM residents", conn)
            search = st.text_input("🔍 بحث بالاسم أو الهوية")
            if search:
                df = df[df['full_name'].str.contains(search) | df['id_num'].str.contains(search)]
            
            st.dataframe(df, use_container_width=True)
            
            # تصدير Excel
            towrite = io.BytesIO()
            df.to_excel(towrite, index=False)
            st.download_button("📥 تحميل قاعدة البيانات Excel", towrite.getvalue(), "Camp_Data_2026.xlsx")

            # حذف سجل
            st.divider()
            id_del = st.selectbox("اختر رقم الهوية للحذف نهائياً:", [""] + df['id_num'].tolist())
            if st.button("🗑 حذف السجل المختار"):
                c.execute("DELETE FROM residents WHERE id_num=?", (id_del,))
                conn.commit()
                st.warning("تم الحذف بنجاح")
                st.rerun()

st.sidebar.markdown("---")
st.sidebar.info(f"إصدار النظام: 2.0 (2026)")
