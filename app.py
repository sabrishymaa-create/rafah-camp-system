import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# 1. إعدادات الصفحة والتنسيق (2026 Style)
st.set_page_config(page_title="مخيم رفح السلام", layout="wide")

st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; height: 3em; background-color: #2E7D32; color: white; border: none; }
    .news-ticker { background: #b71c1c; color: white; padding: 10px; font-weight: bold; border-radius: 8px; margin-bottom: 20px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background: #f8f9fa; text-align: center; padding: 10px; font-weight: bold; border-top: 2px solid #2E7D32; z-index: 1000; }
    .main-header { background: #1b5e20; color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. إنشاء وقاعدة البيانات
conn = sqlite3.connect('rafah_camp_system_v2026.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS residents (id_num TEXT PRIMARY KEY, f1 TEXT, f2 TEXT, f3 TEXT, f4 TEXT, phone TEXT, health TEXT, social TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS family (p_id TEXT, type TEXT, name TEXT, id_num TEXT, dob TEXT, age TEXT, health TEXT, orphan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
c.execute("INSERT OR IGNORE INTO settings VALUES ('news', 'مرحباً بكم في منظومة مخيم رفح السلام الرقمية 2026 - بإدارة د. أكرم السدودي.')")
conn.commit()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'w_count' not in st.session_state: st.session_state.w_count = 1
if 'k_count' not in st.session_state: st.session_state.k_count = 1

# شريط الأخبار والهيدر
news_msg = c.execute("SELECT value FROM settings WHERE key='news'").fetchone()[0]
st.markdown(f'<div class="news-ticker"><marquee direction="right">{news_msg}</marquee></div>', unsafe_allow_html=True)
st.markdown('<div class="main-header"><h1>🏥 مخيم رفح السلام</h1><h4>إدارة الدكتور أكرم السدودي</h4></div>', unsafe_allow_html=True)

# 3. نظام الإدارة (ADMIN)
col_a1, col_a2 = st.columns([0.8, 0.2])
with col_a2:
    if not st.session_state.logged_in:
        with st.popover("🔐 دخول الإدارة"):
            u, p = st.text_input("المستخدم"), st.text_input("الكلمة", type="password")
            if st.button("دخول"):
                if u == "admin" and p == "123123": st.session_state.logged_in = True; st.rerun()
                else: st.error("خطأ")
    else:
        if st.button("🚪 خروج"): st.session_state.logged_in = False; st.rerun()

if st.session_state.logged_in:
    st.header("🛠 لوحة التحكم")
    t1, t2, t3 = st.tabs(["📊 البيانات والتحكم", "➕ إضافة يدوي", "⚙️ الإعدادات"])
    with t1:
        df = pd.read_sql("SELECT id_num as 'الهوية', f1||' '||f4 as 'الاسم', phone as 'الجوال', status as 'الحالة' FROM residents", conn)
        st.dataframe(df, use_container_width=True)
        sel = st.selectbox("اختر هوية للتعديل:", ["-- اختر --"] + list(df['الهوية']))
        if sel != "-- اختر --":
            res = c.execute("SELECT * FROM residents WHERE id_num=?", (sel,)).fetchone()
            with st.container(border=True):
                en1, eph = st.columns(2)
                new_n = en1.text_input("الاسم", value=res[1])
                new_p = eph.text_input("الجوال", value=res[5])
                new_s = st.selectbox("الحالة", ["قيد الانتظار", "مقبول", "مرفوض"], index=["قيد الانتظار", "مقبول", "مرفوض"].index(res[8]))
                c1, c2 = st.columns(2)
                if c1.button("💾 حفظ"): c.execute("UPDATE residents SET f1=?, phone=?, status=? WHERE id_num=?", (new_n, new_p, new_s, sel)); conn.commit(); st.rerun()
                if c2.button("🗑️ حذف"): c.execute("DELETE FROM residents WHERE id_num=?", (sel,)); conn.commit(); st.rerun()
    with t3:
        new_txt = st.text_area("تعديل شريط الأخبار", news_msg)
        if st.button("تحديث"): c.execute("UPDATE settings SET value=? WHERE key='news'", (new_txt,)); conn.commit(); st.rerun()

# 4. واجهة المستخدم (التسجيل)
else:
    col_w, col_k = st.columns(2)
    with col_w:
        if st.button("➕ زوجة"): st.session_state.w_count += 1; st.rerun()
    with col_k:
        if st.button("➕ ابن"): st.session_state.k_count += 1; st.rerun()

    with st.form("main_form"):
        st.subheader("👤 بيانات رب الأسرة")
        c1, c2, c3, c4 = st.columns(4)
        f1, f2, f3, f4 = c1.text_input("الأول"), c2.text_input("الثاني"), c3.text_input("الثالث"), c4.text_input("الرابع")
        id_num, ph = st.text_input("الهوية"), st.text_input("الجوال")
        sh, ss = st.columns(2)
        health = sh.selectbox("الصحة", ["سليم", "مزمن", "إعاقة"])
        social = ss.selectbox("الحالة الاجتماعية", ["متزوج", "أعزب", "أرمل", "مطلق", "مهجور", "منفصل"])

        # منطق الإخفاء المطلوب (5 حالات)
        if social not in ["أعزب", "أرمل", "مطلق", "مهجور", "منفصل"]:
            st.divider()
            for i in range(st.session_state.w_count):
                w1, w2 = st.columns(2)
                w1.text_input(f"الزوجة {i+1}", key=f"wn_{i}")
                w2.text_input(f"هوية الزوجة {i+1}", key=f"wi_{i}")

        st.divider()
        for j in range(st.session_state.k_count):
            k1, k2, k3, k4 = st.columns(4)
            kn = k1.text_input(f"اسم الابن {j+1}", key=f"kn_{j}")
            ki = k2.text_input(f"هوية {j+1}", key=f"ki_{j}")
            kd = k3.date_input(f"ميلاد {j+1}", value=datetime(2015,1,1), key=f"kd_{j}")
            # حساب العمر لعام 2026
            age = 2026 - kd.year
            k4.text_input("العمر", value=str(age), disabled=True, key=f"ka_{j}")
            ko = st.selectbox("اليتم", ["ليس يتيم", "يتيم الأب", "يتيم الأم", "كلاهما"], key=f"ko_{j}")

        if st.form_submit_button("💾 حفظ البيانات"):
            if f1 and id_num:
                c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?,?,?,?)", (id_num, f1, f2, f3, f4, ph, health, social, "قيد الانتظار"))
                conn.commit(); st.success("✅ تم الحفظ."); st.session_state.w_count, st.session_state.k_count = 1, 1
            else: st.error("أكمل البيانات")

st.markdown('<div class="footer">حقوق الملكية محفوظة باسم: ابوسفيان © 2026</div>', unsafe_allow_html=True)
