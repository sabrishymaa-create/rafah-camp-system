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
    .ticker-text { display: inline-block; padding-right: 100%; animation: ticker 30s linear infinite; }
    @keyframes ticker { 0% { transform: translate(0, 0); } 100% { transform: translate(100%, 0); } }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8f9fa; color: #333; text-align: center; padding: 10px; font-weight: bold; border-top: 2px solid #2E7D32; z-index: 1000; }
    .login-section { background: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. قاعدة البيانات - تم تغيير اسم الملف لضمان إنشاء جداول جديدة نظيفة
conn = sqlite3.connect('rafah_camp_2026_v2.db', check_same_thread=False)
c = conn.cursor()
# إنشاء الجدول بـ 9 أعمدة بدقة
c.execute('''CREATE TABLE IF NOT EXISTS residents (
    id_num TEXT PRIMARY KEY, f1 TEXT, f2 TEXT, f3 TEXT, f4 TEXT, 
    phone TEXT, health TEXT, social TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
conn.commit()

c.execute("INSERT OR IGNORE INTO settings VALUES ('news', 'مرحباً بكم في منظومة مخيم رفح السلام الرقمية لعام 2026 - بإدارة د. أكرم السدودي.')")
conn.commit()

# حالة الجلسة
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'show_login' not in st.session_state: st.session_state.show_login = False
if 'wives_count' not in st.session_state: st.session_state.wives_count = 1
if 'kids_count' not in st.session_state: st.session_state.kids_count = 1

# شريط الأخبار
c.execute("SELECT value FROM settings WHERE key='news'")
news_msg = c.fetchone()
st.markdown(f'<div class="news-ticker"><div class="ticker-text">{news_msg[0]}</div></div>', unsafe_allow_html=True)

# الهيدر وزر الدخول (أعلى اليسار)
h_col1, h_col2 = st.columns([0.8, 0.2])
with h_col1:
    st.title("🏥 مخيم رفح السلام")
    st.markdown(f"#### إدارة الدكتور أكرم السدودي")
with h_col2:
    if not st.session_state.logged_in:
        if st.button("🔐 دخول الإدارة"):
            st.session_state.show_login = not st.session_state.show_login
    else:
        if st.button("🚪 تسجيل خروج"):
            st.session_state.logged_in = False
            st.rerun()

# واجهة تسجيل الدخول
if st.session_state.show_login and not st.session_state.logged_in:
    with st.container():
        st.markdown('<div class="login-section">', unsafe_allow_html=True)
        l_col1, l_col2 = st.columns(2)
        u = l_col1.text_input("اسم المستخدم")
        p = l_col2.text_input("كلمة المرور", type="password")
        if st.button("تأكيد الدخول"):
            if u == "admin" and p == "123123":
                st.session_state.logged_in = True
                st.session_state.show_login = False
                st.rerun()
            else: st.error("❌ بيانات الدخول غير صحيحة")
        st.markdown('</div>', unsafe_allow_html=True)

# 3. المحتوى الرئيسي
if st.session_state.logged_in:
    st.header("🛠 لوحة تحكم الإدارة")
    t1, t2 = st.tabs(["📊 البيانات والموافقة", "📢 تعديل الشريط الإخباري"])
    
    with t2:
        new_news = st.text_area("تعديل نص الشريط:", news_msg[0])
        if st.button("حفظ وتحديث الشريط"):
            c.execute("UPDATE settings SET value=? WHERE key='news'", (new_news,))
            conn.commit(); st.rerun()

    with t1:
        df = pd.read_sql("SELECT * FROM residents", conn)
        df_arabic = df.rename(columns={
            'id_num': 'رقم الهوية', 'f1': 'الاسم الأول', 'f2': 'الثاني', 'f3': 'الثالث', 'f4': 'الرابع',
            'phone': 'الجوال', 'health': 'الصحة', 'social': 'الحالة الاجتماعية', 'status': 'حالة الطلب'
        })
        
        q = st.text_input("🔍 بحث سريع بالاسم أو الهوية")
        if q:
            df_arabic = df_arabic[df_arabic['رقم الهوية'].astype(str).str.contains(q) | df_arabic['الاسم الأول'].str.contains(q)]
        
        st.dataframe(df_arabic, use_container_width=True)
        
        st.divider()
        target_id = st.selectbox("اختر رقم الهوية لاتخاذ إجراء:", [""] + df['id_num'].tolist())
        if target_id:
            row = df[df['id_num'] == target_id].iloc[0]
            st.info(f"الاسم: {row['f1']} {row['f4']} | الحالة: {row['status']}")
            
            c1, c2, c3, c4, c5 = st.columns(5)
            if c1.button("✅ موافقة"):
                c.execute("UPDATE residents SET status='✅ مقبول' WHERE id_num=?", (target_id,))
                conn.commit(); st.rerun()
            if c2.button("❌ رفض"):
                c.execute("UPDATE residents SET status='❌ مرفوض' WHERE id_num=?", (target_id,))
                conn.commit(); st.rerun()
            if c3.button("🗑 حذف"):
                c.execute("DELETE FROM residents WHERE id_num=?", (target_id,))
                conn.commit(); st.rerun()
            
            msg_encoded = urllib.parse.quote(f"مرحباً {row['f1']}، يرجى مراجعة إدارة المخيم.")
            c4.markdown(f'<a href="wa.me{row["phone"]}?text={msg_encoded}" target="_blank"><button style="background:#25D366; color:white; border:none; padding:10px; border-radius:5px;">WhatsApp</button></a>', unsafe_allow_html=True)
            c5.markdown(f'<a href="sms:{row["phone"]}?body={msg_encoded}"><button style="background:#007AFF; color:white; border:none; padding:10px; border-radius:5px;">SMS</button></a>', unsafe_allow_html=True)

        buffer = io.BytesIO()
        df_arabic.to_excel(buffer, index=False)
        st.download_button("📥 تحميل ملف Excel بالعربي", buffer.getvalue(), "Report_2026.xlsx")

else:
    st.header("📝 استمارة تسجيل نازح جديد")
    with st.form("main_form"):
        col1, col2, col3, col4 = st.columns(4)
        f1, f2, f3, f4 = col1.text_input("الاسم الأول"), col2.text_input("الثاني"), col3.text_input("الثالث"), col4.text_input("الرابع")
        id_num, phone = st.text_input("رقم الهوية"), st.text_input("رقم الجوال")
        
        h_col, s_col = st.columns(2)
        health = h_col.selectbox("الحالة الصحية", ["سليم", "مزمن", "اعاقة حركية", "إعاقة سمعية", "إعاقة بصرية"])
        social = s_col.selectbox("الحالة الاجتماعية", ["متزوج", "مطلق/ه", "ارمل/ه", "منفصل", "مهجور/ه"])
        
        st.subheader("💍 بيانات الزوجات")
        for i in range(st.session_state.wives_count):
            wc1, wc2 = st.columns(2)
            wc1.text_input(f"اسم الزوجة {i+1} رباعي", key=f"wn_{i}")
            wc2.text_input(f"هوية الزوجة {i+1}", key=f"wi_{i}")
        if st.form_submit_button("➕ إضافة زوجة"):
            st.session_state.wives_count += 1; st.rerun()

        st.subheader("👶 بيانات الأبناء")
        for j in range(st.session_state.kids_count):
            kc1, kc2, kc3, kc4 = st.columns(4)
            kn = kc1.text_input(f"اسم الابن {j+1}", key=f"kn_{j}")
            ki = kc2.text_input(f"هوية {j+1}", key=f"ki_{j}")
            kd = kc3.date_input(f"تاريخ ميلاد {j+1}", key=f"kd_{j}")
            ko = kc4.selectbox(f"اليتم {j+1}", ["ليس يتيم", "يتيم الأب", "يتيم الأم", "كلاهما"], key=f"ko_{j}")
        if st.form_submit_button("➕ إضافة ابن"):
            st.session_state.kids_count += 1; st.rerun()

        if st.form_submit_button("💾 حفظ البيانات وإرسال الطلب"):
            if f1 and id_num:
                # هذا السطر الآن يطابق الجدول تماماً بـ 9 قيم
                c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?,?,?,?)", 
                          (id_num, f1, f2, f3, f4, phone, health, social, '⏳ قيد الانتظار'))
                conn.commit(); st.success("✅ تم حفظ البيانات بنجاح")
            else: st.error("⚠️ يرجى تعبئة الاسم الأول ورقم الهوية")

st.markdown(f'<div class="footer">حقوق الملكية محفوظة باسم: ابوسفيان © 2026</div>', unsafe_allow_html=True)
