import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse

# 1. إعدادات الصفحة والواجهة
st.set_page_config(page_title="مخيم رفح السلام", layout="wide")

# تنسيق الواجهة وحقوق الملكية بالأسفل
st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #2E7D32; color: white; font-weight: bold; }
    .news-ticker { background: #b71c1c; color: white; padding: 10px; font-weight: bold; overflow: hidden; border-radius: 5px; margin-bottom: 20px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f1f1f1; color: black; text-align: center; padding: 10px; font-weight: bold; border-top: 2px solid #2E7D32; z-index: 100; }
    /* أزرار التواصل في لوحة التحكم */
    .btn-whatsapp { background-color: #25D366; color: white; padding: 8px; border-radius: 5px; text-decoration: none; display: inline-block; width: 100%; text-align: center; margin-bottom: 5px; font-size: 14px; }
    .btn-sms { background-color: #007AFF; color: white; padding: 8px; border-radius: 5px; text-decoration: none; display: inline-block; width: 100%; text-align: center; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# 2. قاعدة البيانات
conn = sqlite3.connect('camp_final_2026_v1.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS residents (id_num TEXT PRIMARY KEY, name TEXT, phone TEXT, health TEXT, social TEXT, wives TEXT, kids TEXT)''')
conn.commit()

# 3. شريط الأخبار
st.markdown('<div class="news-ticker"><marquee direction="right">مرحباً بكم في مخيم رفح السلام - بإدارة د. أكرم السدودي - يرجى تسجيل البيانات بدقة لضمان الخدمة.</marquee></div>', unsafe_allow_html=True)

st.title("🏥 مخيم رفح السلام")
st.subheader("إدارة الدكتور أكرم السدودي")

choice = st.selectbox("📌 اختر الصفحة:", ["📝 تسجيل نازح جديد", "🔐 لوحة تحكم الإدارة (Admin)"])

if choice == "📝 تسجيل نازح جديد":
    st.header("📋 استمارة تسجيل البيانات")
    with st.form("main_form"):
        col1, col2 = st.columns(2)
        name = col1.text_input("الاسم الرباعي الكامل")
        id_num = col2.text_input("رقم الهوية")
        phone = col1.text_input("رقم الجوال")
        health = col2.selectbox("الحالة الصحية", ["سليم", "مزمن", "اعاقة حركية", "اعاقة سمعية", "اعاقة بصرية"])
        social = col1.selectbox("الحالة الاجتماعية", ["متزوج/ة", "مطلق/ه", "ارمل/ه", "منفصل", "مهجور/ه"])
        
        st.subheader("👨‍👩‍👧‍👦 بيانات العائلة")
        wives = st.text_area("بيانات الزوجات (الاسم ورقم الهوية)")
        kids = st.text_area("بيانات الأبناء (الاسم، الهوية، تاريخ الميلاد، الحالة الصحية، اليتم)")
        
        if st.form_submit_button("💾 حفظ البيانات"):
            if name and id_num:
                c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?,?)", (id_num, name, phone, health, social, wives, kids))
                conn.commit()
                st.success(f"✅ تم حفظ بيانات {name} بنجاح!")
            else: st.error("⚠️ يرجى إدخال الاسم ورقم الهوية")

elif choice == "🔐 لوحة تحكم الإدارة (Admin)":
    st.sidebar.header("تسجيل الدخول")
    user = st.sidebar.text_input("اسم المستخدم")
    pw = st.sidebar.text_input("كلمة المرور", type="password")
    
    if user == "admin" and pw == "admin123":
        st.header("🛠 لوحة الإدارة المركزية - د. أكرم السدودي")
        
        # جلب البيانات من القاعدة
        df = pd.read_sql("SELECT * FROM residents", conn)
        
        # إحصائيات سريعة في الأعلى
        col_stat1, col_stat2 = st.columns(2)
        col_stat1.metric("إجمالي المسجلين", len(df))
        col_stat2.metric("عدد الحالات الصحية/الإعاقة", len(df[df['health'] != 'سليم']))

        st.divider()
        
        # البحث والفرز
        search = st.text_input("🔍 ابحث عن اسم أو رقم هوية (Search Name or ID)")
        if search:
            df = df[df['name'].str.contains(search) | df['id_num'].str.contains(search)]
        
        # عرض الجدول بشكل واضح وكامل
        st.subheader("📄 قائمة الأسماء والبيانات")
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("📱 خيارات التواصل والتحكم بالأسماء")
        
        # اختيار اسم محدد لإجراء عمليات عليه
        target = st.selectbox("اختر اسماً من القائمة أعلاه (للمراسلة أو الحذف):", [""] + df['name'].tolist())
        
        if target:
            selected_row = df[df['name'] == target].iloc[0]
            phone_num = selected_row['phone']
            msg = urllib.parse.quote(f"مرحباً {target}، يرجى مراجعة إدارة مخيم رفح السلام.")
            
            col_msg, col_del = st.columns(2)
            
            with col_msg:
                st.info(f"إجراءات التواصل مع: {target}")
                # زر واتساب
                st.markdown(f'<a href="wa.me{phone_num}?text={msg}" class="btn-whatsapp" target="_blank">📲 ارسال WhatsApp</a>', unsafe_allow_html=True)
                # زر رسالة نصية SMS
                st.markdown(f'<a href="sms:{phone_num}?body={msg}" class="btn-sms">✉️ ارسال رسالة SMS</a>', unsafe_allow_html=True)
            
            with col_del:
                st.warning("إجراءات الحذف")
                if st.button("🗑 حذف هذا الاسم نهائياً"):
                    c.execute("DELETE FROM residents WHERE name=?", (target,))
                    conn.commit()
                    st.success("تم الحذف بنجاح!")
                    st.rerun()

        st.divider()
        # زر تحميل الإكسل بناءً على البحث الحالي
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False)
        st.download_button("📥 تحميل النتائج الحالية كملف Excel", towrite.getvalue(), "Camp_Report_2026.xlsx")
    else:
        st.warning("الرجاء إدخال بيانات الإدارة (admin / admin123) في القائمة الجانبية")

# حقوق الملكية ثابتة بالأسفل
st.markdown('<div class="footer">حقوق الملكية محفوظة باسم: ابوسفيان © 2026</div>', unsafe_allow_html=True)
