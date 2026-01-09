import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib

# إعدادات الصفحة (متوافقة مع الهاتف)
st.set_page_config(page_title="مخيم رفح السلام", layout="wide")

# حقوق الملكية
ST_FOOTER = "جميع الحقوق محفوظة باسم ابوسفيان © 2026"

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('camp_data.db', check_same_thread=False)
c = conn.cursor()

# إنشاء الجداول إذا لم تكن موجودة
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (id_num TEXT PRIMARY KEY, name TEXT, phone TEXT, health TEXT, disability_type TEXT, 
              social_status TEXT, secret_ans1 TEXT, secret_ans2 TEXT, role TEXT, password TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS family_members 
             (parent_id TEXT, member_name TEXT, member_id TEXT, birth_date TEXT, 
              age INTEGER, is_orphan TEXT, health_status TEXT, relation TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS news (content TEXT, date TEXT)''')
conn.commit()

# دالة تشفير كلمة المرور
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# إضافة الإدمن الافتراضي (د. أكرم السدودي)
admin_id = "803256551"
admin_pw = make_hashes("12345")
c.execute("INSERT OR IGNORE INTO users (id_num, role, password) VALUES (?, ?, ?)", (admin_id, 'admin', admin_pw))
conn.commit()

# --- واجهة المستخدم ---
st.title("🏥 مخيم رفح السلام")
st.subheader("إدارة الدكتور أكرم السدودي")
st.write(f"📅 {datetime.now().strftime('%Y-%m-%d')} | 🕒 {datetime.now().strftime('%H:%M:%S')}")

menu = ["تسجيل الدخول", "تسجيل جديد (للنازحين)"]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

if choice == "تسجيل جديد (للنازحين)":
    st.header("📝 استمارة تسجيل البيانات")
    
    with st.form("reg_form"):
        col1, col2, col3, col4 = st.columns(4)
        fname = col1.text_input("الاسم الأول")
        sname = col2.text_input("الاسم الثاني")
        tname = col3.text_input("الاسم الثالث")
        lname = col4.text_input("الاسم الرابع")
        
        id_num = st.text_input("رقم الهوية")
        phone = st.text_input("رقم الجوال")
        
        health = st.selectbox("الحالة الصحية", ["سليم", "مزمن", "اعاقة"])
        dis_type = ""
        if health == "اعاقة":
            dis_type = st.text_input("نوع الاعاقة")
            
        social = st.selectbox("الحالة الاجتماعية", ["اعزب", "متزوج", "متعدد الزوجات", "مطلق/ه", "ارمل/ه"])
        
        st.info("أسئلة الأمان (للدخول لاحقاً)")
        q1 = st.text_input("تاريخ ميلادك (مثلاً 1990)")
        q2 = st.text_input("اسم طفلك الأول (أو أي كلمة سر خاصة)")
        
        submit = st.form_submit_button("حفظ البيانات")
        
        if submit:
            full_name = f"{fname} {sname} {tname} {lname}"
            try:
                c.execute("INSERT INTO users (id_num, name, phone, health, disability_type, social_status, secret_ans1, secret_ans2, role) VALUES (?,?,?,?,?,?,?,?,?)",
                          (id_num, full_name, phone, health, dis_type, social, q1, q2, 'user'))
                conn.commit()
                st.success("تم تسجيل بياناتك بنجاح!")
            except:
                st.error("رقم الهوية مسجل مسبقاً")

elif choice == "تسجيل الدخول":
    st.sidebar.header("لوحة الدخول")
    login_id = st.sidebar.text_input("رقم الهوية")
    login_pw = st.sidebar.text_input("كلمة المرور (للإدارة فقط)", type='password')
    
    # أسئلة الأمان للمستخدمين العاديين
    s_ans1 = st.sidebar.text_input("سؤال الأمان 1 (تاريخ الميلاد)")
    s_ans2 = st.sidebar.text_input("سؤال الأمان 2 (الاسم الخاص)")

    if st.sidebar.button("دخول"):
        # فحص إذا كان أدمن
        if login_id == admin_id and make_hashes(login_pw) == admin_pw:
            st.session_state['role'] = 'admin'
            st.success("مرحباً د. أكرم السدودي")
        else:
            # فحص مستخدم عادي
            c.execute("SELECT * FROM users WHERE id_num=? AND secret_ans1=? AND secret_ans2=?", (login_id, s_ans1, s_ans2))
            if c.fetchone():
                st.session_state['role'] = 'user'
                st.session_state['user_id'] = login_id
                st.success("تم الدخول بنجاح")
            else:
                st.error("بيانات الدخول غير صحيحة")

    # --- لوحة تحكم الإدارة ---
    if 'role' in st.session_state and st.session_state['role'] == 'admin':
        st.header("🛠 لوحة تحكم المسؤول")
        
        # عرض البيانات والفرز
        data = pd.read_sql("SELECT * FROM users WHERE role='user'", conn)
        
        st.subheader("📊 فرز وتصدير البيانات")
        filter_col = st.multiselect("فرز حسب:", ["سليم", "مزمن", "اعاقة", "ارمل/ه", "مطلق/ه"])
        
        if filter_col:
            filtered_df = data[data['health'].isin(filter_col) | data['social_status'].isin(filter_col)]
        else:
            filtered_df = data

        st.dataframe(filtered_df)
        
        # تصدير إكسل
        if st.button("تصدير النتائج إلى Excel"):
            filtered_df.to_excel("search_results.xlsx", index=False)
            st.success("تم حفظ الملف باسم search_results.xlsx")

        # إدارة الأخبار
        st.subheader("📢 شريط الأخبار")
        new_post = st.text_area("أضف خبراً جديداً")
        if st.button("نشر"):
            c.execute("INSERT INTO news VALUES (?,?)", (new_post, datetime.now().date()))
            conn.commit()

st.markdown(f"<hr><center>{ST_FOOTER}</center>", unsafe_allow_html=True)
