import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse

# 1. إعدادات الصفحة
st.set_page_config(page_title="مخيم رفح السلام", layout="wide", initial_sidebar_state="expanded")

# 2. التنسيق الجمالي وحل مشكلة التشويش
st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #2E7D32; color: white; font-weight: bold; }
    .main-box { background-color: #f9f9f9; padding: 20px; border-radius: 15px; border: 1px solid #ddd; }
    .news-ticker { background: #b71c1c; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 20px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #eeeeee; color: black; text-align: center; padding: 10px; font-weight: bold; border-top: 2px solid #2E7D32; }
    </style>
    """, unsafe_allow_html=True)

# 3. إدارة قاعدة البيانات
conn = sqlite3.connect('camp_system_v2026.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS residents (id_num TEXT PRIMARY KEY, name TEXT, phone TEXT, health TEXT, social TEXT, family_details TEXT)''')
conn.commit()

# تهيئة حالة الدخول لمنع مشاكل كلمة المرور
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- الواجهة العلوية ---
st.markdown('<div class="news-ticker"><marquee direction="right">مرحباً بكم في مخيم رفح السلام - بإدارة د. أكرم السدودي - يرجى تسجيل البيانات بدقة.</marquee></div>', unsafe_allow_html=True)
st.title("🏥 مخيم رفح السلام")
st.markdown("#### إدارة الدكتور أكرم السدودي")

# --- القائمة الجانبية (لحل مشكلة التشويش) ---
st.sidebar.title("🔐 تسجيل الدخول للإدارة")
if not st.session_state['logged_in']:
    admin_user = st.sidebar.text_input("اسم المستخدم", key="user")
    admin_pass = st.sidebar.text_input("كلمة المرور", type="password", key="pass")
    if st.sidebar.button("دخول الإدارة"):
        if admin_user == "admin" and admin_pass == "admin123":
            st.session_state['logged_in'] = True
            st.sidebar.success("تم الدخول بنجاح")
            st.rerun()
        else:
            st.sidebar.error("بيانات الدخول خاطئة")
else:
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- اختيار الصفحات ---
menu = ["📝 تسجيل جديد", "📊 لوحة التحكم"]
choice = st.selectbox("انتقل إلى:", menu)

if choice == "📝 تسجيل جديد":
    st.subheader("📋 استمارة تسجيل نازح وعائلته")
    with st.container():
        with st.form("reg_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("الاسم الرباعي الكامل")
            id_num = col2.text_input("رقم الهوية")
            phone = col1.text_input("رقم الجوال")
            health = col2.selectbox("الحالة الصحية", ["سليم", "مزمن", "اعاقة حركية", "اعاقة سمعية", "اعاقة بصرية"])
            social = col1.selectbox("الحالة الاجتماعية", ["متزوج/ة", "مطلق/ه", "ارمل/ه", "منفصل", "مهجور/ه"])
            
            st.markdown("---")
            st.subheader("👨‍👩‍👧‍👦 بيانات الزوجات والأبناء")
            family_info = st.text_area("أدخل أسماء الزوجات والأبناء، أرقام هوياتهم، وحالتهم (مثال: الاسم - الهوية - يتيم/إعاقة)")
            
            submit = st.form_submit_button("💾 حفظ البيانات بشكل نهائي")
            if submit:
                if name and id_num:
                    c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?)", (id_num, name, phone, health, social, family_info))
                    conn.commit()
                    st.success(f"✅ تم حفظ بيانات {name} بنجاح")
                else:
                    st.error("⚠️ يرجى تعبئة الاسم ورقم الهوية")

elif choice == "📊 لوحة التحكم":
    if st.session_state['logged_in']:
        st.subheader("🛠 لوحة إدارة البيانات - د. أكرم السدودي")
        
        # جلب وعرض البيانات
        df = pd.read_sql("SELECT * FROM residents", conn)
        
        if not df.empty:
            search = st.text_input("🔍 ابحث بالاسم أو رقم الهوية")
            if search:
                df = df[df['name'].str.contains(search) | df['id_num'].str.contains(search)]
            
            st.dataframe(df, use_container_width=True)
            
            st.markdown("---")
            # خيارات التواصل والحذف
            target = st.selectbox("اختر اسماً للإجراء (مراسلة أو حذف):", [""] + df['name'].tolist())
            if target:
                selected_user = df[df['name'] == target].iloc[0]
                col_w, col_s, col_d = st.columns(3)
                
                # واتساب
                wa_msg = urllib.parse.quote(f"مرحباً {target}، مراجعة إدارة مخيم رفح السلام")
                col_w.markdown(f'<a href="wa.me{selected_user["phone"]}?text={wa_msg}" target="_blank"><button style="width:100%; background:#25D366; color:white; border:none; padding:10px; border-radius:5px;">واتساب</button></a>', unsafe_allow_html=True)
                
                # SMS
                col_s.markdown(f'<a href="sms:{selected_user["phone"]}?body={wa_msg}"><button style="width:100%; background:#007AFF; color:white; border:none; padding:10px; border-radius:5px;">رسالة SMS</button></a>', unsafe_allow_html=True)
                
                # حذف
                if col_d.button("🗑 حذف السجل"):
                    c.execute("DELETE FROM residents WHERE name=?", (target,))
                    conn.commit()
                    st.success("تم الحذف")
                    st.rerun()

            # تصدير Excel
            towrite = io.BytesIO()
            df.to_excel(towrite, index=False)
            st.download_button("📥 تحميل كافة البيانات Excel", towrite.getvalue(), "Camp_Data_2026.xlsx")
        else:
            st.warning("⚠️ لا توجد بيانات مسجلة حالياً. قاعدة البيانات فارغة.")
    else:
        st.error("🔒 عذراً، يجب تسجيل الدخول من القائمة الجانبية لرؤية البيانات.")

# حقوق الملكية الثابتة
st.markdown('<div class="footer">حقوق الملكية محفوظة باسم: ابوسفيان © 2026</div>', unsafe_allow_html=True)
