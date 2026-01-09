import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse

# 1. إعدادات الصفحة والتنسيق (UI) لعام 2026
st.set_page_config(page_title="مخيم رفح السلام", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; }
    .news-ticker { background: #b71c1c; color: white; padding: 10px; font-weight: bold; overflow: hidden; white-space: nowrap; border-radius: 8px; margin-bottom: 20px; border-right: 5px solid #ffeb3b; }
    .ticker-text { display: inline-block; padding-right: 100%; animation: ticker 30s linear infinite; }
    @keyframes ticker { 0% { transform: translate(0, 0); } 100% { transform: translate(100%, 0); } }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8f9fa; color: #333; text-align: center; padding: 10px; font-weight: bold; border-top: 2px solid #2E7D32; z-index: 1000; }
    .login-section { background: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. قاعدة البيانات (إصلاح الأعمدة)
conn = sqlite3.connect('rafah_peace_camp_2026.db', check_same_thread=False)
c = conn.cursor()
# جدول النازحين (9 أعمدة)
c.execute('''CREATE TABLE IF NOT EXISTS residents (
    id_num TEXT PRIMARY KEY, f1 TEXT, f2 TEXT, f3 TEXT, f4 TEXT, 
    phone TEXT, health TEXT, social TEXT, status TEXT)''')
# جدول العائلة
c.execute('''CREATE TABLE IF NOT EXISTS family (
    p_id TEXT, type TEXT, name TEXT, id_num TEXT, dob TEXT, age TEXT, health TEXT, orphan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
conn.commit()

c.execute("INSERT OR IGNORE INTO settings VALUES ('news', 'مرحباً بكم في مخيم رفح السلام د. أكرم السدودي - يرجى تسجيل البيانات بدقة.')")
conn.commit()

# 3. إدارة حالة الجلسة
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'show_login' not in st.session_state: st.session_state.show_login = False
if 'wives_count' not in st.session_state: st.session_state.wives_count = 1
if 'kids_count' not in st.session_state: st.session_state.kids_count = 1

# --- شريط الأخبار ---
c.execute("SELECT value FROM settings WHERE key='news'")
news_msg = c.fetchone()[0]
st.markdown(f'<div class="news-ticker"><div class="ticker-text">{news_msg}</div></div>', unsafe_allow_html=True)

# --- الهيدر العلوي وزر الدخول ---
h_col1, h_col2 = st.columns([0.8, 0.2])
with h_col1:
    st.title("🏥 مخيم رفح السلام")
    st.markdown(f"####  أكرم السدودي | {datetime.now().strftime('%Y-%m-%d')}")
with h_col2:
    if not st.session_state.logged_in:
        if st.button("🔐 دخول الإدارة"):
            st.session_state.show_login = not st.session_state.show_login
    else:
        if st.button("🚪 خروج"):
            st.session_state.logged_in = False
            st.rerun()

# واجهة الدخول (تظهر وتختفي بدقة)
if st.session_state.show_login and not st.session_state.logged_in:
    with st.container():
        st.markdown('<div class="login-section">', unsafe_allow_html=True)
        l_col1, l_col2 = st.columns(2)
        u = l_col1.text_input("اسم المستخدم")
        p = l_col2.text_input("كلمة المرور", type="password")
        if st.button("تأكيد الدخول"):
            if u == "....." and p == "....":
                st.session_state.logged_in = True
                st.session_state.show_login = False
                st.rerun()
            else: st.error("⚠️ بيانات خاطئة")
        st.markdown('</div>', unsafe_allow_html=True)

# 4. المحتوى الرئيسي
if st.session_state.logged_in:
    # --- لوحة التحكم (Admin Panel) ---
    st.header("🛠 لوحة الإدارة")
    t1, t2 = st.tabs(["📊 البيانات والفرز", "📢 تعديل الأخبار"])
    
    with t2:
        new_news = st.text_area("تعديل الخبر:", news_msg)
        if st.button("حفظ الخبر"):
            c.execute("UPDATE settings SET value=? WHERE key='news'", (new_news,))
            conn.commit(); st.rerun()

    with t1:
        df = pd.read_sql("SELECT * FROM residents", conn)
        q = st.text_input("🔍 بحث بالاسم أو الهوية")
        if q: df = df[df['f1'].str.contains(q) | df['id_num'].str.contains(q)]
        st.dataframe(df, use_container_width=True)
        
        # تصدير إكسل
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 تحميل Excel", buffer.getvalue(), "Camp_Report.xlsx")

        # حذف وتعديل
        target = st.selectbox("اختر رقم هوية للإجراء:", [""] + df['id_num'].tolist())
        if target:
            col_a, col_b = st.columns(2)
            if col_a.button("✅ قبول"):
                c.execute("UPDATE residents SET status='مقبول' WHERE id_num=?", (target,))
                conn.commit(); st.success("تم القبول")
            if col_b.button("🗑 حذف"):
                c.execute("DELETE FROM residents WHERE id_num=?", (target,))
                conn.commit(); st.rerun()

else:
    # --- واجهة التسجيل ---
    st.header("📝 تسجيل نازح جديد")
    with st.form("resident_form"):
        col1, col2, col3, col4 = st.columns(4)
        f1, f2, f3, f4 = col1.text_input("الأول"), col2.text_input("الثاني"), col3.text_input("الثالث"), col4.text_input("الرابع")
        id_num, phone = st.text_input("رقم الهوية"), st.text_input("رقم الجوال")
        
        h_col, s_col = st.columns(2)
        health = h_col.selectbox("الحالة الصحية", ["سليم", "مزمن", "اعاقة حركية", "إعاقة سمعية", "إعاقة بصرية"])
        social = s_col.selectbox("الحالة الاجتماعية", ["متزوج", "مطلق/ه", "ارمل/ه", "منفصل", "مهجور/ه"])
        
        st.subheader("💍 الزوجات")
        for i in range(st.session_state.wives_count):
            wc1, wc2 = st.columns(2)
            wc1.text_input(f"اسم الزوجة {i+1}", key=f"wname_{i}")
            wc2.text_input(f"هوية الزوجة {i+1}", key=f"wid_{i}")
        if st.form_submit_button("➕ زوجة أخرى"):
            st.session_state.wives_count += 1
            st.rerun()

        st.subheader("👶 الأبناء")
        for j in range(st.session_state.kids_count):
            kc1, kc2, kc3, kc4 = st.columns([3, 2, 2, 2])
            k_name = kc1.text_input(f"اسم الابن {j+1}", key=f"kn_{j}")
            k_id = kc2.text_input(f"هوية {j+1}", key=f"ki_{j}")
            k_dob = kc3.date_input(f"ميلاد {j+1}", key=f"kd_{j}")
            k_orphan = kc4.selectbox(f"اليتم {j+1}", ["ليس يتيم", "يتيم الأب", "يتيم الأم", "كلاهما"], key=f"ko_{j}")
        if st.form_submit_button("➕ ابن آخر"):
            st.session_state.kids_count += 1
            st.rerun()

        if st.form_submit_button("💾 حفظ البيانات النهائية"):
            if f1 and id_num:
                # تصحيح عدد الأعمدة هنا (9 قيم تطابق 9 أعمدة)
                c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?,?,?,?)", 
                          (id_num, f1, f2, f3, f4, phone, health, social, 'قيد الانتظار'))
                conn.commit()
                st.success("✅ تم الحفظ بنجاح")
            else: st.error("⚠️ أدخل البيانات الأساسية")

# حقوق الملكية بالأسفل
st.markdown('<div class="footer">حقوق الملكية محفوظة باسم: ابوسفيان © 2026</div>', unsafe_allow_html=True)
