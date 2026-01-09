import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse

# 1. إعدادات الصفحة والتنسيق المتطور
st.set_page_config(page_title="مخيم رفح السلام", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; height: 3em; background-color: #2E7D32; color: white; }
    .news-ticker { background: #b71c1c; color: white; padding: 10px; font-weight: bold; overflow: hidden; white-space: nowrap; border-radius: 8px; margin-bottom: 20px; border-right: 5px solid #ffeb3b; }
    .ticker-text { display: inline-block; padding-right: 100%; animation: ticker 30s linear infinite; }
    @keyframes ticker { 0% { transform: translate(0, 0); } 100% { transform: translate(100%, 0); } }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8f9fa; color: #333; text-align: center; padding: 10px; font-weight: bold; border-top: 2px solid #2E7D32; z-index: 1000; }
    .main-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# 2. قاعدة البيانات المتكاملة
conn = sqlite3.connect('rafah_camp_system_v2026_final.db', check_same_thread=False)
c = conn.cursor()
# جدول الآباء
c.execute('''CREATE TABLE IF NOT EXISTS residents (id_num TEXT PRIMARY KEY, f1 TEXT, f2 TEXT, f3 TEXT, f4 TEXT, phone TEXT, health TEXT, social TEXT, status TEXT)''')
# جدول الزوجات والأبناء
c.execute('''CREATE TABLE IF NOT EXISTS family (p_id TEXT, type TEXT, name TEXT, id_num TEXT, dob TEXT, age TEXT, health TEXT, orphan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
conn.commit()

c.execute("INSERT OR IGNORE INTO settings VALUES ('news', 'مرحباً بكم في منظومة مخيم رفح السلام الرقمية 2026 - بإدارة د. أكرم السدودي.')")
conn.commit()

# حالة الجلسة
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'show_login' not in st.session_state: st.session_state.show_login = False
if 'wives_count' not in st.session_state: st.session_state.wives_count = 1
if 'kids_count' not in st.session_state: st.session_state.kids_count = 1

# شريط الأخبار
c.execute("SELECT value FROM settings WHERE key='news'")
news_msg = c.fetchone()[0]
st.markdown(f'<div class="news-ticker"><div class="ticker-text">{news_msg}</div></div>', unsafe_allow_html=True)

# الهيدر وزر الدخول (أعلى اليسار)
h_col1, h_col2 = st.columns([0.8, 0.2])
with h_col1:
    st.title("🏥 مخيم رفح السلام")
    st.markdown(f"#### إدارة الدكتور أكرم السدودي")
with h_col2:
    if not st.session_state.logged_in:
        if st.button("🔐 دخول الإدارة"): st.session_state.show_login = not st.session_state.show_login
    else:
        if st.button("🚪 خروج الإدارة"): st.session_state.logged_in = False; st.rerun()

# واجهة الدخول
if st.session_state.show_login and not st.session_state.logged_in:
    l_col1, l_col2 = st.columns(2)
    u = l_col1.text_input("اسم المستخدم")
    p = l_col2.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u == "admin" and p == "123123":
            st.session_state.logged_in = True; st.session_state.show_login = False; st.rerun()
        else: st.error("❌ بيانات خاطئة")

# 3. المحتوى
if st.session_state.logged_in:
    st.header("🛠 لوحة تحكم د. أكرم السدودي الشاملة")
    tab1, tab2, tab3 = st.tabs(["📊 البيانات والفرز", "➕ إضافة طلب إداري", "⚙️ الإعدادات"])
    
    with tab1:
        # إحصائيات سريعة
        df_res = pd.read_sql("SELECT * FROM residents", conn)
        df_fam = pd.read_sql("SELECT * FROM family", conn)
        
        c_s1, c_s2, c_s3, c_s4 = st.columns(4)
        c_s1.metric("إجمالي العائلات", len(df_res))
        c_s2.metric("إجمالي الأبناء", len(df_fam[df_fam['type']=='ابن']))
        c_s3.metric("الأيتام", len(df_fam[df_fam['orphan']!='ليس يتيم']))
        c_s4.metric("الإعاقات", len(df_res[df_res['health']!='سليم']) + len(df_fam[df_fam['health']!='سليم']))

        st.subheader("🔍 البحث والفرز التفصيلي")
        f_col1, f_col2, f_col3 = st.columns(3)
        search = f_col1.text_input("ابحث بالاسم أو الهوية")
        f_health = f_col2.selectbox("فرز حسب الحالة الصحية", ["الكل", "سليم", "مزمن", "اعاقة حركية", "إعاقة سمعية", "إعاقة بصرية"])
        f_social = f_col3.selectbox("فرز حسب الحالة الاجتماعية", ["الكل", "متزوج", "مطلق/ه", "ارمل/ه", "شهيد", "مهجور/ه"])
        
        # تصفية البيانات
        df_display = df_res.copy()
        if search: df_display = df_display[df_display['f1'].str.contains(search) | df_display['id_num'].str.contains(search)]
        if f_health != "الكل": df_display = df_display[df_display['health'] == f_health]
        if f_social != "الكل": df_display = df_display[df_display['social'] == f_social]
        
        st.dataframe(df_display.rename(columns={'id_num':'الهوية','f1':'الأول','f4':'الرابع','phone':'الجوال','status':'الحالة'}), use_container_width=True)

        st.divider()
        target = st.selectbox("اختر نازحاً لمراجعة ملفه الكامل أو تعديله:", [""] + df_display['id_num'].tolist())
        if target:
            res_row = df_res[df_res['id_num'] == target].iloc[0]
            st.markdown(f"### ملف تعريف: {res_row['f1']} {res_row['f4']}")
            
            with st.form("edit_form"):
                e_col1, e_col2, e_col3 = st.columns(3)
                en1 = e_col1.text_input("تعديل الاسم الأول", value=res_row['f1'])
                eph = e_col2.text_input("تعديل الجوال", value=res_row['phone'])
                est = e_col3.selectbox("تحديث الحالة", ["⏳ قيد الانتظار", "✅ مقبول", "❌ مرفوض"], index=0)
                
                # عرض الزوجات والأبناء داخل ملف التعريف
                fam_rows = df_fam[df_fam['p_id'] == target]
                st.write("👨‍👩‍👧‍👦 أفراد العائلة المضافين:")
                st.table(fam_rows[['name', 'id_num', 'type', 'age', 'health', 'orphan']])
                
                c_up, c_del = st.columns(2)
                if c_up.form_submit_button("💾 حفظ التعديلات"):
                    c.execute("UPDATE residents SET f1=?, phone=?, status=? WHERE id_num=?", (en1, eph, est, target))
                    conn.commit(); st.rerun()
                if c_del.form_submit_button("🗑 حذف السجل نهائياً"):
                    c.execute("DELETE FROM residents WHERE id_num=?", (target,))
                    c.execute("DELETE FROM family WHERE p_id=?", (target,))
                    conn.commit(); st.rerun()
            
            # مراسلة
            wa_msg = urllib.parse.quote(f"مرحباً {res_row['f1']}، يرجى مراجعة إدارة مخيم رفح السلام.")
            st.markdown(f'<a href="wa.me{res_row["phone"]}?text={wa_msg}" target="_blank"><button style="background:#25D366; color:white; border:none; padding:12px; border-radius:8px; width:100%;">💬 مراسلة WhatsApp</button></a>', unsafe_allow_html=True)

        # تصدير Excel
        buffer = io.BytesIO()
        df_display.to_excel(buffer, index=False)
        st.download_button("📥 تصدير نتائج البحث الحالية Excel", buffer.getvalue(), "Camp_Filtered_Report.xlsx")

else:
    # --- واجهة تسجيل النازحين (الاستمارة الكاملة) ---
    st.header("📝 استمارة تسجيل نازح جديد")
    with st.form("resident_form"):
        st.subheader("👤 بيانات رب الأسرة")
        col1, col2, col3, col4 = st.columns(4)
        f1, f2, f3, f4 = col1.text_input("الاسم الأول"), col2.text_input("الثاني"), col3.text_input("الثالث"), col4.text_input("الرابع")
        id_num, phone = st.text_input("رقم الهوية"), st.text_input("رقم الجوال")
        
        c_h, c_s = st.columns(2)
        health = c_h.selectbox("الحالة الصحية", ["سليم", "مزمن", "اعاقة حركية", "إعاقة سمعية", "إعاقة بصرية"])
        social = c_s.selectbox("الحالة الاجتماعية", ["متزوج", "مطلق/ه", "ارمل/ه", "منفصل", "مهجور/ه"])
        
        st.divider()
        st.subheader("💍 بيانات الزوجات")
        for i in range(st.session_state.wives_count):
            wc1, wc2 = st.columns(2)
            wc1.text_input(f"اسم الزوجة {i+1} رباعي", key=f"wname_{i}")
            wc2.text_input(f"هوية الزوجة {i+1}", key=f"wid_{i}")
        if st.form_submit_button("➕ إضافة زوجة أخرى"):
            st.session_state.wives_count += 1; st.rerun()

        st.divider()
        st.subheader("👶 بيانات الأبناء")
        for j in range(st.session_state.kids_count):
            kc1, kc2, kc3, kc4, kc5, kc6 = st.columns(6)
            kn = kc1.text_input(f"الاسم {j+1}", key=f"kn_{j}")
            ki = kc2.text_input(f"الهوية", key=f"ki_{j}")
            kd = kc3.date_input(f"الميلاد", key=f"kd_{j}")
            # حساب العمر ديناميكياً
            age = datetime.now().year - kd.year
            kc4.text_input(f"العمر", value=str(age), disabled=True, key=f"ka_{j}")
            kh = kc5.selectbox(f"الصحة", ["سليم", "مزمن", "اعاقة"], key=f"kh_{j}")
            ko = kc6.selectbox(f"اليتم", ["ليس يتيم", "يتيم الأب", "يتيم الأم", "كلاهما"], key=f"ko_{j}")
        if st.form_submit_button("➕ إضافة ابن آخر"):
            st.session_state.kids_count += 1; st.rerun()

        if st.form_submit_button("💾 حفظ البيانات وإرسال الطلب النهائي"):
            if f1 and id_num:
                c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?,?,?,?)", 
                          (id_num, f1, f2, f3, f4, phone, health, social, '⏳ قيد الانتظار'))
                # حفظ الأبناء والزوجات في جدول منفصل
                for i in range(st.session_state.wives_count):
                    wn = st.session_state.get(f"wname_{i}"); wi = st.session_state.get(f"wid_{i}")
                    if wn: c.execute("INSERT INTO family VALUES (?,?,?,?,?,?,?,?)", (id_num, 'زوجة', wn, wi, '', '', '', ''))
                for j in range(st.session_state.kids_count):
                    kn = st.session_state.get(f"kn_{j}"); ki = st.session_state.get(f"ki_{j}")
                    kd = st.session_state.get(f"kd_{j}"); kh = st.session_state.get(f"kh_{j}")
                    ko = st.session_state.get(f"ko_{j}")
                    age = datetime.now().year - kd.year
                    if kn: c.execute("INSERT INTO family VALUES (?,?,?,?,?,?,?,?)", (id_num, 'ابن', kn, ki, str(kd), str(age), kh, ko))
                
                conn.commit(); st.success("✅ تم حفظ عائلتك بنجاح وبانتظار موافقة د. أكرم.")
                st.session_state.wives_count = 1; st.session_state.kids_count = 1
            else: st.error("⚠️ الاسم الأول والهوية مطلوبان")

# حقوق الملكية الثابتة
st.markdown('<div class="footer">حقوق الملكية محفوظة باسم: ابوسفيان © 2026</div>', unsafe_allow_html=True)
