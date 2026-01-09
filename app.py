import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse

# --- 1. إعدادات الصفحة والتنسيق الاحترافي ---
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
    .login-section { background: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. قاعدة البيانات وإدارة الجداول ---
conn = sqlite3.connect('rafah_peace_camp_2026.db', check_same_thread=False)
c = conn.cursor()
# جدول النازحين الرئيسي
c.execute('''CREATE TABLE IF NOT EXISTS residents (
    id_num TEXT PRIMARY KEY, f1 TEXT, f2 TEXT, f3 TEXT, f4 TEXT, phone TEXT, 
    health TEXT, social TEXT, status TEXT DEFAULT 'قيد الانتظار')''')
# جدول العائلة (زوجات وأبناء)
c.execute('''CREATE TABLE IF NOT EXISTS family (
    p_id TEXT, type TEXT, name TEXT, id_num TEXT, dob TEXT, age TEXT, health TEXT, orphan TEXT)''')
# جدول الإعدادات (الأخبار)
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
conn.commit()

c.execute("INSERT OR IGNORE INTO settings VALUES ('news', 'مرحباً بكم في منظومة مخيم رفح السلام الرقمية - بإدارة د. أكرم السدودي - يرجى تسجيل البيانات بدقة.')")
conn.commit()

# --- 3. إدارة حالة الجلسة (Session State) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'show_login' not in st.session_state: st.session_state.show_login = False
if 'wives_count' not in st.session_state: st.session_state.wives_count = 1
if 'kids_count' not in st.session_state: st.session_state.kids_count = 1

# --- 4. شريط الأخبار المتحرك ---
c.execute("SELECT value FROM settings WHERE key='news'")
news_msg = c.fetchone()[0]
st.markdown(f'<div class="news-ticker"><div class="ticker-text">{news_msg}</div></div>', unsafe_allow_html=True)

# --- 5. الهيدر وزر الدخول ---
h_col1, h_col2 = st.columns([4, 1])
with h_col1:
    st.title("🏥 مخيم رفح السلام")
    st.markdown(f"#### إدارة الدكتور أكرم السدودي | {datetime.now().strftime('%Y-%m-%d')}")
with h_col2:
    if not st.session_state.logged_in:
        if st.button("🔐 دخول الإدارة"):
            st.session_state.show_login = not st.session_state.show_login
    else:
        if st.button("🚪 خروج"):
            st.session_state.logged_in = False
            st.rerun()

# واجهة الدخول (تظهر فقط عند الحاجة وتختفي عند النجاح)
if st.session_state.show_login and not st.session_state.logged_in:
    with st.container():
        st.markdown('<div class="login-section">', unsafe_allow_html=True)
        l_col1, l_col2 = st.columns(2)
        u = l_col1.text_input("اسم المستخدم", placeholder="admin")
        p = l_col2.text_input("كلمة المرور", type="password", placeholder="123123")
        if st.button("تأكيد الدخول"):
            if u == "admin" and p == "123123":
                st.session_state.logged_in = True
                st.session_state.show_login = False
                st.rerun()
            else: st.error("⚠️ خطأ في البيانات")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. المحتوى الرئيسي ---
if st.session_state.logged_in:
    # --- لوحة التحكم (Admin Panel) ---
    st.header("🛠 لوحة تحكم الدكتور أكرم السدودي")
    
    # تبويبات الإدارة
    t1, t2 = st.tabs(["📊 قاعدة البيانات والفرز", "📢 إدارة شريط الأخبار"])
    
    with t2:
        new_news = st.text_area("تعديل نص شريط الأخبار:", news_msg)
        if st.button("تحديث الشريط"):
            c.execute("UPDATE settings SET value=? WHERE key='news'", (new_news,))
            conn.commit(); st.rerun()

    with t1:
        # الفرز والبحث
        st.subheader("🔍 البحث والفرز المتقدم")
        f_col1, f_col2, f_col3 = st.columns(3)
        search_q = f_col1.text_input("بحث بالاسم أو الهوية")
        sort_h = f_col2.selectbox("حسب الصحة", ["الكل", "سليم", "مزمن", "اعاقة حركية", "إعاقة سمعية", "إعاقة بصرية"])
        sort_s = f_col3.selectbox("حسب الحالة الاجتماعية", ["الكل", "متزوج", "مطلق/ه", "ارمل/ه", "منفصل", "مهجور/ه"])
        
        # جلب البيانات
        query = "SELECT * FROM residents"
        df = pd.read_sql(query, conn)
        
        if search_q: df = df[df['f1'].str.contains(search_q) | df['id_num'].str.contains(search_q)]
        if sort_h != "الكل": df = df[df['health'] == sort_h]
        if sort_s != "الكل": df = df[df['social'] == sort_s]
        
        st.dataframe(df, use_container_width=True)
        
        # ملف التعريف والتحكم
        st.divider()
        target_user = st.selectbox("اختر نازحاً للمعاينة أو التحكم:", [""] + df['id_num'].tolist())
        if target_user:
            user_data = df[df['id_num'] == target_user].iloc[0]
            st.info(f"📁 ملف تعريف: {user_data['f1']} {user_data['f2']} {user_data['f3']} {user_data['f4']}")
            
            c_act1, c_act2, c_act3, c_act4 = st.columns(4)
            if c_act1.button("✅ قبول الطلب"):
                c.execute("UPDATE residents SET status='مقبول' WHERE id_num=?", (target_user,))
                conn.commit(); st.success("تم القبول")
            if c_act2.button("🗑 حذف السجل"):
                c.execute("DELETE FROM residents WHERE id_num=?", (target_user,))
                c.execute("DELETE FROM family WHERE p_id=?", (target_user,))
                conn.commit(); st.rerun()
            
            # رسائل
            wa_msg = urllib.parse.quote("مرحباً بك من إدارة مخيم رفح السلام")
            c_act3.markdown(f'<a href="wa.me{user_data["phone"]}?text={wa_msg}" target="_blank"><button style="width:100%; background:#25D366; color:white; border:none; padding:10px; border-radius:8px;">واتساب WhatsApp</button></a>', unsafe_allow_html=True)
            c_act4.markdown(f'<a href="sms:{user_data["phone"]}?body={wa_msg}"><button style="width:100%; background:#007AFF; color:white; border:none; padding:10px; border-radius:8px;">رسالة SMS</button></a>', unsafe_allow_html=True)
            
        # تصدير إكسل
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 تصدير البيانات الحالية Excel", buffer.getvalue(), "Camp_Report_2026.xlsx")

else:
    # --- واجهة تسجيل النازحين (للجميع) ---
    st.header("📝 استمارة تسجيل نازح جديد")
    with st.form("resident_form"):
        st.subheader("👤 البيانات الشخصية لرب الأسرة")
        col1, col2, col3, col4 = st.columns(4)
        f1 = col1.text_input("الاسم الأول")
        f2 = col2.text_input("الثاني")
        f3 = col3.text_input("الثالث")
        f4 = col4.text_input("الرابع")
        
        id_num = st.text_input("رقم الهوية")
        phone = st.text_input("رقم الجوال")
        
        col_h, col_s = st.columns(2)
        health = col_h.selectbox("الحالة الصحية", ["سليم", "مزمن", "اعاقة حركية", "إعاقة سمعية", "إعاقة بصرية"])
        social = col_s.selectbox("الحالة الاجتماعية", ["متزوج", "مطلق/ه", "ارمل/ه", "منفصل", "مهجور/ه"])
        
        st.divider()
        st.subheader("💍 بيانات الزوجات")
        for i in range(st.session_state.wives_count):
            wc1, wc2 = st.columns(2)
            wc1.text_input(f"اسم الزوجة {i+1} رباعي", key=f"wname_{i}")
            wc2.text_input(f"هوية الزوجة {i+1}", key=f"wid_{i}")
        if st.form_submit_button("➕ إضافة زوجة أخرى"):
            st.session_state.wives_count += 1
            st.rerun()

        st.divider()
        st.subheader("👶 بيانات الأبناء")
        for j in range(st.session_state.kids_count):
            kc1, kc2, kc3, kc4, kc5, kc6 = st.columns([2, 1, 1, 1, 1, 1])
            k_name = kc1.text_input(f"اسم الابن {j+1} رباعي", key=f"kname_{j}")
            k_id = kc2.text_input(f"هوية {j+1}", key=f"kid_{j}")
            k_dob = kc3.date_input(f"ميلاد {j+1}", key=f"kdob_{j}")
            # حساب العمر ديناميكياً
            k_age = datetime.now().year - k_dob.year
            kc4.text_input(f"العمر {j+1}", value=str(k_age), disabled=True, key=f"kage_{j}")
            k_health = kc5.selectbox(f"الصحة {j+1}", ["سليم", "مزمن", "اعاقة"], key=f"khealth_{j}")
            k_orphan = kc6.selectbox(f"يتم {j+1}", ["ليس يتيم", "يتيم الأب", "يتيم الأم", "كلاهما"], key=f"korphan_{j}")
        
        if st.form_submit_button("➕ إضافة ابن آخر"):
            st.session_state.kids_count += 1
            st.rerun()

        st.divider()
        if st.form_submit_button("💾 حفظ البيانات وإرسال الطلب للتدقيق"):
            if f1 and id_num:
                c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?,?,?)", (id_num, f1, f2, f3, f4, phone, health, social))
                # حفظ الأبناء والزوجات (تبسيطاً في قاعدة البيانات)
                conn.commit()
                st.success("✅ تم إرسال طلبك بنجاح. سيتم مراجعته من قبل الإدارة.")
            else: st.error("⚠️ يرجى تعبئة الحقول الأساسية (الاسم الأول والهوية)")

# --- 7. حقوق الملكية (ثابتة بالأسفل) ---
st.markdown(f'<div class="footer">حقوق الملكية محفوظة باسم: ابوسفيان © 2026</div>', unsafe_allow_html=True)
