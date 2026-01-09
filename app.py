import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# 1. إعدادات الصفحة والتنسيق الجمالي
st.set_page_config(page_title="مخيم رفح السلام", layout="wide")

st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; background-color: #2E7D32; color: white; border: none; height: 3em; }
    .news-ticker { background: #b71c1c; color: white; padding: 10px; font-weight: bold; border-radius: 8px; margin-bottom: 20px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background: #f8f9fa; text-align: center; padding: 10px; font-weight: bold; border-top: 2px solid #2E7D32; z-index: 1000; color: #333; }
    .main-header { background: #1b5e20; color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. إنشاء وقاعدة البيانات والجداول
conn = sqlite3.connect('rafah_camp_final_2026.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS residents (id_num TEXT PRIMARY KEY, f1 TEXT, f2 TEXT, f3 TEXT, f4 TEXT, phone TEXT, health TEXT, social TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS family (p_id TEXT, type TEXT, name TEXT, id_num TEXT, dob TEXT, age TEXT, health TEXT, orphan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
c.execute("INSERT OR IGNORE INTO settings VALUES ('news', 'مرحباً بكم في منظومة مخيم رفح السلام الرقمية 2026 - بإدارة د. أكرم السدودي.')")
conn.commit()

# حالة الجلسة
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'w_count' not in st.session_state: st.session_state.w_count = 1
if 'k_count' not in st.session_state: st.session_state.k_count = 1

# شريط الأخبار
news_msg = c.execute("SELECT value FROM settings WHERE key='news'").fetchone()[0]
st.markdown(f'<div class="news-ticker"><marquee direction="right">{news_msg}</marquee></div>', unsafe_allow_html=True)

# الهيدر الرئيسي
st.markdown('<div class="main-header"><h1>🏥 مخيم رفح السلام</h1><h4>بإدارة د. أكرم السدودي</h4></div>', unsafe_allow_html=True)

# 3. نظام الإدارة (Admin)
col_a1, col_a2 = st.columns([0.8, 0.2])
with col_a2:
    if not st.session_state.logged_in:
        with st.popover("🔐 دخول الإدارة"):
            u = st.text_input("المستخدم")
            p = st.text_input("الكلمة", type="password")
            if st.button("دخول"):
                if u == "admin" and p == "123123":
                    st.session_state.logged_in = True; st.rerun()
                else: st.error("خطأ!")
    else:
        if st.button("🚪 خروج"): st.session_state.logged_in = False; st.rerun()

if st.session_state.logged_in:
    st.header("🛠 لوحة الإدارة والتحكم")
    tab1, tab2, tab3 = st.tabs(["📊 البيانات والفرز", "➕ إضافة يدوي", "⚙️ الإعدادات"])

    with tab1:
        df_res = pd.read_sql("SELECT id_num as 'الهوية', f1 as 'الأول', f2 as 'الثاني', f3 as 'الثالث', f4 as 'الرابع', phone as 'الجوال', health as 'الصحة', social as 'الاجتماعية', status as 'حالة الطلب' FROM residents", conn)
        search = st.text_input("🔍 بحث شامل بالاسم أو الهوية أو الحالة...")
        if search: df_res = df_res[df_res.apply(lambda r: search in str(r.values), axis=1)]
        st.dataframe(df_res, use_container_width=True)

        st.subheader("⚙️ إدارة الأسماء")
        all_res = c.execute("SELECT id_num, f1, f4 FROM residents").fetchall()
        options = {f"{r[1]} {r[2]} ({r[0]})": r[0] for r in all_res}
        choice = st.selectbox("اختر نازحاً للتحكم:", ["-- اختر --"] + list(options.keys()))
        
        if choice != "-- اختر --":
            target_id = options[choice]
            curr = c.execute("SELECT * FROM residents WHERE id_num=?", (target_id,)).fetchone()
            with st.container(border=True):
                col_e1, col_e2 = st.columns(2)
                new_f1 = col_e1.text_input("تعديل الاسم الأول", value=curr[1])
                new_phone = col_edit2 = col_e2.text_input("تعديل الجوال", value=curr[5])
                
                b1, b2, b3 = st.columns(3)
                if b1.button("✅ قبول"): c.execute("UPDATE residents SET status='مقبول' WHERE id_num=?", (target_id,)); conn.commit(); st.rerun()
                if b2.button("❌ رفض"): c.execute("UPDATE residents SET status='مرفوض' WHERE id_num=?", (target_id,)); conn.commit(); st.rerun()
                if b3.button("🗑️ حذف"): c.execute("DELETE FROM residents WHERE id_num=?", (target_id,)); conn.commit(); st.rerun()
        
        buffer = io.BytesIO()
        df_res.to_excel(buffer, index=False); st.download_button("📥 تصدير Excel", buffer.getvalue(), "Camp_2026.xlsx")

    with tab2:
        st.write("استخدم الاستمارة أدناه لإضافة نازح مباشرة من لوحة الإدارة.")

    with tab3:
        n_news = st.text_area("تعديل شريط الأخبار", news_msg)
        if st.button("حفظ"): c.execute("UPDATE settings SET value=? WHERE key='news'", (n_news,)); conn.commit(); st.rerun()

# 4. واجهة المستخدم (الاستمارة الكاملة)
else:
    with st.form("main_form"):
        st.subheader("👤 بيانات رب الأسرة")
        c1, c2, c3, c4 = st.columns(4)
        f1, f2, f3, f4 = c1.text_input("الاسم الأول"), c2.text_input("الثاني"), c3.text_input("الثالث"), c4.text_input("الرابع")
        id_num, phone = st.text_input("رقم الهوية"), st.text_input("رقم الجوال")
        
        ch, cs = st.columns(2)
        health = ch.selectbox("الحالة الصحية", ["سليم", "مزمن", "إعاقة حركية", "إعاقة سمعية", "إعاقة بصرية"])
        social = cs.selectbox("الحالة الاجتماعية", ["متزوج", "أرمل/ه", "مطلق/ه", "منفصل", "مهجور/ه"])
        
        # منطق إخفاء بيانات الزوجة
        if social == "متزوج":
            st.divider(); st.subheader("💍 بيانات الزوجة")
            st.info("لإضافة أكثر من زوجة، يرجى التنسيق مع الإدارة بعد التسجيل.")
            w_name, w_id = st.text_input("اسم الزوجة رباعي"), st.text_input("هوية الزوجة")
        
        st.divider(); st.subheader("👶 بيانات الأبناء")
        k_count_input = st.number_input("عدد الأبناء", min_value=0, max_value=20, value=1)
        
        for j in range(int(k_count_input)):
            st.markdown(f"**الابن {j+1}:**")
            k_col1, k_col2, k_col3, k_col4 = st.columns([3, 2, 2, 2])
            kn = k_col1.text_input("الاسم رباعي", key=f"kn_{j}")
            ki = k_col2.text_input("الهوية", key=f"ki_{j}")
            kd = k_col3.date_input("الميلاد", value=datetime(2015,1,1), key=f"kd_{j}")
            # حساب العمر
            age = datetime.now().year - kd.year
            k_col4.text_input("العمر", value=str(age), disabled=True, key=f"ka_{j}")
            
            k_col5, k_col6 = st.columns(2)
            kh = k_col5.selectbox("الصحة", ["سليم", "مزمن", "إعاقة"], key=f"kh_{j}")
            ko = k_col6.selectbox("اليتم", ["ليس يتيم", "يتيم الأب", "يتيم الأم", "كلاهما"], key=f"ko_{j}")

        if st.form_submit_button("💾 حفظ وإرسال البيانات"):
            if f1 and id_num:
                c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?,?,?,?)", (id_num, f1, f2, f3, f4, phone, health, social, "قيد الانتظار"))
                if social == "متزوج" and w_name:
                    c.execute("INSERT INTO family VALUES (?,?,?,?,?,?,?,?)", (id_num, 'زوجة', w_name, w_id, '', '', '', ''))
                for j in range(int(k_count_input)):
                    if st.session_state.get(f"kn_{j}"):
                        c.execute("INSERT INTO family VALUES (?,?,?,?,?,?,?,?)", (id_num, 'ابن', st.session_state.get(f"kn_{j}"), st.session_state.get(f"ki_{j}"), str(st.session_state.get(f"kd_{j}")), str(datetime.now().year - st.session_state.get(f"kd_{j}").year), st.session_state.get(f"kh_{j}"), st.session_state.get(f"ko_{j}")))
                conn.commit(); st.success("✅ تم التسجيل بنجاح.")
            else: st.error("أكمل البيانات الأساسية")

st.markdown('<div class="footer">حقوق الملكية محفوظة باسم: ابوسفيان © 2026</div>', unsafe_allow_html=True)
