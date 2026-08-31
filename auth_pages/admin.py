"""
pages/admin.py — Admin Dashboard
=================================
Only accessible to users with role='admin'.
Sections:
  1. User Management   — view all users, change roles, delete users
  2. All Calculations  — see every calculation by every user
  3. Emission Factors  — edit kgCO₂/kg values live
  4. Transport Factors — edit kgCO₂/tonne·km values live
  5. Box Config        — edit ply options, plastic types, pallet constants
"""

import os
import json
import html
from datetime import datetime
import streamlit as st
import pandas as pd

from auth import session
from database.db import UserManager, DatabaseManager, ConfigManager, SessionManager
from config.settings import DB_CONFIG

# ── Init managers ─────────────────────────────────────────────────────────────
db_path = os.path.abspath(DB_CONFIG.get("sqlite_path", "carbon_calculator.db"))
um  = UserManager(db_path)
db  = DatabaseManager(DB_CONFIG)
cfg = ConfigManager(db_path)
sm  = SessionManager(db_path)


def render():
    """Main entry point — called from app.py when page == 'Admin'."""

    session.require_admin()   # stops rendering if not admin

    user = session.current_user()

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#003057,#005288);
                padding:18px 28px;border-radius:8px;margin-bottom:24px;
                border-left:5px solid #F5A623;">
        <div style="font-family:'Barlow Condensed',sans-serif;font-size:1.4rem;
                    font-weight:700;color:#FFFFFF;text-transform:uppercase;letter-spacing:1px;">
            Admin Dashboard
        </div>
        <div style="font-size:0.82rem;color:#F5A623;margin-top:4px;">
            Logged in as {html.escape(user.get('email', ''))} — admin access
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "👥 Users",
        "📊 All Calculations",
        "🧪 Emission Factors",
        "🚛 Transport Factors",
        "📦 Box & Pallet Config",
        "🔒 Active Sessions",
    ])

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 1 — USER MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### All Users")
        users = um.get_all_users()

        if not users:
            st.info("No users yet — users appear here after first login.")
        else:
            df_users = pd.DataFrame(users)
            st.dataframe(df_users, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("#### Change Role")
            emails = [u["email"] for u in users]
            rc1, rc2, rc3 = st.columns([3, 2, 1])
            with rc1:
                target_email = st.selectbox("Select user", emails, key="role_email")
            with rc2:
                new_role = st.selectbox("New role", ["user", "admin"], key="role_val")
            with rc3:
                st.markdown("<div style='margin-top:26px'></div>", unsafe_allow_html=True)
                if st.button("Apply", key="role_btn"):
                    if target_email == user.get("email") and new_role == "user":
                        st.error("You cannot demote yourself.")
                    else:
                        ok, msg = um.set_role(target_email, new_role)
                        st.success(msg) if ok else st.error(msg)

            st.markdown("---")
            st.markdown("#### Delete User")
            st.warning("Deleting a user does NOT delete their calculations — only their login access.")
            dc1, dc2 = st.columns([3, 1])
            with dc1:
                del_email = st.selectbox("Select user to delete", emails, key="del_user_email")
            with dc2:
                st.markdown("<div style='margin-top:26px'></div>", unsafe_allow_html=True)
                if st.button("Delete User", key="del_user_btn"):
                    if del_email == user.get("email"):
                        st.error("You cannot delete your own account.")
                    else:
                        ok, msg = um.delete_user(del_email)
                        st.success(msg) if ok else st.error(msg)
                        st.rerun()

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 2 — ALL CALCULATIONS
    # ═══════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("### All Calculations (All Users)")
        st.markdown(
            '<div style="background:#FFF8E1;border-left:4px solid #F5A623;'
            'padding:10px 14px;border-radius:4px;font-size:0.84rem;color:#7A5200;margin-bottom:16px;">'
            '⚠ Deleting here (or a user deleting their own record) only hides it from normal views — '
            'admins can still see and restore it below.</div>',
            unsafe_allow_html=True
        )

        # Build user email lookup
        users      = um.get_all_users()
        user_map   = {u["id"]: u["email"] for u in users}

        records    = db.get_all_calculations(include_deleted=True)   # admins see deleted rows too

        if not records:
            st.info("No calculations saved yet.")
        else:
            active_count  = sum(1 for r in records if not r.get("deleted_at"))
            deleted_count = len(records) - active_count
            st.markdown(
                f'<div style="color:#8D9BAD;font-size:0.82rem;margin-bottom:10px;">'
                f'{len(records)} total calculation(s) — {active_count} active, {deleted_count} deleted</div>',
                unsafe_allow_html=True
            )

            user_options = ["All Users"] + sorted({
                user_map.get(r.get("user_id"), "— No User —") for r in records
            })
            filter_user = st.selectbox("Filter by User", user_options, key="admin_calc_user_filter")
            if filter_user != "All Users":
                records = [r for r in records
                           if user_map.get(r.get("user_id"), "— No User —") == filter_user]
                st.markdown(
                    f'<div style="color:#8D9BAD;font-size:0.78rem;margin-bottom:10px;">'
                    f'Showing {len(records)} record(s) for {html.escape(filter_user)}</div>',
                    unsafe_allow_html=True
                )

            record_dates = []
            for r in records:
                try:
                    record_dates.append(
                        datetime.strptime(str(r.get("timestamp", "")), "%Y-%m-%d %H:%M:%S").date()
                    )
                except Exception:
                    pass

            if record_dates:
                min_date, max_date = min(record_dates), max(record_dates)
                st.markdown("**Filter by Date**")
                date_from_col, date_to_col = st.columns(2)
                with date_from_col:
                    date_from = st.date_input("From", value=min_date, min_value=min_date,
                                               max_value=max_date, key="admin_calc_date_from")
                with date_to_col:
                    date_to = st.date_input("To", value=max_date, min_value=min_date,
                                             max_value=max_date, key="admin_calc_date_to")

                def _in_date_range(r):
                    try:
                        d = datetime.strptime(str(r.get("timestamp", "")), "%Y-%m-%d %H:%M:%S").date()
                    except Exception:
                        return True
                    return date_from <= d <= date_to

                records = [r for r in records if _in_date_range(r)]
                st.markdown(
                    f'<div style="color:#8D9BAD;font-size:0.78rem;margin-bottom:10px;">'
                    f'Showing {len(records)} record(s) from {date_from.strftime("%d %b %Y")} '
                    f'to {date_to.strftime("%d %b %Y")}</div>',
                    unsafe_allow_html=True
                )

            rows = []
            for r in records:
                inp = r.get("inputs", {})
                out = r.get("outputs", {})
                rows.append({
                    "ID":          r.get("id"),
                    "Status":      "Deleted" if r.get("deleted_at") else "Active",
                    "User":        user_map.get(r.get("user_id"), "—"),
                    "Timestamp":   r.get("timestamp"),
                    "Deleted At":  r.get("deleted_at") or "—",
                    "Project":     inp.get("pc_name", "—"),
                    "Product":     inp.get("product_name", "—"),
                    "Box":         inp.get("box_choice", "—"),
                    "CO₂ Design":  round(out.get("co2_total_design", 0), 4),
                    "CO₂ Physical":round(out.get("co2_total_phys", 0), 4),
                    "Transport":   inp.get("transport_design", "—"),
                    "Notes":       r.get("description", ""),
                })
            df_all = pd.DataFrame(rows)
            st.dataframe(df_all, use_container_width=True, hide_index=True,
                         column_config={
                             "CO₂ Design":   st.column_config.NumberColumn(format="%.4f"),
                             "CO₂ Physical": st.column_config.NumberColumn(format="%.4f"),
                         })

            active_ids  = [r.get("id") for r in records if not r.get("deleted_at")]
            deleted_ids = [r.get("id") for r in records if r.get("deleted_at")]

            st.markdown("---")
            st.markdown("#### Delete a Calculation")
            if active_ids:
                del_id = st.selectbox("Record ID to delete", active_ids, key="admin_del_calc")
                if st.button("Delete Calculation", key="admin_del_calc_btn"):
                    db.delete_calculation(del_id)
                    st.success(f"Record #{del_id} deleted (hidden from normal views, still recoverable).")
                    st.rerun()
            else:
                st.info("No active calculations to delete.")

            st.markdown("---")
            st.markdown("#### Restore a Deleted Calculation")
            if deleted_ids:
                restore_id = st.selectbox("Record ID to restore", deleted_ids, key="admin_restore_calc")
                if st.button("Restore Calculation", key="admin_restore_calc_btn"):
                    db.restore_calculation(restore_id)
                    st.success(f"Record #{restore_id} restored.")
                    st.rerun()
            else:
                st.info("No deleted calculations.")

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 3 — EMISSION FACTORS
    # ═══════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### Material Emission Factors")
        st.markdown(
            '<div style="background:#FFF8E1;border-left:4px solid #F5A623;'
            'padding:10px 14px;border-radius:4px;font-size:0.84rem;color:#7A5200;margin-bottom:16px;">'
            '⚠ Changes take effect immediately on the next calculation. '
            'These values override the hardcoded defaults in formulas.py.</div>',
            unsafe_allow_html=True
        )

        emission_keys = [
            ("emission_corrugation", "Corrugation"),
            ("emission_solidwood",   "Solidwood"),
            ("emission_plywood",     "Plywood"),
            ("emission_ldpe",        "LDPE Plastic"),
            ("emission_hdpe",        "HDPE Plastic"),
            ("emission_pp",          "PP Plastic"),
            ("emission_lldpe",       "LLDPE Plastic"),
            ("emission_ps",          "PS Plastic"),
        ]

        for key, label in emission_keys:
            current = cfg.get_float(key)
            ec1, ec2, ec3 = st.columns([3, 2, 1])
            with ec1:
                st.markdown(
                    f'<div style="padding:8px 0;font-size:0.88rem;font-weight:600;'
                    f'color:#003057;">{label}</div>',
                    unsafe_allow_html=True
                )
            with ec2:
                new_val = st.number_input(
                    f"kgCO₂/kg",
                    value=current,
                    step=0.001,
                    format="%.3f",
                    key=f"ef_{key}",
                    label_visibility="collapsed",
                )
            with ec3:
                if st.button("Save", key=f"ef_save_{key}"):
                    ok, msg = cfg.set(key, str(new_val))
                    st.toast(f"✓ {label} updated" if ok else f"✗ {msg}")

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 4 — TRANSPORT FACTORS
    # ═══════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown("### Transport Emission Factors (kgCO₂/tonne·km)")

        transport_keys = [
            ("transport_road", "Road"),
            ("transport_rail", "Rail"),
            ("transport_sea",  "Sea (Ocean)"),
            ("transport_air",  "Air"),
        ]

        for key, label in transport_keys:
            current = cfg.get_float(key)
            tc1, tc2, tc3 = st.columns([3, 2, 1])
            with tc1:
                st.markdown(
                    f'<div style="padding:8px 0;font-size:0.88rem;font-weight:600;'
                    f'color:#003057;">{label}</div>',
                    unsafe_allow_html=True
                )
            with tc2:
                new_val = st.number_input(
                    "kgCO₂/t·km",
                    value=current,
                    step=0.001,
                    format="%.4f",
                    key=f"tf_{key}",
                    label_visibility="collapsed",
                )
            with tc3:
                if st.button("Save", key=f"tf_save_{key}"):
                    ok, msg = cfg.set(key, str(new_val))
                    st.toast(f"✓ {label} updated" if ok else f"✗ {msg}")

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 5 — BOX & PALLET CONFIG
    # ═══════════════════════════════════════════════════════════════════════
    with tab5:
        st.markdown("### Box Ply Options")
        current_ply = cfg.get("ply_options", "[3, 5, 7]")
        new_ply = st.text_input(
            "Ply options (JSON list, e.g. [3, 5, 7, 9])",
            value=current_ply,
            key="cfg_ply",
        )
        if st.button("Save Ply Options", key="cfg_ply_btn"):
            try:
                parsed = json.loads(new_ply)
                assert isinstance(parsed, list) and all(isinstance(x, int) for x in parsed)
                ok, msg = cfg.set("ply_options", new_ply)
                st.toast(f"✓ Ply options updated" if ok else f"✗ {msg}")
            except Exception:
                st.error("Invalid format. Must be a JSON list of integers, e.g. [3, 5, 7]")

        st.markdown("---")
        st.markdown("### Plastic Types")
        current_pt = cfg.get("plastic_types", '["LDPE","HDPE","PP","LLDPE","PS"]')
        new_pt = st.text_input(
            'Plastic types (JSON list, e.g. ["LDPE","HDPE","PP"])',
            value=current_pt,
            key="cfg_pt",
        )
        if st.button("Save Plastic Types", key="cfg_pt_btn"):
            try:
                parsed = json.loads(new_pt)
                assert isinstance(parsed, list) and all(isinstance(x, str) for x in parsed)
                ok, msg = cfg.set("plastic_types", new_pt)
                st.toast(f"✓ Plastic types updated" if ok else f"✗ {msg}")
            except Exception:
                st.error('Invalid format. Must be a JSON list of strings, e.g. ["LDPE","PP"]')

        st.markdown("---")
        st.markdown("### Pallet Constants")
        pallet_keys = [
            ("pallet_deck_h",       "Deck Height (mm)",    "int"),
            ("pallet_runner_l",     "Runner Length (mm)",  "int"),
            ("pallet_runner_w",     "Runner Width (mm)",   "int"),
            ("pallet_runner_h",     "Runner Height (mm)",  "int"),
            ("pallet_runner_count", "Runner Count",        "int"),
            ("pallet_plank_w",      "Plank Width (mm)",    "int"),
            ("pallet_plank_h",      "Plank Height (mm)",   "int"),
            ("pallet_plank_count",  "Plank Count",         "int"),
            ("pallet_density",      "Wood Density (kg/m³)","int"),
            ("box_clearance",       "Box Clearance (mm)",  "int"),
        ]
        for key, label, dtype in pallet_keys:
            current = cfg.get_int(key)
            pc1, pc2, pc3 = st.columns([3, 2, 1])
            with pc1:
                st.markdown(
                    f'<div style="padding:8px 0;font-size:0.88rem;font-weight:600;'
                    f'color:#003057;">{label}</div>',
                    unsafe_allow_html=True
                )
            with pc2:
                new_val = st.number_input(
                    label, value=current, step=1,
                    key=f"pc_{key}", label_visibility="collapsed"
                )
            with pc3:
                if st.button("Save", key=f"pc_save_{key}"):
                    ok, msg = cfg.set(key, str(int(new_val)))
                    st.toast(f"✓ {label} updated" if ok else f"✗ {msg}")

        st.markdown("---")
        st.markdown("### Raw Config Table")
        st.dataframe(
            pd.DataFrame(cfg.get_all()),
            use_container_width=True,
            hide_index=True
        )

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 6 — ACTIVE SESSIONS
    # ═══════════════════════════════════════════════════════════════════════
    with tab6:
        st.markdown("### Active Login Sessions")
        st.markdown(
            '<div style="background:#FFF8E1;border-left:4px solid #F5A623;'
            'padding:10px 14px;border-radius:4px;font-size:0.84rem;color:#7A5200;margin-bottom:16px;">'
            '⚠ Terminating a session signs that browser out immediately (on its next interaction) '
            'and requires them to sign in again — it does not delete their account or calculations.</div>',
            unsafe_allow_html=True
        )

        my_token    = session.get_session_token()
        sessions    = sm.get_active_sessions()

        if not sessions:
            st.info("No active sessions.")
        else:
            rows = [{
                "Email":      s["email"],
                "Name":       s["name"],
                "Started":    s["created_at"],
                "Last Seen":  s["last_seen"],
                "This Device": "Yes" if s["token"] == my_token else "",
            } for s in sessions]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("#### Terminate a Session")
            options = {
                f'{s["email"]} — started {s["created_at"]}'
                f'{" (this device)" if s["token"] == my_token else ""}': s["token"]
                for s in sessions
            }
            sc1, sc2 = st.columns([3, 1])
            with sc1:
                chosen_label = st.selectbox("Select session", list(options.keys()), key="term_session")
            with sc2:
                st.markdown("<div style='margin-top:26px'></div>", unsafe_allow_html=True)
                if st.button("Terminate", key="term_session_btn"):
                    token = options[chosen_label]
                    sm.revoke(token)
                    if token == my_token:
                        st.warning("You terminated your own session — you'll be signed out now.")
                        session.logout()
                    st.success("Session terminated.")
                    st.rerun()
