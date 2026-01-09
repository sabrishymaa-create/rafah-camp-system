import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# 1. إعدادات النظام والواجهة
st.set_page_config(page_title="مخيم رفح السلام", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #2E7D32; color: white; font-weight: bold; }
    .news-ticker { background: #b71c1c; color: white; padding: 12px; font-weight: bold; overflow: hidden; white-space: nowrap; border-radius: 8px; margin-bottom: 20px; }
    .ticker-text { display: inline-block; padding-right: 100%; animation: ticker 25s linear infinite; }
    @keyframes ticker { 0% { transform: translate(0, 0); } 100% { transform: translate(100%, 0); } }
    </style>
    """, unsafe_allow_html=True)

# 2. قاعدة البيانات (ربط الجداول ببعضها)
conn = sqlite3.connect('peace_camp_2026.db', check_same_thread=False)
c = conn.cursor()
# جدول رب الأسرة
c.execute('''CREATE TABLE IF NOT EXISTS residents (id_num TEXT PRIMARY KEY, name TEXT, phone TEXT, health TEXT, social TEXT)''')
# جدول أفراد العائلة (زوجات وأبناء) مرتبطين برقم هوية الأب
c.execute('''CREATE TABLE IF NOT EXISTS family (parent_id TEXT, member_name TEXT, member_id TEXT, dob TEXT, type TEXT, orphan TEXT, health TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
conn.commit()

c.execute("INSERT OR IGNORE INTO settings VALUES ('news', 'مرحباً بكم في مخيم رفح السلام - إدارة د. أكرم السدودي')")
conn.commit()

if 'wives_list' not in st.session_state: st.session_state.wives_list = []
if 'kids_list' not in st.session_state: st.session_state.kids_list = []
if 'is_admin' not in st.session_state: st.session_state.is_admin = False

# --- شريط الأخبار ---
c.execute("SELECT value FROM settings WHERE key='news'")
msg_news = c.fetchone()[0]
st.markdown(f'<div class="news-ticker"><div class="ticker-text">{msg_news}</div></div>', unsafe_allow_html=True)

st.title("🏥 منظومة مخيم رفح السلام")
st.markdown(f"#### بإشراف الدكتور أكرم السدودي | حقوق الملكية: ابوسفيان")

choice = st.selectbox("📌 القائمة الرئيسية:", ["📝 تسجيل نازح جديد", "🔐 لوحة التحكم الشاملة (Admin)"])

if choice == "📝 تسجيل نازح جديد":
    st.header("📋 استمارة البيانات")
    with st.container():
        col1, col2 = st.columns(2)
        full_name = col1.text_input("اسم رب الأسرة رباعي")
        id_num = col2.text_input("رقم هوية رب الأسرة")
        phone = col1.text_input("رقم الجوال")
        health_opts = ["سليم", "مزمن", "اعاقة حركية", "اعاقة سمعية", "اعاقة بصرية"]
        health = col2.selectbox("الحالة الصحية لرب الأسرة", health_opts)
        social_opts = ["متزوج/ة", "مطلق/ه", "ارمل/ه", "منفصل", "مهجور/ه", "شهيد"]
        social = col1.selectbox("الحالة الاجتماعية", social_opts)

        st.divider()
        st.subheader("💍 الزوجات")
        if st.button("➕ أضف زوجة"): st.session_state.wives_list.append("")
        for i, _ in enumerate(st.session_state.wives_list):
            st.session_state.wives_list[i] = st.text_input(f"اسم وهوية الزوجة {i+1}", key=f"w_{i}")

        st.subheader("👶 الأبناء")
        if st.button("➕ أضف ابن"): st.session_state.kids_list.append({"n":"", "i":"", "d":"", "h":"سليم", "o":"ليس يتيم"})
        for i, _ in enumerate(st.session_state.kids_list):
            k1, k2, k3, k4 = st.columns(4)
            st.session_state.kids_list[i]['n'] = k1.text_input(f"اسم الابن {i+1}", key=f"kn_{i}")
            st.session_state.kids_list[i]['i'] = k2.text_input(f"هوية {i+1}", key=f"ki_{i}")
            st.session_state.kids_list[i]['h'] = k3.selectbox(f"صحة {i+1}", health_opts, key=f"kh_{i}")
            st.session_state.kids_list[i]['o'] = k4.selectbox(f"يتم {i+1}", ["ليس يتيم", "يتيم الأب", "يتيم الأم", "كلاهما"], key=f"ko_{i}")

        if st.button("💾 حفظ البيانات"):
            if full_name and id_num:
                c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?)", (id_num, full_name, phone, health, social))
                for w in st.session_state.wives_list:
                    if w: c.execute("INSERT INTO family VALUES (?,?,'','','زوجة','','')", (id_num, w))
                for k in st.session_state.kids_list:
                    if k['n']: c.execute("INSERT INTO family VALUES (?,?,?,?,'ابن',?,?)", (id_num, k['n'], k['i'], "", k['o'], k['h']))
                conn.commit()
                st.success("✅ تم الحفظ بنجاح!")
                st.session_state.wives_list, st.session_state.kids_list = [], []
            else: st.error("⚠️ أدخل الاسم والهوية")

elif choice == "🔐 لوحة التحكم الشاملة (Admin)":
    if not st.session_state.is_admin:
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if u == "admin" and p == "admin123":
                st.session_state.is_admin = True
                st.rerun()
            else: st.error("خطأ")
    else:
        st.header("🛠 لوحة الإدارة - د. أكرم السدودي")
        if st.button("🔓 خروج"): st.session_state.is_admin = False; st.rerun()

        # الفرز المتقدم
        st.subheader("🔍 البحث والفرز المتقدم")
        df_res = pd.read_sql("SELECT * FROM residents", conn)
        df_fam = pd.read_sql("SELECT * FROM family", conn)
        
        filter_type = st.selectbox("فرز حسب الحالة:", ["الكل", "اعاقة", "يتيم", "ارمل/ه", "شهيد"])
        
        # عرض البيانات المدمجة
        if not df_res.empty:
            st.write("📊 قائمة النازحين والعائلات:")
            for index, row in df_res.iterrows():
                with st.expander(f"👤 {row['name']} (هوية: {row['id_num']}) - {row['social']}"):
                    st.write(f"📞 الجوال: {row['phone']} | 🏥 الصحة: {row['health']}")
                    family_members = df_fam[df_fam['parent_id'] == row['id_num']]
                    if not family_members.empty:
                        st.table(family_members[['member_name', 'type', 'orphan', 'health_status']])
                    
                    col_del, col_wa = st.columns(2)
                    if col_del.button(f"🗑 حذف سجل {row['name']}", key=f"del_{row['id_num']}"):
                        c.execute("DELETE FROM residents WHERE id_num=?", (row['id_num'],))
                        c.execute("DELETE FROM family WHERE parent_id=?", (row['id_num'],))
                        conn.commit()
                        st.rerun()
                    col_wa.markdown(f"[💬 مراسلة واتساب](wa.me{row['phone']})")

        # تصدير Excel للكل
        if st.button("📥 تصدير كافة البيانات إلى Excel"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_res.to_excel(writer, sheet_name='الأسماء الرئيسية', index=False)
                df_fam.to_excel(writer, sheet_name='أفراد العائلات', index=False)
            st.download_button("تحميل الملف الآن", output.getvalue(), "Peace_Camp_Report.xlsx")

st.markdown("---")
st.write("© 2026 | حقوق الملكية: **ابوسفيان**")
