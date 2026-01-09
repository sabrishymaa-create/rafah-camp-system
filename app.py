import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse

# 1. إعدادات الصفحة
st.set_page_config(page_title="مخيم رفح السلام", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; height: 3em; }
    .news-ticker { background: #b71c1c; color: white; padding: 10px; font-weight: bold; overflow: hidden; white-space: nowrap; border-radius: 8px; margin-bottom: 20px; border-right: 5px solid #ffeb3b; }
    .ticker-text { display: inline-block; padding-right: 100%; animation: ticker 25s linear infinite; }
    @keyframes ticker { 0% { transform: translate(0, 0); } 100% { transform: translate(100%, 0); } }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8f9fa; color: #333; text-align: center; padding: 10px; font-weight: bold; border-top: 2px solid #2E7D32; z-index: 1000; }
    </style>
    """, unsafe_allow_html=True)

# 2. قاعدة البيانات
conn = sqlite3.connect('rafah_camp_2026_final_v3.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS residents (
    id_num TEXT PRIMARY KEY, f1 TEXT, f2 TEXT, f3 TEXT, f4 TEXT, 
    phone TEXT, health TEXT, social TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
conn.commit()

c.execute("INSERT OR IGNORE INTO settings VALUES ('news', 'مرحباً بكم في منظومة مخيم رفح السلام الرقمية 2026 - بإدارة د. أكرم السدودي.')")
conn.commit()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'show_login' not in st.session_state: st.session_state.show_login = False

# شريط الأخبار
c.execute("SELECT value FROM settings WHERE key='news'")
news_msg = c.fetchone()[0]
st.markdown(f'<div class="news-ticker"><div class="ticker-text">{news_msg}</div></div>', unsafe_allow_html=True)

# الهيدر وزر الدخول
h_col1, h_col2 = st.columns([0.8, 0.2])
with h_col1:
    st.title("🏥 مخيم رفح السلام")
    st.markdown(f"#### إدارة الدكتور أكرم السدودي")
with h_col2:
    if not st.session_state.logged_in:
        if st.button("🔐 دخول الإدارة"): st.session_state.show_login = not st.session_state.show_login
    else:
        if st.button("🚪 خروج"): 
            st.session_state.logged_in = False
            st.rerun()

if st.session_state.show_login and not st.session_state.logged_in:
    l_col1, l_col2 = st.columns(2)
    u = l_col1.text_input("Username")
    p = l_col2.text_input("Password", type="password")
    if st.button("تأكيد الدخول"):
        if u == "admin" and p == "123123":
            st.session_state.logged_in = True
            st.session_state.show_login = False
            st.rerun()
        else: st.error("بيانات خاطئة")

# 3. المحتوى الرئيسي
if st.session_state.logged_in:
    st.header("🛠 لوحة تحكم الإدارة")
    tab1, tab2, tab3 = st.tabs(["📊 إدارة الطلبات", "➕ إضافة طلب جديد", "📢 الإعدادات"])

    with tab1: # إدارة وتعديل الطلبات
        df = pd.read_sql("SELECT * FROM residents", conn)
        df_view = df.rename(columns={'id_num':'الهوية','f1':'الأول','f4':'الرابع','phone':'الجوال','status':'الحالة'})
        st.dataframe(df_view, use_container_width=True)
        
        target_id = st.selectbox("اختر رقم الهوية للتعديل أو الموافقة:", [""] + df['id_num'].tolist())
        if target_id:
            row = df[df['id_num'] == target_id].iloc[0]
            with st.expander("📝 تعديل بيانات أو حالة: " + row['f1']):
                edit_f1 = st.text_input("الاسم الأول", value=row['f1'])
                edit_phone = st.text_input("الجوال", value=row['phone'])
                edit_status = st.selectbox("تغيير الحالة", ["⏳ قيد الانتظار", "✅ مقبول", "❌ مرفوض"], 
                                           index=["⏳ قيد الانتظار", "✅ مقبول", "❌ مرفوض"].index(row['status']))
                
                col_up, col_del = st.columns(2)
                if col_up.button("💾 حفظ التعديلات"):
                    c.execute("UPDATE residents SET f1=?, phone=?, status=? WHERE id_num=?", (edit_f1, edit_phone, edit_status, target_id))
                    conn.commit(); st.success("تم التحديث"); st.rerun()
                if col_del.button("🗑 حذف السجل نهائياً"):
                    c.execute("DELETE FROM residents WHERE id_num=?", (target_id,))
                    conn.commit(); st.rerun()

    with tab2: # إضافة طلب من الإدارة
        st.subheader("إضافة نازح جديد مباشرة")
        with st.form("admin_add_form"):
            c1, c2, c3, c4 = st.columns(4)
            nf1, nid = c1.text_input("الاسم الأول"), c2.text_input("رقم الهوية")
            nph, nhe = c3.text_input("الجوال"), c4.selectbox("الصحة", ["سليم", "مزمن", "اعاقة"])
            if st.form_submit_button("إضافة الآن"):
                c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?,?,?,?)", (nid, nf1, "", "", "", nph, nhe, "متزوج", "✅ مقبول"))
                conn.commit(); st.success("تمت الإضافة بنجاح")

    with tab3: # تعديل شريط الأخبار
        new_news = st.text_area("تعديل الخبر:", news_msg)
        if st.button("تحديث"):
            c.execute("UPDATE settings SET value=? WHERE key='news'", (new_news,))
            conn.commit(); st.rerun()

else:
    # واجهة النازحين
    st.header("📝 تسجيل البيانات / الاستعلام عن حالة الطلب")
    mode = st.radio("اختر الإجراء:", ["إرسال طلب جديد", "الاستعلام عن حالة طلبي"])
    
    if mode == "إرسال طلب جديد":
        with st.form("user_form"):
            col1, col2 = st.columns(2)
            f1, id_n = col1.text_input("الاسم الأول"), col2.text_input("رقم الهوية")
            phone = col1.text_input("رقم الجوال")
            health = col2.selectbox("الحالة الصحية", ["سليم", "مزمن", "اعاقة حركية", "اعاقة سمعية", "اعاقة بصرية"])
            if st.form_submit_button("إرسال الطلب"):
                c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?,?,?,?)", (id_n, f1, "", "", "", phone, health, "متزوج", "⏳ قيد الانتظار"))
                conn.commit(); st.success("تم الإرسال بنجاح")
                
    else: # الاستعلام
        check_id = st.text_input("أدخل رقم هويتك للاستعلام:")
        if st.button("بحث"):
            res = pd.read_sql(f"SELECT f1, status FROM residents WHERE id_num='{check_id}'", conn)
            if not res.empty:
                st.info(f"مرحباً {res.iloc[0]['f1']}، حالة طلبك هي: {res.iloc[0]['status']}")
            else: st.error("رقم الهوية غير مسجل")

st.markdown(f'<div class="footer">حقوق الملكية محفوظة باسم: ابوسفيان © 2026</div>', unsafe_allow_html=True)
