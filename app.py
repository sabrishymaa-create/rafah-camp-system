import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse

# 1. إعدادات الصفحة والتصميم
st.set_page_config(page_title="مخيم رفح السلام", layout="wide")

# تصميم الواجهة ودعم العربية (RTL) مع شريط الأخبار المتحرك
st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #1e88e5; color: white; font-weight: bold; }
    
    .news-ticker {
        background: #b71c1c;
        color: white;
        padding: 10px;
        font-weight: bold;
        overflow: hidden;
        white-space: nowrap;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .ticker-text {
        display: inline-block;
        padding-right: 100%;
        animation: ticker 25s linear infinite;
    }
    @keyframes ticker {
        0% { transform: translate(0, 0); }
        100% { transform: translate(100%, 0); }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. الاتصال بقاعدة البيانات
conn = sqlite3.connect('camp_system_complete_2026.db', check_same_thread=False)
c = conn.cursor()

# إنشاء الجداول
c.execute('''CREATE TABLE IF NOT EXISTS residents (
    id_num TEXT PRIMARY KEY, full_name TEXT, phone TEXT, health TEXT, social TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
conn.commit()

# إعداد شريط الأخبار الافتراضي
c.execute("INSERT OR IGNORE INTO settings VALUES ('news', 'أهلاً بكم في مخيم رفح السلام - إدارة الدكتور أكرم السدودي - يرجى الالتزام بتعليمات الإدارة وتحديث بياناتكم دورياً.')")
conn.commit()

# 3. إدارة حالة الجلسة (Session State) للأزرار
if 'wives_count' not in st.session_state: st.session_state.wives_count = 0
if 'kids_count' not in st.session_state: st.session_state.kids_count = 0

def add_wife(): st.session_state.wives_count += 1
def add_kid(): st.session_state.kids_count += 1

# --- عرض شريط الأخبار في الأعلى ---
c.execute("SELECT value FROM settings WHERE key='news'")
current_news = c.fetchone()[0]
st.markdown(f'<div class="news-ticker"><div class="ticker-text">{current_news}</div></div>', unsafe_allow_html=True)

# --- الهيدر الرئيسي ---
st.title("🏥 مخيم رفح السلام | Rafah Peace Camp")
st.markdown(f"#### إدارة الدكتور أكرم السدودي")
st.write(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d')} | حقوق الملكية: ابوسفيان")

# القائمة الجانبية
menu = ["📝 تسجيل البيانات (Registration)", "🔐 لوحة التحكم (Admin Panel)"]
choice = st.sidebar.selectbox("اختر الصفحة / Menu", menu)

if choice == "📝 تسجيل البيانات (Registration)":
    st.header("📋 استمارة تسجيل النازحين")
    with st.form("main_form"):
        col1, col2 = st.columns(2)
        f_name = col1.text_input("الاسم رباعي")
        id_num = col2.text_input("رقم الهوية")
        phone = col1.text_input("رقم الجوال (بمفتاح الدولة مثلا 970)")
        
        h_opts = ["سليم", "مزمن", "اعاقة حركية", "اعاقة سمعية", "اعاقة بصرية"]
        health = col2.selectbox("الحالة الصحية", h_opts)
        
        s_opts = ["متزوج/ة", "مطلق/ه", "ارمل/ه", "منفصل", "مهجور/ه", "اعزب"]
        social = col1.selectbox("الحالة الاجتماعية", s_opts)

        st.subheader("💍 بيانات الزوجات")
        for i in range(st.session_state.wives_count):
            w1, w2 = st.columns(2)
            w1.text_input(f"اسم الزوجة {i+1} رباعي", key=f"wn_{i}")
            w2.text_input(f"هوية الزوجة {i+1}", key=f"wi_{i}")
        st.form_submit_button("➕ إضافة زوجة أخرى", on_click=add_wife)

        st.subheader("👶 بيانات الأبناء")
        for j in range(st.session_state.kids_count):
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.text_input(f"الاسم رباعي {j+1}", key=f"kn_{j}")
            k2.text_input(f"رقم الهوية {j+1}", key=f"ki_{j}")
            k3.date_input(f"تاريخ الميلاد {j+1}", key=f"kd_{j}")
            k4.selectbox(f"الصحة {j+1}", h_opts, key=f"kh_{j}")
            k5.selectbox(f"اليتم {j+1}", ["ليس يتيم", "يتيم الأب", "يتيم الأم", "كلاهما"], key=f"ko_{j}")
        st.form_submit_button("➕ إضافة ابن/ابنة", on_click=add_kid)

        save_btn = st.form_submit_button("💾 حفظ البيانات النهائية")
        if save_btn:
            if f_name and id_num:
                c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?)", (id_num, f_name, phone, health, social, "نشط"))
                conn.commit()
                st.success(f"✅ تم حفظ بيانات {f_name} بنجاح")
            else:
                st.error("⚠️ يرجى تعبئة الاسم ورقم الهوية")

elif choice == "🔐 لوحة التحكم (Admin Panel)":
    st.sidebar.header("دخول المسؤول")
    user = st.sidebar.text_input("Username")
    pw = st.sidebar.text_input("Password", type="password")
    
    if user == "admin" and pw == "admin123":
        st.header("🛠 لوحة الإدارة - د. أكرم السدودي")
        
        with st.expander("📢 تعديل شريط الأخبار"):
            new_news = st.text_area("اكتب الخبر الجديد هنا:", current_news)
            if st.button("تحديث الشريط"):
                c.execute("UPDATE settings SET value=? WHERE key='news'", (new_news,))
                conn.commit()
                st.rerun()

        df = pd.read_sql("SELECT * FROM residents", conn)
        q = st.text_input("🔍 بحث سريع (اسم أو هوية)")
        if q: df = df[df['full_name'].str.contains(q) | df['id_num'].str.contains(q)]
        st.dataframe(df, use_container_width=True)

        st.subheader("📱 تواصل سريع مع الأشخاص")
        if not df.empty:
            selected_user = st.selectbox("اختر شخصاً للتواصل معه:", df['full_name'].tolist())
            user_data = df[df['full_name'] == selected_user].iloc[0]
            u_phone = str(user_data['phone'])
            msg = st.text_area("نص الرسالة:", "مرحباً، يرجى مراجعة إدارة مخيم رفح السلام.")
            
            col_sms, col_wa = st.columns(2)
            # زر واتساب
            wa_link = f"wa.me{u_phone}?text={urllib.parse.quote(msg)}"
            col_wa.markdown(f'<a href="{wa_link}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer;">ارسال WhatsApp</button></a>', unsafe_allow_html=True)
            
            # زر SMS (يعمل على الجوالات)
            sms_link = f"sms:{u_phone}?body={urllib.parse.quote(msg)}"
            col_sms.markdown(f'<a href="{sms_link}"><button style="width:100%; background-color:#007AFF; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer;">ارسال رسالة SMS</button></a>', unsafe_allow_html=True)

        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            target = st.selectbox("حذف سجل:", [""] + df['id_num'].tolist())
            if st.button("🗑 حذف الآن"):
                c.execute("DELETE FROM residents WHERE id_num=?", (target,))
                conn.commit()
                st.rerun()
        with col_b:
            towrite = io.BytesIO()
            df.to_excel(towrite, index=False, header=True)
            st.download_button(label="📥 تصدير Excel", data=towrite.getvalue(), file_name="Camp_Report.xlsx")

st.sidebar.markdown("---")
st.sidebar.write("© 2026 | حقوق الملكية: **ابوسفيان**")
