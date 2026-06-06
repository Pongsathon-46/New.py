import streamlit as st
import json
import base64
import uuid
from datetime import date
from io import BytesIO

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Portfolio สหกิจศึกษา",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ────────────────────────────────────────────────
TOTAL_WEEKS = 39
MONTH_NAMES = ["มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.", "ม.ค.", "ก.พ."]

def week_to_month(week: int) -> str:
    return MONTH_NAMES[int(week // (TOTAL_WEEKS / 9))]

def week_label(week: int) -> str:
    return f"อาทิตย์ที่ {week + 1} — {week_to_month(week)}"

# ── Session state init ───────────────────────────────────────
def init_state():
    defaults = {
        "page": "home",
        "items": [],       # portfolio items
        "projects": [],    # coop project PDFs
        "profile": {
            "nameTH": "", "nameEN": "",
            "dept": "", "deptEN": "",
            "university": "", "universityEN": "",
            "company": "", "division": "",
            "bio": "", "photo": None,  # base64 string
        },
        "edit_item_id": None,
        "viewing_project_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Helpers ──────────────────────────────────────────────────
def file_to_b64(uploaded_file) -> str:
    return base64.b64encode(uploaded_file.read()).decode()

def b64_img_tag(b64: str, mime: str = "image/jpeg", style: str = "") -> str:
    return f'<img src="data:{mime};base64,{b64}" style="{style}">'

def display_pdf(b64_data: str):
    pdf_display = f"""
    <iframe
        src="data:application/pdf;base64,{b64_data}"
        width="100%" height="700px"
        style="border:none; border-radius:8px;">
    </iframe>"""
    st.markdown(pdf_display, unsafe_allow_html=True)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Sarabun', 'Noto Sans Thai', sans-serif !important;
}

/* Hide default streamlit header padding */
.block-container { padding-top: 1rem !important; }

/* Sidebar nav buttons */
.nav-btn {
    display: block; width: 100%; text-align: left;
    padding: 10px 14px; margin-bottom: 6px;
    border-radius: 10px; border: none; cursor: pointer;
    font-size: 15px; font-family: inherit;
    background: transparent; color: #1a1a18;
    transition: background 0.15s;
}
.nav-btn:hover { background: #E1F5EE; }
.nav-btn.active { background: #1D9E75; color: #fff; font-weight: 700; }

/* Cards */
.card {
    background: #fff; border-radius: 14px;
    border: 1px solid #E8E6DF; padding: 1.2rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-bottom: 14px;
}

/* Stat cards */
.stat-card {
    background: #fff; border-radius: 12px;
    border: 1px solid #E8E6DF; padding: 1rem;
    text-align: center;
}
.stat-num { font-size: 28px; font-weight: 700; color: #1a1a18; }
.stat-label { font-size: 12px; color: #888; }

/* Badge */
.badge {
    display: inline-block; border-radius: 6px;
    font-size: 11px; font-weight: 600;
    padding: 2px 8px; margin-right: 4px;
}
.badge-week  { background:#E1F5EE; color:#0F6E56; border:1px solid #5DCAA5; }
.badge-month { background:#F1EFE8; color:#5F5E5A; border:1px solid #B4B2A9; }
.badge-img   { background:#E1F5EE; color:#0F6E56; border:1px solid #5DCAA5; }
.badge-pdf   { background:#E6F1FB; color:#185FA5; border:1px solid #85B7EB; }
.badge-blog  { background:#FAEEDA; color:#854F0B; border:1px solid #EF9F27; }

/* Hero section */
.hero {
    background: linear-gradient(135deg, #0F6E56 0%, #085041 40%, #042C53 100%);
    border-radius: 16px; padding: 2.5rem; color: #fff;
    margin-bottom: 1.5rem;
}
.hero h1 { font-size: 2rem; margin: 0 0 4px; }
.hero h2 { font-size: 1.2rem; margin: 0 0 1.5rem; color: #9FE1CB; font-weight: 500; }
.info-row { display:flex; gap:12px; align-items:flex-start; margin-bottom:12px; }
.info-main { font-weight:600; font-size:14px; }
.info-sub  { font-size:12px; color:#9FE1CB; }

/* Timeline bar */
.tl-bar {
    display: inline-block;
    background: #1D9E75;
    border-radius: 3px;
    min-width: 8px;
    vertical-align: bottom;
}
.tl-bar-empty {
    display: inline-block;
    background: #E8E6DF;
    border-radius: 3px;
    width: 8px; height: 5px;
    vertical-align: bottom;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar navigation ───────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎓 Portfolio สหกิจศึกษา")
    st.caption("9 เดือน · 39 อาทิตย์")
    st.divider()

    pages = [
        ("🏠", "หน้าแรก",    "home"),
        ("📁", "พอร์ตโฟลิโอ", "portfolio"),
        ("📋", "โครงงาน",     "project"),
    ]
    for icon, label, pid in pages:
        active = "active" if st.session_state.page == pid else ""
        if st.button(f"{icon}  {label}", key=f"nav_{pid}",
                     use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.page = pid
            st.rerun()

    st.divider()
    st.caption("ข้อมูลทั้งหมดเก็บใน Session\n(รีเฟรชหน้าจะรีเซต)")

# ══════════════════════════════════════════════════════════════
#  PAGE: HOME
# ══════════════════════════════════════════════════════════════
if st.session_state.page == "home":
    p = st.session_state.profile

    # Hero block
    col_info, col_photo = st.columns([2, 1], gap="large")

    with col_info:
        st.markdown("""
        <div style="display:inline-flex;align-items:center;gap:8px;
                    background:rgba(15,110,86,0.12);border-radius:20px;
                    padding:6px 14px;margin-bottom:16px;
                    border:1px solid #5DCAA5;">
            <span>🎓</span><span style="font-size:13px;font-weight:500;color:#0F6E56">นักศึกษาสหกิจศึกษา</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"## {p['nameTH'] or 'ชื่อ-นามสกุล (ภาษาไทย)'}")
        st.markdown(f"**{p['nameEN'] or 'Name Surname'}**")

        for icon, main_key, sub_key, main_ph, sub_ph in [
            ("🏛️", "dept",       "deptEN",       "ภาควิชา / สาขาวิชา", "Department"),
            ("🎓", "university", "universityEN", "มหาวิทยาลัย",         "University"),
            ("🏢", "company",    "division",     "บริษัทที่ฝึกงาน",     "ฝ่าย / แผนก"),
        ]:
            main_val = p.get(main_key) or main_ph
            sub_val  = p.get(sub_key)  or sub_ph
            st.markdown(f"""
            <div class="info-row">
                <span style="font-size:18px">{icon}</span>
                <div>
                    <div class="info-main">{main_val}</div>
                    <div class="info-sub">{sub_val}</div>
                </div>
            </div>""", unsafe_allow_html=True)

        if p.get("bio"):
            st.markdown(f"*{p['bio']}*")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ดูพอร์ตโฟลิโอ →", type="primary", key="go_portfolio"):
            st.session_state.page = "portfolio"
            st.rerun()

    with col_photo:
        if p.get("photo"):
            st.markdown(
                f'<img src="data:image/jpeg;base64,{p["photo"]}" '
                f'style="width:100%;border-radius:16px;'
                f'border:3px solid #1D9E75;object-fit:cover;max-height:320px;">',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("""
            <div style="width:100%;height:260px;border-radius:16px;
                        border:2px dashed #5DCAA5;display:flex;
                        align-items:center;justify-content:center;
                        background:#F7F5F0;flex-direction:column;gap:8px;">
                <span style="font-size:40px">📷</span>
                <span style="font-size:13px;color:#888">อัปโหลดรูปด้านล่าง</span>
            </div>""", unsafe_allow_html=True)

        photo_file = st.file_uploader("อัปโหลดรูปโปรไฟล์", type=["jpg","jpeg","png"],
                                       key="photo_upload", label_visibility="collapsed")
        if photo_file:
            photo_file.seek(0)
            st.session_state.profile["photo"] = base64.b64encode(photo_file.read()).decode()
            st.rerun()

    st.divider()

    # Edit profile form
    with st.expander("✏️ แก้ไขข้อมูลส่วนตัว"):
        with st.form("profile_form"):
            c1, c2 = st.columns(2)
            with c1:
                nameTH      = st.text_input("ชื่อ-นามสกุล (ภาษาไทย)", value=p.get("nameTH",""), placeholder="นายพงศธร ปราสาทหินพิมาย")
                dept        = st.text_input("สาขาวิชา (ภาษาไทย)",      value=p.get("dept",""),   placeholder="ภาควิชาวิศวกรรมโยธา")
                university  = st.text_input("มหาวิทยาลัย (ภาษาไทย)",   value=p.get("university",""), placeholder="มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ")
                company     = st.text_input("บริษัทที่ฝึกงาน",           value=p.get("company",""),   placeholder="บริษัท NL Development จำกัด (มหาชน)")
            with c2:
                nameEN      = st.text_input("Name Surname (English)",    value=p.get("nameEN",""),      placeholder="Pongsathon Prasathinpimay")
                deptEN      = st.text_input("Department (English)",      value=p.get("deptEN",""),      placeholder="Department of Civil Engineering")
                universityEN= st.text_input("University (English)",      value=p.get("universityEN",""),placeholder="King Mongkut's University of Technology North Bangkok")
                division    = st.text_input("ฝ่าย / แผนก",              value=p.get("division",""),    placeholder="ฝ่ายพัฒนาโครงสร้างพื้นฐาน")
            bio = st.text_area("คำแนะนำตัว / Bio", value=p.get("bio",""), placeholder="แนะนำตัวเองและความสนใจ...", height=80)

            if st.form_submit_button("💾 บันทึกข้อมูล", type="primary"):
                st.session_state.profile.update({
                    "nameTH": nameTH, "nameEN": nameEN,
                    "dept": dept, "deptEN": deptEN,
                    "university": university, "universityEN": universityEN,
                    "company": company, "division": division, "bio": bio,
                })
                st.success("บันทึกข้อมูลเรียบร้อย!")
                st.rerun()

# ══════════════════════════════════════════════════════════════
#  PAGE: PORTFOLIO
# ══════════════════════════════════════════════════════════════
elif st.session_state.page == "portfolio":
    st.markdown("## 📁 พอร์ตโฟลิโอ")

    items = st.session_state.items

    # ── Stats ──────────────────────────────────────────────────
    weeks_with_work = len({it["week"] for it in items})
    img_count  = sum(1 for it in items for f in it["files"] if f["type"] == "รูปภาพ")
    pdf_count  = sum(1 for it in items for f in it["files"] if f["type"] == "PDF")

    c1,c2,c3,c4 = st.columns(4)
    for col, icon, val, label in [
        (c1,"📁", len(items),       "ผลงานทั้งหมด"),
        (c2,"📅", weeks_with_work,  "อาทิตย์ที่มีผลงาน"),
        (c3,"🖼️", img_count,        "รูปภาพ"),
        (c4,"📄", pdf_count,        "PDF / รายงาน"),
    ]:
        col.markdown(f"""
        <div class="stat-card">
            <div style="font-size:24px">{icon}</div>
            <div class="stat-num">{val}</div>
            <div class="stat-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Timeline ────────────────────────────────────────────────
    if items:
        week_counts = [sum(1 for it in items if it["week"] == w) for w in range(TOTAL_WEEKS)]
        max_c = max(week_counts) if max(week_counts) > 0 else 1

        st.markdown("**ภาพรวมรายอาทิตย์ (9 เดือน · 39 อาทิตย์)**")

        # Month labels
        month_html = "".join(
            f'<span style="display:inline-block;width:{100/9:.2f}%;text-align:center;font-size:10px;color:#aaa;">{MONTH_NAMES[m]}</span>'
            for m in range(9)
        )
        # Bars
        bars_html = "".join(
            f'<span class="tl-bar" style="height:{max(8, int(c/max_c*44))}px;width:calc({100/TOTAL_WEEKS:.2f}% - 2px);margin:0 1px;" title="อาทิตย์ที่ {i+1}: {c} ผลงาน"></span>'
            if c > 0 else
            f'<span class="tl-bar-empty" style="width:calc({100/TOTAL_WEEKS:.2f}% - 2px);margin:0 1px;" title="อาทิตย์ที่ {i+1}: ไม่มีผลงาน"></span>'
            for i, c in enumerate(week_counts)
        )
        st.markdown(f"""
        <div style="background:#fff;border-radius:12px;border:1px solid #E8E6DF;padding:1rem 1.2rem;margin-bottom:16px;">
            <div style="width:100%;margin-bottom:4px;">{month_html}</div>
            <div style="width:100%;display:flex;align-items:flex-end;height:50px;">{bars_html}</div>
        </div>""", unsafe_allow_html=True)

    # ── Filter & Search ─────────────────────────────────────────
    col_search, col_filter, col_week = st.columns([3, 2, 2])
    with col_search:
        search = st.text_input("", placeholder="🔍 ค้นหาผลงาน...", label_visibility="collapsed")
    with col_filter:
        ftype = st.selectbox("", ["ทั้งหมด","รูปภาพ","PDF","บทความ"], label_visibility="collapsed")
    with col_week:
        week_opts = ["ทุกอาทิตย์"] + [week_label(w) for w in range(TOTAL_WEEKS)]
        week_sel = st.selectbox("", week_opts, label_visibility="collapsed")

    # Add button
    if st.button("➕ เพิ่มผลงาน", type="primary", key="add_btn"):
        st.session_state.edit_item_id = "__new__"

    # ── Add / Edit form ─────────────────────────────────────────
    if st.session_state.edit_item_id:
        is_new = st.session_state.edit_item_id == "__new__"
        existing = next((x for x in items if x["id"] == st.session_state.edit_item_id), None) if not is_new else None

        with st.form("item_form"):
            st.markdown(f"### {'เพิ่มผลงานใหม่' if is_new else 'แก้ไขผลงาน'}")
            title = st.text_input("ชื่อผลงาน *", value=existing["title"] if existing else "", placeholder="เช่น งานวิเคราะห์ข้อมูลลูกค้า")
            week_idx = st.selectbox("อาทิตย์ที่ฝึก", range(TOTAL_WEEKS),
                                    index=existing["week"] if existing else 0,
                                    format_func=week_label)
            desc = st.text_area("คำอธิบาย", value=existing["desc"] if existing else "",
                                placeholder="สรุปสิ่งที่ทำ สิ่งที่เรียนรู้ หรือผลลัพธ์ที่ได้...", height=80)

            uploaded = None
            if is_new:
                uploaded = st.file_uploader("ไฟล์ผลงาน", type=["jpg","jpeg","png","pdf","txt","doc","docx"],
                                            accept_multiple_files=True)

            c_save, c_cancel = st.columns([1,4])
            with c_save:
                submitted = st.form_submit_button("💾 บันทึก", type="primary")
            with c_cancel:
                if st.form_submit_button("ยกเลิก"):
                    st.session_state.edit_item_id = None
                    st.rerun()

            if submitted:
                if not title.strip():
                    st.error("กรุณากรอกชื่อผลงาน")
                else:
                    files = existing["files"] if existing else []
                    if uploaded:
                        for f in uploaded:
                            f.seek(0)
                            b64 = base64.b64encode(f.read()).decode()
                            ftype_det = "รูปภาพ" if f.type.startswith("image/") else "PDF" if f.name.endswith(".pdf") else "บทความ"
                            files.append({"id": str(uuid.uuid4()), "name": f.name,
                                          "type": ftype_det, "size": f.size, "b64": b64, "mime": f.type})

                    new_item = {
                        "id":    existing["id"] if existing else str(uuid.uuid4()),
                        "title": title.strip(),
                        "desc":  desc.strip(),
                        "week":  int(week_idx),
                        "files": files,
                        "date":  existing["date"] if existing else date.today().strftime("%d/%m/%Y"),
                    }
                    if existing:
                        st.session_state.items = [new_item if x["id"] == existing["id"] else x for x in items]
                    else:
                        st.session_state.items.insert(0, new_item)
                    st.session_state.edit_item_id = None
                    st.success("บันทึกเรียบร้อย!")
                    st.rerun()

    # ── Item list ───────────────────────────────────────────────
    filtered = [
        it for it in items
        if (ftype == "ทั้งหมด" or any(f["type"] == ftype for f in it["files"]))
        and (not search or search.lower() in it["title"].lower() or search.lower() in it["desc"].lower())
        and (week_sel == "ทุกอาทิตย์" or it["week"] == week_opts.index(week_sel) - 1)
    ]
    filtered.sort(key=lambda x: x["week"])

    if not filtered:
        st.info("ยังไม่มีผลงาน" if not items else "ไม่พบผลงานที่ค้นหา")
    else:
        cols = st.columns(3)
        for i, item in enumerate(filtered):
            with cols[i % 3]:
                imgs = [f for f in item["files"] if f["type"] == "รูปภาพ"]
                docs = [f for f in item["files"] if f["type"] != "รูปภาพ"]

                with st.container(border=True):
                    # Cover image
                    if imgs:
                        img_data = imgs[0]["b64"]
                        mime = imgs[0].get("mime","image/jpeg")
                        st.markdown(
                            f'<img src="data:{mime};base64,{img_data}" style="width:100%;height:160px;object-fit:cover;border-radius:8px;margin-bottom:8px;">',
                            unsafe_allow_html=True)

                    # Badges
                    badge_html = f'<span class="badge badge-week">อาทิตย์ที่ {item["week"]+1}</span>'
                    badge_html += f'<span class="badge badge-month">{week_to_month(item["week"])}</span>'
                    for ft in set(f["type"] for f in item["files"]):
                        cls = {"รูปภาพ":"badge-img","PDF":"badge-pdf","บทความ":"badge-blog"}.get(ft,"badge-month")
                        badge_html += f'<span class="badge {cls}">{ft}</span>'
                    st.markdown(badge_html, unsafe_allow_html=True)

                    st.markdown(f"**{item['title']}**")
                    if item["desc"]:
                        st.caption(item["desc"][:120] + ("..." if len(item["desc"])>120 else ""))

                    # Show docs
                    for f in docs:
                        b64 = f["b64"]
                        st.download_button(f"⬇ {f['name']}", data=base64.b64decode(b64),
                                           file_name=f["name"], key=f"dl_{f['id']}")

                    # Extra images
                    if len(imgs) > 1:
                        with st.expander(f"รูปเพิ่มเติม ({len(imgs)-1})"):
                            for img in imgs[1:]:
                                st.image(base64.b64decode(img["b64"]), use_container_width=True)

                    col_e, col_d = st.columns(2)
                    with col_e:
                        if st.button("แก้ไข", key=f"edit_{item['id']}", use_container_width=True):
                            st.session_state.edit_item_id = item["id"]
                            st.rerun()
                    with col_d:
                        if st.button("🗑️ ลบ", key=f"del_{item['id']}", use_container_width=True):
                            st.session_state.items = [x for x in items if x["id"] != item["id"]]
                            st.rerun()
                    st.caption(item["date"])

# ══════════════════════════════════════════════════════════════
#  PAGE: PROJECT
# ══════════════════════════════════════════════════════════════
elif st.session_state.page == "project":
    st.markdown("## 📋 โครงงานสหกิจศึกษา")
    st.caption("อัปโหลดและแสดงไฟล์รายงานโครงงาน")

    projects = st.session_state.projects

    # ── Add project form ────────────────────────────────────────
    with st.expander("➕ เพิ่มโครงงานใหม่", expanded=len(projects)==0):
        with st.form("project_form"):
            proj_title = st.text_input("ชื่อโครงงาน *", placeholder="เช่น การออกแบบระบบระบายน้ำ...")
            proj_desc  = st.text_area("รายละเอียด / บทคัดย่อ",
                                      placeholder="สรุปโครงงาน วัตถุประสงค์ หรือผลลัพธ์ที่ได้...", height=80)
            proj_pdf   = st.file_uploader("ไฟล์ PDF โครงงาน *", type=["pdf"])

            if st.form_submit_button("💾 บันทึกโครงงาน", type="primary"):
                if not proj_title.strip():
                    st.error("กรุณากรอกชื่อโครงงาน")
                elif not proj_pdf:
                    st.error("กรุณาแนบไฟล์ PDF")
                else:
                    proj_pdf.seek(0)
                    b64 = base64.b64encode(proj_pdf.read()).decode()
                    st.session_state.projects.insert(0, {
                        "id":    str(uuid.uuid4()),
                        "title": proj_title.strip(),
                        "desc":  proj_desc.strip(),
                        "date":  date.today().strftime("%d/%m/%Y"),
                        "pdf": {"name": proj_pdf.name, "size": proj_pdf.size, "b64": b64},
                    })
                    st.success("เพิ่มโครงงานเรียบร้อย!")
                    st.rerun()

    st.divider()

    # ── Project list ────────────────────────────────────────────
    if not projects:
        st.info("ยังไม่มีโครงงาน — กดเพิ่มโครงงานใหม่ด้านบน")
    else:
        for proj in projects:
            with st.container(border=True):
                col_icon, col_info, col_actions = st.columns([0.5, 6, 2])

                with col_icon:
                    st.markdown("<span style='font-size:32px'>📄</span>", unsafe_allow_html=True)

                with col_info:
                    st.markdown(f"**{proj['title']}**")
                    if proj["desc"]:
                        st.caption(proj["desc"][:200])
                    st.caption(f"📅 {proj['date']}  ·  📎 {proj['pdf']['name']}  ·  {proj['pdf']['size']//1024} KB")

                with col_actions:
                    viewing = st.session_state.viewing_project_id == proj["id"]
                    btn_label = "📕 ซ่อน PDF" if viewing else "📖 เปิดอ่าน"
                    if st.button(btn_label, key=f"view_{proj['id']}", use_container_width=True):
                        st.session_state.viewing_project_id = None if viewing else proj["id"]
                        st.rerun()

                    st.download_button("⬇ ดาวน์โหลด",
                                       data=base64.b64decode(proj["pdf"]["b64"]),
                                       file_name=proj["pdf"]["name"],
                                       mime="application/pdf",
                                       key=f"dl_{proj['id']}",
                                       use_container_width=True)

                    if st.button("🗑️ ลบ", key=f"dproj_{proj['id']}", use_container_width=True):
                        st.session_state.projects = [x for x in projects if x["id"] != proj["id"]]
                        if st.session_state.viewing_project_id == proj["id"]:
                            st.session_state.viewing_project_id = None
                        st.rerun()

                # PDF Viewer
                if st.session_state.viewing_project_id == proj["id"]:
                    st.markdown("---")
                    display_pdf(proj["pdf"]["b64"])
