import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# إعدادات الصفحة لدعم العربية والجوال
st.set_page_config(page_title="مخيم رفح السلام", layout="wide")

# تصميم واجهة تدعم اليمين إلى اليسار (RTL)
st.markdown("""
    <style>
    body { direction: rtl; text-align: right; }
    div.stButton > button { width: 100%; border-radius: 5px; background-color: #007bff; color: white; }
    .stTextInput input { text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('rafah_camp_2026.db', check_same_thread=False)
c = conn.cursor()

# إنشاء الجداول
c.execute('''CREATE TABLE IF NOT EXISTS residents (
    id_num TEXT PRIMARY KEY, full_name TEXT, phone TEXT, health TEXT, 
    dis_type TEXT, social TEXT, status TEXT DEFAULT 'قيد الانتظار')''')

c.execute('''CREATE TABLE IF NOT EXISTS family (
    id SERIAL PRIMARY KEY, parent_id TEXT, member_name TEXT, member_id TEXT, 
    birth_date TEXT, age INTEGER, type TEXT, orphan_status TEXT, health_status TEXT)''')
conn.commit()

# --- إدارة حالة الجلسة للأزرار الديناميكية (+) ---
if 'wives' not in st.session_state: st.session_state.wives = []
if 'children' not in st.session_state: st.session_state.children = []

def add_wife(): st.session_state.wives.append({'name': '', 'id': ''})
def add_child(): st.session_state.children.append({'name': '', 'id': '', 'dob': datetime.now(), 'health': 'سليم', 'orphan': 'لا'})

# --- الواجهة الرئيسية ---
st.title("🏥 منظومة مخيم رفح السلام")
st.subheader("إدارة الدكتور أكرم السدودي")
st.write(f"📅 {datetime.now().strftime('%Y-%m-%d')} | 🕒 {datetime.now().strftime('%H:%M:%S')}")

menu = ["🏠 الرئيسية", "📝 تسجيل البيانات", "🔐 لوحة تحكم الإدارة"]
choice = st.sidebar.selectbox("القائمة", menu)

if choice == "📝 تسجيل البيانات":
    st.header("📋 استمارة تسجيل نازح")
    
    with st.expander("👤 البيانات الشخصية", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        f1 = col1.text_input("الاسم الأول")
        f2 = col2.text_input("الثاني")
        f3 = col3.text_input("الثالث")
        f4 = col4.text_input("الرابع")
        full_name = f"{f1} {f2} {f3} {f4}"
        
        id_num = st.text_input("رقم الهوية")
        phone = st.text_input("رقم الجوال")
        
        health = st.selectbox("الحالة الصحية", ["سليم", "مزمن", "اعاقة"])
        dis_type = st.text_input("نوع الاعاقة") if health == "اعاقة" else ""
        
        social = st.selectbox("الحالة الاجتماعية", ["متزوج", "متعدد الزوجات", "مطلق/ه", "ارمل/ه", "اعزب"])

    with st.expander("💍 بيانات الزوجات"):
        st.button("➕ إضافة زوجة", on_click=add_wife)
        for i, wife in enumerate(st.session_state.wives):
            c1, c2 = st.columns(2)
            wife['name'] = c1.text_input(f"اسم الزوجة {i+1}", key=f"wname_{i}")
            wife['id'] = c2.text_input(f"هوية الزوجة {i+1}", key=f"wid_{i}")

    with st.expander("👶 بيانات الأبناء"):
        st.button("➕ إضافة ابن/ابنة", on_click=add_child)
        for i, child in enumerate(st.session_state.children):
            c1, c2, c3, c4, c5 = st.columns(5)
            child['name'] = c1.text_input("الاسم رباعي", key=f"cname_{i}")
            child['id'] = c2.text_input("رقم الهوية", key=f"cid_{i}")
            child['dob'] = c3.date_input("تاريخ الميلاد", key=f"cdob_{i}")
            child['orphan'] = c4.selectbox("يتيم؟", ["لا", "يتيم الأب", "يتيم الأم", "كلاهما"], key=f"corph_{i}")
            child['health'] = c5.text_input("الحالة الصحية", key=f"chealth_{i}")

    if st.button("💾 حفظ وإرسال الطلب"):
        # حفظ البيانات الأساسية
        c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?,?)", 
                  (id_num, full_name, phone, health, dis_type, social, 'قيد الانتظار'))
        # حفظ الأبناء (مثال)
        for child in st.session_state.children:
            age = datetime.now().year - child['dob'].year
            c.execute("INSERT INTO family (parent_id, member_name, member_id, birth_date, age, type, orphan_status, health_status) VALUES (?,?,?,?,?,?,?,?)",
                      (id_num, child['name'], child['id'], str(child['dob']), age, 'ابن', child['orphan'], child['health']))
        conn.commit()
        st.success("تم الحفظ بنجاح!")

elif choice == "🔐 لوحة تحكم الإدارة":
    admin_id = st.sidebar.text_input("رقم الهوية")
    admin_pw = st.sidebar.text_input("كلمة المرور", type='password')
    
    if admin_id == "803256551" and admin_pw == "12345":
        st.header("🛠 لوحة التحكم - د. أكرم السدودي")
        
        # الفرز المتقدم
        st.subheader("🔍 الفرز والبحث")
        filter_opt = st.multiselect("فرز حسب:", ["اعاقة", "ارمل/ه", "مطلق/ه", "مزمن", "يتيم"])
        
        df = pd.read_sql("SELECT * FROM residents", conn)
        st.dataframe(df)

        # أزرار الإجراءات
        target = st.selectbox("اختر اسم لإجراء عملية:", df['full_name'].tolist() if not df.empty else [])
        col_act1, col_act2, col_act3 = st.columns(3)
        
        if col_act1.button("🗑 حذف السجل"):
            c.execute("DELETE FROM residents WHERE full_name=?", (target,))
            conn.commit()
            st.rerun()
            
        if col_act2.button("📱 رسالة WhatsApp"):
            user_phone = df[df['full_name'] == target]['phone'].values[0]
            st.markdown(f"[فتح واتساب](wa.me{user_phone}?text=مرحباً%20بكم%20من%20مخيم%20رفح%20السلام)")

        # تصدير إكسل
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 تصدير الكل إلى Excel", buffer.getvalue(), "camp_report.xlsx")

st.sidebar.markdown("---")
st.sidebar.write("حقوق الملكية: **ابوسفيان**")
