import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse

# 1. إعدادات الصفحة والتنسيق الاحترافي (CSS)
st.set_page_config(page_title="مخيم رفح السلام", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { border-radius: 12px; font-weight: bold; width: 100%; height: 3em; background-color: #1b5e20; color: white; border: none; transition: 0.3s; }
    .stButton>button:hover { background-color: #2e7d32; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
    .news-ticker { background: #b71c1c; color: white; padding: 12px; font-weight: bold; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background: #f8f9fa; text-align: center; padding: 10px; font-weight: bold; border-top: 3px solid #1b5e20; z-index: 1000; color: #333; }
    .main-header { background: linear-gradient(90deg, #1b5e20, #4caf50); color: white; padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# 2. قاعدة البيانات والجداول
conn = sqlite3.connect('rafah_camp_v2026_final.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS residents (id_num TEXT PRIMARY KEY, f1 TEXT, f2 TEXT, f3 TEXT, f4 TEXT, phone TEXT, health TEXT, social TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS family (p_id TEXT, type TEXT, name TEXT, id_num TEXT, dob TEXT, age TEXT, health TEXT, orphan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
c.execute("INSERT OR IGNORE INTO settings VALUES ('news', 'مرحباً بكم في منظومة مخيم رفح السلام الرقمية 2026 - بإدارة د. أكرم السدودي.')")
conn.commit()

# حالة الجلسة (Session State)
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'w_count' not in st.session_state: st.session_state.w_count = 1
if 'k_count' not in st.session_state: st.session_state.k_count = 1

# شريط الأخبار
news_msg = c.execute("SELECT value FROM settings WHERE key='news'").fetchone()[0]
st.markdown(f'<div class="news-ticker"><marquee direction="right">{news_msg}</marquee></div>', unsafe_allow_html=True)
st.markdown('<div class="main-header"><h1>🏥 منظومة مخيم رفح السلام الرقمية</h1><h3>إشراف د. أكرم السدودي</h3></div>', unsafe_allow_html=True)

# 3. نظام الإدارة (ADMIN PANEL)
col_top_r, col_top_l = st.columns([0.85, 0.15])
with col_top_l:
    if not st.session_state.logged_in:
        with st.popover("🔐 دخول الإدارة"):
            u = st.text_input("المستخدم")
            p = st.text_input("كلمة المرور", type="password")
            if st.button("تأكيد الدخول"):
                if u == "admin" and p == "123123": st.session_state.logged_in = True; st.rerun()
                else: st.error("بيانات خاطئة")
    else:
        if st.button("🚪 تسجيل الخروج"): st.session_state.logged_in = False; st.rerun()

if st.session_state.logged_in:
    st.header("🛠 لوحة التحكم والعمليات")
    tab1, tab2, tab3 = st.tabs(["📊 كشوفات النازحين", "➕ إضافة من الإدارة", "⚙️ الإعدادات"])
    
    with tab1:
        # جلب البيانات بتعريب الأعمدة
        df = pd.read_sql("SELECT id_num as 'الهوية', f1||' '||f2||' '||f3||' '||f4 as 'الاسم الكامل', phone as 'الجوال', status as 'الحالة', social as 'الاجتماعية' FROM residents", conn)
        search = st.text_input("🔍 بحث ذكي (بالاسم، الهوية، أو الحالة)")
        if search: df = df[df.apply(lambda r: search in str(r.values), axis=1)]
        st.dataframe(df, use_container_width=True)

        st.divider()
        st.subheader("⚙️ التحكم والعمليات على السجلات")
        sel_id = st.selectbox("اختر رقم هوية لإجراء (تعديل / قبول / حذف):", ["-- اختر الهوية --"] + list(df['الهوية']))
        
        if sel_id != "-- اختر الهوية --":
            res = c.execute("SELECT * FROM residents WHERE id_num=?", (sel_id,)).fetchone()
            with st.container(border=True):
                st.write(f"📝 تعديل بيانات السجل: **{res} {res}**")
                ce1, ce2, ce3 = st.columns(3)
                edit_f1 = ce1.text_input("تعديل الاسم الأول", value=res[1])
                edit_ph = ce2.text_input("تعديل رقم الجوال", value=res[5])
                edit_st = ce3.selectbox("تحديث الحالة", ["قيد الانتظار", "مقبول", "مرفوض"], index=["قيد الانتظار", "مقبول", "مرفوض"].index(res[8]))
                
                act1, act2, act3, act4 = st.columns(4)
                if act1.button("💾 حفظ التعديلات"):
                    c.execute("UPDATE residents SET f1=?, phone=?, status=? WHERE id_num=?", (edit_f1, edit_ph, edit_st, sel_id))
                    conn.commit(); st.success("✅ تم التحديث"); st.rerun()
                if act2.button("✅ قبول فوري"):
                    c.execute("UPDATE residents SET status='مقبول' WHERE id_num=?", (sel_id,))
                    conn.commit(); st.rerun()
                if act3.button("🗑️ حذف نهائي"):
                    c.execute("DELETE FROM residents WHERE id_num=?", (sel_id,))
                    c.execute("DELETE FROM family WHERE p_id=?", (sel_id,))
                    conn.commit(); st.warning("🗑️ تم الحذف"); st.rerun()
                
                # إرسال واتساب
                msg = urllib.parse.quote(f"مرحباً سيد {res[1]}, تم تحديث حالة طلبك في مخيم رفح السلام إلى: {edit_st}")
                act4.link_button("💬 واتساب", f"wa.me{res[5]}?text={msg}")
        
        # تصدير Excel
        buf = io.BytesIO()
        df.to_excel(buf, index=False); st.download_button("📥 تحميل الكشف بالكامل (Excel)", buf.getvalue(), "Rafah_Camp_2026.xlsx")

    with tab3:
        new_news = st.text_area("تعديل محتوى شريط الأخبار", news_msg)
        if st.button("تحديث الشريط"):
            c.execute("UPDATE settings SET value=? WHERE key='news'", (new_news,))
            conn.commit(); st.success("تم التحديث"); st.rerun()

# 4. واجهة تسجيل النازحين (USER INTERFACE)
else:
    st.header("📝 استمارة تسجيل نازح جديد")
    
    # أزرار الإضافة خارج الفورم (ضروري تقنياً)
    col_aw, col_ak = st.columns(2)
    with col_aw:
        if st.button("💍 إضافة زوجة أخرى (+)"): st.session_state.w_count += 1; st.rerun()
    with col_ak:
        if st.button("👶 إضافة ابن آخر (+)"): st.session_state.k_count += 1; st.rerun()

    with st.form("main_form"):
        st.subheader("👤 بيانات رب الأسرة")
        c1, c2, c3, c4 = st.columns(4)
        f1, f2, f3, f4 = c1.text_input("الاسم الأول"), c2.text_input("الثاني"), c3.text_input("الثالث"), c4.text_input("الرابع")
        id_num, phone = st.text_input("رقم الهوية الوطنية"), st.text_input("رقم الجوال")
        
        sh, ss = st.columns(2)
        health = sh.selectbox("الحالة الصحية", ["سليم", "مزمن", "إعاقة حركية", "إعاقة سمعية", "إعاقة بصرية"])
        social = ss.selectbox("الحالة الاجتماعية", ["متزوج", "أعزب", "أرمل", "مطلق", "مهجور", "منفصل"])

        # منطق الإخفاء: إخفاء الزوجة عند الحالات الخمس المحددة
        hide_wives_list = ["أعزب", "أرمل", "مطلق", "مهجور", "منفصل"]
        if social not in hide_wives_list:
            st.divider()
            st.subheader(f"💍 بيانات الزوجات ({st.session_state.w_count})")
            for i in range(st.session_state.w_count):
                wc1, wc2 = st.columns(2)
                wc1.text_input(f"اسم الزوجة {i+1} رباعي", key=f"wn_{i}")
                wc2.text_input(f"رقم هوية الزوجة {i+1}", key=f"wi_{i}")

        st.divider()
        st.subheader(f"👶 بيانات الأبناء ({st.session_state.k_count})")
        for j in range(st.session_state.k_count):
            st.write(f"**الابن/ة رقم {j+1}:**")
            k_row1 = st.columns(4)
            kn = k_row1.text_input("الاسم رباعي", key=f"kn_{j}")
            ki = k_row1.text_input("الهوية", key=f"ki_{j}")
            kd = k_row1.date_input("تاريخ الميلاد", value=datetime(2015,1,1), key=f"kd_{j}")
            # حساب العمر ديناميكياً لعام 2026
            age_calc = 2026 - kd.year
            k_row1.text_input("العمر", value=str(age_calc), disabled=True, key=f"ka_{j}")
            
            k_row2 = st.columns(2)
            k_health = k_row2.selectbox(f"الحالة الصحية", ["سليم", "مزمن", "إعاقة"], key=f"kh_{j}")
            k_orphan = k_row2.selectbox(f"خانة اليتم", ["ليس يتيم", "يتيم الأب", "يتيم الأم", "كلاهما"], key=f"ko_{j}")

        if st.form_submit_button("💾 حفظ البيانات وإرسال الطلب النهائي"):
            if f1 and id_num:
                try:
                    c.execute("INSERT OR REPLACE INTO residents VALUES (?,?,?,?,?,?,?,?,?)", (id_num, f1, f2, f3, f4, phone, health, social, "قيد الانتظار"))
                    for j in range(st.session_state.k_count):
                        if st.session_state.get(f"kn_{j}"):
                            c.execute("INSERT INTO family VALUES (?,?,?,?,?,?,?,?)", (id_num, 'ابن', st.session_state[f"kn_{j}"], st.session_state[f"ki_{j}"], str(st.session_state[f"kd_{j}"]), str(2026 - st.session_state[f"kd_{j}"].year), st.session_state[f"kh_{j}"], st.session_state[f"ko_{j}"]))
                    conn.commit()
                    st.success(f"✅ تم الحفظ بنجاح باسم د. أكرم السدودي. رقم طلبك هو هويتك: {id_num}")
                    st.session_state.w_count, st.session_state.k_count = 1, 1
                except Exception as e: st.error(f"خطأ في الحفظ: {e}")
            else: st.error("⚠️ يرجى إدخال الاسم الأول ورقم الهوية")

# حقوق الملكية الثابتة
st.markdown('<div class="footer">حقوق الملكية محفوظة باسم: ابوسفيان © 2026</div>', unsafe_allow_html=True)
