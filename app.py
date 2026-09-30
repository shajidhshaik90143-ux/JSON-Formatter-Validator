import json
from pathlib import Path
import streamlit as st
from src.json_tools import (
    parse_json, format_json, minify_json, validate_json,
    json_stats, flatten_json, jsonpath_query, diff_json
)

st.set_page_config(
    page_title="JSON Formatter & Validator",
    page_icon="{}",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main {max-width: 1450px; margin: auto;}
.hero {
    padding: 1.3rem 1.5rem;
    border-radius: 18px;
    background: linear-gradient(135deg,#111827,#1f2937);
    color: white;
    margin-bottom: 1rem;
}
.hero h1 {margin:0 0 .3rem 0;}
.hero p {margin:0;color:#cbd5e1;}
.card {
    border:1px solid #e5e7eb;
    border-radius:14px;
    padding:14px;
    background:#fff;
}
.small {color:#64748b;font-size:.9rem;}
.badge {
    display:inline-block;padding:4px 9px;border-radius:999px;
    background:#eef2ff;color:#3730a3;font-size:.78rem;font-weight:600;
}
</style>
""", unsafe_allow_html=True)

if "json_text" not in st.session_state:
    st.session_state.json_text = '{\n  "name": "JSON Formatter",\n  "version": 1,\n  "features": ["format", "validate", "query"]\n}'
if "json_text_b" not in st.session_state:
    st.session_state.json_text_b = ""

st.markdown("""
<div class="hero">
<h1>JSON Formatter & Validator</h1>
<p>Format, validate, inspect, query, compare, flatten and export JSON from one professional workspace.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Workspace")
    uploaded = st.file_uploader("Import JSON", type=["json", "txt"])
    if uploaded:
        try:
            st.session_state.json_text = uploaded.getvalue().decode("utf-8")
            st.success("JSON imported.")
        except Exception as e:
            st.error(f"Could not read file: {e}")

    st.divider()
    indent = st.selectbox("Indentation", [2, 4, 1], index=0)
    sort_keys = st.checkbox("Sort object keys", value=False)
    ensure_ascii = st.checkbox("Escape non-ASCII", value=False)
    st.divider()
    st.caption("Tip: Use Ctrl+A inside the editor, paste JSON, then switch tabs.")

tabs = st.tabs(["Formatter", "Validator", "Explorer", "Query", "Diff", "Flatten & Export"])

with tabs[0]:
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Input JSON")
        st.session_state.json_text = st.text_area(
            "JSON input", st.session_state.json_text, height=470,
            label_visibility="collapsed"
        )
        a, b, c = st.columns(3)
        with a:
            if st.button("Beautify", use_container_width=True):
                obj, err = parse_json(st.session_state.json_text)
                if err:
                    st.error(err)
                else:
                    st.session_state.json_text = format_json(
                        obj, indent, sort_keys, ensure_ascii
                    )
                    st.rerun()
        with b:
            if st.button("Minify", use_container_width=True):
                obj, err = parse_json(st.session_state.json_text)
                if err:
                    st.error(err)
                else:
                    st.session_state.json_text = minify_json(obj, sort_keys, ensure_ascii)
                    st.rerun()
        with c:
            if st.button("Clear", use_container_width=True):
                st.session_state.json_text = ""
                st.rerun()

    with c2:
        st.subheader("Formatted Preview")
        obj, err = parse_json(st.session_state.json_text)
        if err:
            st.error(err)
            st.code(st.session_state.json_text or "", language="json")
        else:
            formatted = format_json(obj, indent, sort_keys, ensure_ascii)
            st.code(formatted, language="json")
            st.download_button(
                "Download formatted JSON",
                formatted.encode("utf-8"),
                "formatted.json",
                "application/json",
                use_container_width=True,
            )

with tabs[1]:
    st.subheader("JSON Validation")
    result = validate_json(st.session_state.json_text)
    if result["valid"]:
        st.success("Valid JSON")
        st.write(f"Root type: **{result['root_type']}**")
        st.write(f"Characters: **{result['characters']:,}**")
        st.write(f"Lines: **{result['lines']:,}**")
    else:
        st.error("Invalid JSON")
        st.code(result["error"])
        if result.get("line"):
            st.write(f"Approximate location: line **{result['line']}**, column **{result['column']}**")

    if result["valid"]:
        stats = json_stats(result["data"])
        cols = st.columns(5)
        for col, (label, value) in zip(cols, [
            ("Objects", stats["objects"]), ("Arrays", stats["arrays"]),
            ("Strings", stats["strings"]), ("Numbers", stats["numbers"]),
            ("Max depth", stats["max_depth"])
        ]):
            col.metric(label, value)

with tabs[2]:
    st.subheader("JSON Explorer")
    obj, err = parse_json(st.session_state.json_text)
    if err:
        st.error(err)
    else:
        mode = st.radio("View", ["JSON Tree", "Table"], horizontal=True)
        if mode == "JSON Tree":
            st.json(obj, expanded=2)
        else:
            flat = flatten_json(obj)
            if flat:
                import pandas as pd
                df = pd.DataFrame(flat, columns=["Path", "Type", "Value"])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No scalar values found.")

with tabs[3]:
    st.subheader("JSON Query")
    obj, err = parse_json(st.session_state.json_text)
    if err:
        st.error(err)
    else:
        query = st.text_input("Path", value="$.features[0]", placeholder="Example: $.users[0].name")
        if st.button("Run Query", type="primary"):
            value, found, message = jsonpath_query(obj, query)
            if found:
                st.success("Match found")
                st.json(value)
            else:
                st.warning(message)
        st.markdown("Supported syntax: `$.user.name`, `$.users[0].name`, `$['user-name']`, `$`")

with tabs[4]:
    st.subheader("JSON Diff")
    left, right = st.columns(2)
    with left:
        st.session_state.json_text = st.text_area(
            "JSON A", st.session_state.json_text, height=350, key="diff_a"
        )
    with right:
        st.session_state.json_text_b = st.text_area(
            "JSON B", st.session_state.json_text_b, height=350, key="diff_b"
        )
    if st.button("Compare JSON", type="primary"):
        a_obj, a_err = parse_json(st.session_state.json_text)
        b_obj, b_err = parse_json(st.session_state.json_text_b)
        if a_err or b_err:
            if a_err: st.error(f"JSON A: {a_err}")
            if b_err: st.error(f"JSON B: {b_err}")
        else:
            changes = diff_json(a_obj, b_obj)
            if not changes:
                st.success("The two JSON documents are identical.")
            else:
                import pandas as pd
                st.dataframe(pd.DataFrame(changes), use_container_width=True, hide_index=True)

with tabs[5]:
    st.subheader("Flatten & Export")
    obj, err = parse_json(st.session_state.json_text)
    if err:
        st.error(err)
    else:
        rows = flatten_json(obj)
        import pandas as pd
        df = pd.DataFrame(rows, columns=["Path", "Type", "Value"])
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download flattened CSV", csv, "json_flattened.csv",
            "text/csv", use_container_width=True
        )
        pretty = format_json(obj, indent, sort_keys, ensure_ascii)
        st.download_button(
            "Download pretty JSON", pretty.encode("utf-8"), "data.json",
            "application/json", use_container_width=True
        )
