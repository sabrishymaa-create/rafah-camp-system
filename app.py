import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# إعدادات الصفحة
st.set_page_config(page_title="مخيم رفح السلام", layout="wide")

# دالة للاتصال بقاعدة البيانات
def get_connection():
    conn = sqlite3.connect('camp_system.db', check_same_thread=False)
    return conn

conn = get_connection()
c = conn.cursor()

# إنشاء الجداول (المستخدمين، الأبناء، الزوجات)
c.execute('''CREATE TABLE IF NOT EXISTS residents (
    id_num TEXT PRIMARY KEY, fname TEXT, sname TEXT, tname TEXT, lname TEXT,
    phone TEXT, health TEXT, dis_type TEXT, social TEXT, status TEXT DEFAULT 'قيد الانتظار')''')

c.execute('''CREATE TABLE IF NOT EXISTS family (
    parent_id TEXT, member_type TEXT, name TEXT, id_num TEXT, birth_date TEXT, age TEXT, health TEXT, orphan TEXT)''')
conn.commit()

# --- واجهة التطبيق ---
st.markdown("""<style> div.stButton > button { width: 100%; border-radius: 10px; } .stTextInput>div>div>input { text-align: right; } </style>""", unsafe_allow_html=True)

st.title("🏥 منظومة مخيم رفح السلام")
st.write(f"إدارة الدكتور أكرم السدودي | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

menu = ["🏠 الرئيسية", "📝 تسجيل جديد", "🔐 لوحة تحكم الإدارة"]
choice = st.sidebar.selectbox("القائمة", menu)

if choice == "📝 تسجيل جديد":
    st.header("إدخال بيانات النازح")
    with st.form("main_form"):
        col1, col2, col3, col4 = st.columns(4)
        fn = col1.text_input("الاسم الأول")
        sn = col2.text_input("الثاني")
        tn = col3.text_input("الثالث")
        ln = col4.text_input("الرابع")
        
        id_num = st.text_input("رقم الهوية")
        phone = st.text_input("رقم الجوال")
        
        health = st.selectbox("الحالة الصحية", ["سليم", "مزمن", "اعاقة"])
        dis_info = st.text_input("نوع الإعاقة (إن وجد)") if health == "اعاقة" else ""
        
        social = st.selectbox("الحالة الاجتماعية", ["اعزب", "متزوج", "متعدد الزوجات", "مطلق/ه", "ارمل/ه"])
        
        # إضافة الزوجات والأبناء (محاكاة الحقول الديناميكية)
        st.subheader("👨‍👩‍👧‍👦 بيانات العائلة")
        family_data = st.text_area("أدخل أسماء الأبناء وهوياتهم (اسم - هوية - تاريخ ميلاد)")
        
        submit = st.form_submit_button("إرسال للتدقيق")
        
        if submit:
            c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (id_num, fn, sn, tn, ln, phone, health, dis_info, social, 'قيد الانتظار'))
            conn.commit()
            st.success("تم إرسال طلبك بنجاح. بانتظار موافقة الإدارة.")

elif choice == "🔐 لوحة تحكم الإدارة":
    admin_id = st.sidebar.text_input("رقم هوية المسؤول")
    admin_pw = st.sidebar.text_input("كلمة المرور", type='password')
    
    if admin_id == "803256551" and admin_pw == "12345":
        st.header("🛠 لوحة تحكم الدكتور أكرم")
        
        # الفرز
        st.subheader("🔍 فرز البيانات")
        filter_type = st.selectbox("فرز حسب", ["الكل", "اعاقة", "ارمل/ه", "مطلق/ه", "مزمن"])
        
        query = "SELECT * FROM residents"
        if filter_type != "الكل":
            query += f" WHERE health='{filter_type}' OR social='{filter_type}'"
            
        df = pd.read_sql(query, conn)
        st.dataframe(df)

        # عمليات الإدارة (حذف وتعديل)
        target_id = st.text_input("أدخل رقم هوية العضو للإجراء (حذف أو قبول)")
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("✅ قبول الطلب"):
            c.execute("UPDATE residents SET status='مقبول' WHERE id_num=?", (target_id,))
            conn.commit()
            st.rerun()
        if col_btn2.button("🗑 حذف السجل"):
            c.execute("DELETE FROM residents WHERE id_num=?", (target_id,))
            conn.commit()
            st.rerun()

        # تصدير إكسل
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 تحميل النتائج Excel", buffer.getvalue(), "report.xlsx")

st.sidebar.markdown("---")
st.sidebar.write("حقوق الملكية: **ابوسفيان**")
