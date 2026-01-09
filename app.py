import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# 1. إعدادات الصفحة والتنسيق
st.set_page_config(page_title="إدارة مخيم رفح السلام", layout="wide")

st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; }
    .news-ticker { background: #b71c1c; color: white; padding: 10px; font-weight: bold; border-radius: 8px; margin-bottom: 20px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background: #f1f1f1; text-align: center; padding: 10px; font-weight: bold; border-top: 3px solid #1b5e20; z-index: 100; }
    .status-box { padding: 5px 10px; border-radius: 5px; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. قاعدة البيانات
conn = sqlite3.connect('rafah_camp_v2_2026.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS residents (id_num TEXT PRIMARY KEY, f1 TEXT, f2 TEXT, f3 TEXT, f4 TEXT, phone TEXT, health TEXT, social TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
c.execute("INSERT OR IGNORE INTO settings VALUES ('news', 'مرحباً بكم في مخيم رفح السلام  -  د. أكرم السدودي.')")
conn.commit()

# حالة الجلسة
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# شريط الأخبار
news_val = c.execute("SELECT value FROM settings WHERE key='news'").fetchone()[0]
st.markdown(f'<div class="news-ticker"><marquee direction="right">{news_val}</marquee></div>', unsafe_allow_html=True)

# الهيدر
st.title("🏥  مخيم رفح السلام")
st.write(" د. أكرم السدودي")

# قفل الإدارة
if not st.session_state.logged_in:
    with st.expander("🔐 تسجيل دخول الإدارة"):
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if u == "admin" and p == "123123":
                st.session_state.logged_in = True; st.rerun()
            else: st.error("بيانات خاطئة")

# 3. محتوى لوحة التحكم (عند تسجيل الدخول)
if st.session_state.logged_in:
    if st.button("🚪 تسجيل الخروج"): st.session_state.logged_in = False; st.rerun()
    
    st.header("🛠 لوحة الإدارة والتحكم")
    tab1, tab2, tab3 = st.tabs(["📊 عرض وإدارة النازحين", "➕ إضافة نازح جديد", "⚙️ الإعدادات العامة"])

    with tab1:
        st.subheader("🔍 البحث والتحكم في المسجلين")
        # جلب البيانات وتعريب الأعمدة
        df = pd.read_sql("SELECT id_num as 'رقم الهوية', f1 as 'الأول', f2 as 'الثاني', f3 as 'الثالث', f4 as 'الرابع', phone as 'الجوال', health as 'الحالة الصحية', social as 'الاجتماعية', status as 'حالة الطلب' FROM residents", conn)
        
        search = st.text_input("بحث بالاسم أو الهوية")
        if search:
            df = df[df.apply(lambda r: search in str(r.values), axis=1)]
        
        st.dataframe(df, use_container_width=True)

        st.divider()
        st.subheader("⚙️ إجراءات سريعة على الأسماء")
        
        # اختيار اسم للتحكم فيه
        list_of_names = pd.read_sql("SELECT id_num, f1, f4 FROM residents", conn)
        options = {f"{row['f1']} {row['f4']} ({row['id_num']})": row['id_num'] for index, row in list_of_names.iterrows()}
        
        selected_name = st.selectbox("اختر نازحاً لتعديل بياناته أو حالته:", ["-- اختر --"] + list(options.keys()))
        
        if selected_name != "-- اختر --":
            selected_id = options[selected_name]
            res_data = c.execute("SELECT * FROM residents WHERE id_num=?", (selected_id,)).fetchone()
            
            with st.container(border=True):
                st.write(f"📝 تعديل بيانات: **{selected_name}**")
                col_edit1, col_edit2 = st.columns(2)
                new_f1 = col_edit1.text_input("الاسم الأول الجديد", value=res_data[1])
                new_phone = col_edit2.text_input("رقم الجوال الجديد", value=res_data[5])
                
                # أزرار التحكم
                c1, c2, c3, c4 = st.columns(4)
                if c1.button("✅ قبول الطلب", type="primary"):
                    c.execute("UPDATE residents SET status='مقبول' WHERE id_num=?", (selected_id,))
                    conn.commit(); st.success("تم القبول"); st.rerun()
                
                if c2.button("❌ رفض الطلب"):
                    c.execute("UPDATE residents SET status='مرفوض' WHERE id_num=?", (selected_id,))
                    conn.commit(); st.warning("تم الرفض"); st.rerun()

                if c3.button("💾 حفظ التعديلات"):
                    c.execute("UPDATE residents SET f1=?, phone=? WHERE id_num=?", (new_f1, new_phone, selected_id))
                    conn.commit(); st.success("تم الحفظ"); st.rerun()

                if c4.button("🗑️ حذف نهائي"):
                    c.execute("DELETE FROM residents WHERE id_num=?", (selected_id,))
                    conn.commit(); st.error("تم الحذف"); st.rerun()

    with tab2:
        st.subheader("➕ إضافة نازح يدوياً من الإدارة")
        with st.form("admin_add_form"):
            ca1, ca2, ca3, ca4 = st.columns(4)
            af1, af2, af3, af4 = ca1.text_input("الأول"), ca2.text_input("الثاني"), ca3.text_input("الثالث"), ca4.text_input("الرابع")
            aid = st.text_input("رقم الهوية")
            aphon = st.text_input("الجوال")
            if st.form_submit_button("إضافة الآن"):
                if af1 and aid:
                    c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?,?,?,?)", 
                              (aid, af1, af2, af3, af4, aphon, "سليم", "متزوج", "مقبول (إدارة)"))
                    conn.commit(); st.success("تمت الإضافة بنجاح")
                else: st.error("أكمل البيانات")

    with tab3:
        st.subheader("📢 إدارة شريط الأخبار")
        new_txt = st.text_area("نص الشريط الحالي", value=news_val)
        if st.button("تحديث الشريط"):
            c.execute("UPDATE settings SET value=? WHERE key='news'", (new_txt,))
            conn.commit(); st.rerun()

# 4. واجهة المستخدم العادية (للتسجيل فقط)
else:
    st.info("👋 مرحباً بك في واجهة التسجيل. إذا كنت مديراً، يرجى تسجيل الدخول من الأعلى.")
    # (هنا تضع كود "استمارة تسجيل نازح جديد" الذي أرسلته لك سابقاً)
    # ملاحظة: تم إخفاء الاستمارة هنا للتركيز على لوحة التحكم المطلوبة.

st.markdown('<div class="footer">حقوق الملكية محفوظة باسم: ابوسفيان © 2026</div>', unsafe_allow_html=True)
