import json
import streamlit as st
import pandas as pd

from generate_forecast import generate_forecast
from chatbot import get_chemist_response, SUGGESTION_CHIPS
from formulation import generate_formulation, TRENDING_ACTIVES
from docs import generate_document, DESTINATION_COUNTRIES, DOCUMENT_TYPES

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Kanzen Forecast", page_icon="⚡", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.block-container { max-width: 750px; padding-top: 2rem; }

.section-label {
    font-size: 0.72rem;
    font-weight: 700;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: .1em;
    margin-bottom: 6px;
    margin-top: 18px;
}
.badge { padding: 3px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; color: #fff; }
.badge-low    { background: #2ecc71; }
.badge-medium { background: #f39c12; }
.badge-high   { background: #e74c3c; }

/* Chatbot styles */
.chat-header {
    display: flex; align-items: center; gap: 12px;
    background: #fff; border-radius: 16px 16px 0 0;
    padding: 14px 18px; border-bottom: 1px solid #f0f0f0;
}
.online-dot {
    width: 9px; height: 9px; border-radius: 50%;
    background: #2ecc71; display: inline-block; margin-right: 4px;
}
.chip {
    display: inline-block;
    background: #f1f5f9; border-radius: 20px;
    padding: 5px 14px; margin: 4px;
    font-size: 0.8rem; color: #334155;
    cursor: pointer; border: 1px solid #e2e8f0;
}
.user-bubble {
    background: #0d9488; color: #fff;
    border-radius: 18px 18px 4px 18px;
    padding: 10px 16px; margin: 6px 0 6px auto;
    max-width: 80%; width: fit-content;
    margin-left: auto; font-size: 0.92rem;
}
.bot-bubble {
    background: #f8fafc; color: #1e293b;
    border-radius: 18px 18px 18px 4px;
    padding: 10px 16px; margin: 6px auto 6px 0;
    max-width: 90%; width: fit-content;
    font-size: 0.92rem; border: 1px solid #e2e8f0;
}
</style>
""", unsafe_allow_html=True)

# ── App header ────────────────────────────────────────────────────────────────
st.markdown("## ⚡ Kanzen Forecast v2.3")
st.caption("AI-powered demand prediction · 18-month sales history · market & seasonal signals")
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 Generate Forecast", "🧪 Chemist Bot", "🧪 Formulation Lab", "📄 Global Logistics"])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FORECAST
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:

    def risk_badge(level: str) -> str:
        css_class = f"badge badge-{level.lower()}"
        return f'<span class="{css_class}">{level}</span>'

    with st.form("forecast_form"):
        st.markdown('<div class="section-label">Product Details</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            product_name = st.text_input("Product Name", placeholder="e.g. Lumina Vitamin C Serum")
            pack_size    = st.selectbox("Pack Size", ["30ml", "50ml", "100ml", "150ml", "200ml", "Custom"])
            mfg_date     = st.text_input("MFG Date (DD/MM/YYYY)", placeholder="11/12/2026")
        with col2:
            category     = st.selectbox("Category",
                                        ["Serum", "Moisturiser", "Cleanser", "SPF / Sun Care",
                                         "Eye Care", "Body Care", "Mask"])
            retail_price = st.number_input("Retail Price ($)", min_value=1.0, value=42.0, step=0.5)
            expiry_date  = st.text_input("Expiry Date (DD/MM/YYYY)", placeholder="11/12/2028")

        quantity = st.number_input("Batch Quantity (units)", min_value=1, value=5000, step=100)

        st.markdown('<div class="section-label">Product Image</div>', unsafe_allow_html=True)
        st.markdown("""
            <div style="border:2px dashed #38bdf8;border-radius:12px;padding:24px;
                        text-align:center;background:#f8fafc;color:#64748b;">
                <div style="font-size:1.8rem">📎</div>
                <div style="font-weight:600;color:#334155">Attach Product Image</div>
                <div style="font-size:0.78rem;color:#94a3b8">PNG or JPG, up to 10MB</div>
            </div>""", unsafe_allow_html=True)

        product_image = st.file_uploader(
            label="", type=["png", "jpg", "jpeg"], label_visibility="collapsed"
        )

        submitted = st.form_submit_button("🔮 Generate AI Forecast", use_container_width=True)

    if submitted:
        if not product_name.strip():
            st.warning("Please enter a product name.")
        else:
            with st.spinner("Kanzen is analysing market signals…"):
                try:
                    image_bytes = product_image.read() if product_image else None
                    image_mime  = product_image.type  if product_image else "image/jpeg"
                    result = generate_forecast(
                        product_name, category, pack_size,
                        retail_price, int(quantity), mfg_date, expiry_date,
                        image_bytes=image_bytes, image_mime=image_mime,
                    )
                except json.JSONDecodeError as e:
                    st.error(f"Could not parse AI response: {e}")
                    st.stop()
                except Exception as e:
                    st.error(f"Error calling Gemini API: {e}")
                    st.stop()

            acc   = result.get("accuracy", 0)
            qtr   = result.get("quarter", "")
            trend = result.get("trend_points", [])
            inv   = result.get("inventory_risk", "Medium")
            vol   = result.get("demand_volatility", "Medium")
            sup   = result.get("supply_chain_risk", "Medium")
            summ  = result.get("summary", "")

            st.success("Forecast generated!")

            # Review summary
            st.markdown('<div class="section-label">Review & Submit</div>', unsafe_allow_html=True)
            for key, val in {"Name": product_name, "Category": category, "Format": pack_size,
                             "Price": f"${retail_price}", "Quantity": quantity,
                             "MFG Date": mfg_date, "Expiry Date": expiry_date}.items():
                c1, c2 = st.columns(2)
                with c1: st.markdown(f"**{key}**")
                with c2: st.markdown(f"<div style='text-align:right'>{val}</div>", unsafe_allow_html=True)
                st.divider()

            if product_image:
                st.markdown('<div class="section-label">Product Image</div>', unsafe_allow_html=True)
                st.image(product_image, width=200, caption=product_image.name)

            # Forecast results
            st.markdown('<div class="section-label">Forecast Results</div>', unsafe_allow_html=True)
            ca, cb = st.columns([3, 1])
            with ca:
                st.markdown(f"### {product_name}")
                st.caption(qtr)
            with cb:
                st.metric("Accuracy", f"{acc}%")

            if trend:
                st.markdown('<div class="section-label">Demand Trend</div>', unsafe_allow_html=True)
                df = pd.DataFrame({"Demand Index": trend},
                                  index=[f"M{i+1}" for i in range(len(trend))])
                st.line_chart(df, height=200, use_container_width=True)

            st.markdown('<div class="section-label">Risk Indicators</div>', unsafe_allow_html=True)
            for label, level in [("Inventory Risk", inv), ("Demand Volatility", vol), ("Supply Chain Risk", sup)]:
                cl, cr = st.columns([3, 1])
                with cl: st.markdown(f"**{label}**")
                with cr: st.markdown(risk_badge(level), unsafe_allow_html=True)

            st.markdown('<div class="section-label">AI Summary</div>', unsafe_allow_html=True)
            st.info(summ)

            st.download_button(
                label="💾 Save Forecast (JSON)",
                data=json.dumps(result, indent=2),
                file_name=f"forecast_{product_name.replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — CHEMIST BOT
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:

    # Initialise session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chip_input" not in st.session_state:
        st.session_state.chip_input = ""

    # ── Chat header ───────────────────────────────────────────────────────────
    st.markdown("""
        <div class="chat-header">
            <span style="font-size:1.8rem">🧪</span>
            <div>
                <div style="font-weight:700;font-size:1rem">Chemist Bot</div>
                <div style="font-size:0.78rem;color:#64748b">
                    <span class="online-dot"></span>Online
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── Welcome message ───────────────────────────────────────────────────────
    if not st.session_state.chat_history:
        st.markdown("""
            <div class="bot-bubble">
                👋 Hello! I'm your AI Chemist. Ask me about formulations,
                ingredients, regulatory limits, or skincare policies.
            </div>
        """, unsafe_allow_html=True)

    # ── Chat history ──────────────────────────────────────────────────────────
    for turn in st.session_state.chat_history:
        if turn["role"] == "user":
            st.markdown(f'<div class="user-bubble">{turn["content"]}</div>',
                        unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown("🧪 **Chemist Bot**")
                st.markdown(turn["content"])
                st.divider()

    # ── Suggestion chips ──────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Quick Questions</div>', unsafe_allow_html=True)
    chip_cols = st.columns(3)
    for i, chip in enumerate(SUGGESTION_CHIPS):
        with chip_cols[i % 3]:
            if st.button(chip, key=f"chip_{i}", use_container_width=True):
                st.session_state.chip_input = chip

    # ── Input box ─────────────────────────────────────────────────────────────
    st.markdown("---")
    user_input = st.chat_input("Ask about formulation, ingredients, regulations…")

    # Handle chip click or typed input
    message_to_send = st.session_state.chip_input or user_input

    if message_to_send:
        st.session_state.chip_input = ""  # reset chip

        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": message_to_send
        })

        with st.spinner("Chemist Bot is thinking…"):
            try:
                reply = get_chemist_response(
                    message_to_send,
                    st.session_state.chat_history[:-1]  # history without current msg
                )
            except Exception as e:
                reply = f"❌ Error: {e}"

        # Add bot reply to history
        st.session_state.chat_history.append({
            "role": "model",
            "content": reply
        })

        st.rerun()

    # ── Clear chat ────────────────────────────────────────────────────────────
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — FORMULATION LAB
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:

    # ── Trending actives grid ─────────────────────────────────────────────────
    st.markdown("### 🔥 Trending Q1 2026")
    t1, t2 = st.columns(2)
    for i, active in enumerate(TRENDING_ACTIVES):
        with (t1 if i % 2 == 0 else t2):
            st.markdown(f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;
                        padding:14px 18px;margin-bottom:12px;">
                <div style="font-weight:700;font-size:0.95rem">{active['name']}</div>
                <div style="color:#64748b;font-size:0.8rem">{active['category']}</div>
                <div style="color:#2ecc71;font-weight:700;font-size:0.85rem;margin-top:4px">
                    ↑ {active['growth']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # ── Formula Generator ─────────────────────────────────────────────────────
    st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">
            <div style="background:#0d9488;border-radius:10px;padding:8px;font-size:1.2rem">✦</div>
            <span style="font-weight:700;font-size:1.1rem">Formula Generator</span>
        </div>
    """, unsafe_allow_html=True)

    with st.form("formulation_form"):
        skin_type      = st.text_input("SKIN TYPE",      placeholder="e.g. Oily / Combination")
        concern        = st.text_input("CONCERN",         placeholder="e.g. Acne, Hyperpigmentation")
        product_format = st.text_input("FORMAT",          placeholder="e.g. Serum, Moisturiser")

        gen_submitted = st.form_submit_button("✦ Generate AI Formula", use_container_width=True)

    # ── Formula result ────────────────────────────────────────────────────────
    if gen_submitted:
        if not skin_type.strip() or not concern.strip() or not product_format.strip():
            st.warning("Please fill in all three fields.")
        else:
            with st.spinner("Generating your formula…"):
                try:
                    formula = generate_formulation(skin_type, concern, product_format)
                except json.JSONDecodeError as e:
                    st.error(f"Could not parse AI response: {e}")
                    st.stop()
                except Exception as e:
                    st.error(f"Error generating formula: {e}")
                    st.stop()

            st.success(f"✦ AI Formula Result — {formula.get('formula_name', '')}")

            # Base formula
            st.markdown("**BASE FORMULA**")
            base = formula.get("base_formula", [])
            base_str = " · ".join([f"{i['ingredient']} {i['percentage']}%" for i in base])
            st.markdown(f"<div style='background:#f1f5f9;border-radius:8px;padding:12px;"
                        f"font-size:0.88rem;color:#334155'>{base_str}</div>",
                        unsafe_allow_html=True)

            # Active stack
            st.markdown("**ACTIVE STACK**")
            actives = formula.get("active_stack", [])
            active_str = " · ".join([f"{i['ingredient']} {i['percentage']}%" for i in actives])
            st.markdown(f"<div style='background:#f1f5f9;border-radius:8px;padding:12px;"
                        f"font-size:0.88rem;color:#334155'>{active_str}</div>",
                        unsafe_allow_html=True)

            # MOQ / Cost / Retail row
            st.markdown("")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Est. MOQ",      formula.get("est_moq", "—"))
            with m2:
                st.metric("Cost/Unit",     formula.get("cost_per_unit", "—"))
            with m3:
                st.metric("Retail",        formula.get("retail_range", "—"))

            # Key benefits
            benefits = formula.get("key_benefits", [])
            if benefits:
                st.markdown('<div class="section-label">Key Benefits</div>', unsafe_allow_html=True)
                for b in benefits:
                    st.markdown(f"✅ {b}")

            # pH & notes
            col_ph, col_notes = st.columns([1, 2])
            with col_ph:
                st.markdown('<div class="section-label">pH Range</div>', unsafe_allow_html=True)
                st.markdown(f"**{formula.get('ph_range', '—')}**")
            with col_notes:
                st.markdown('<div class="section-label">Formulation Notes</div>', unsafe_allow_html=True)
                st.info(formula.get("notes", ""))

            # Save to Lab button
            st.download_button(
                label="🧪 Save to Lab (JSON)",
                data=json.dumps(formula, indent=2),
                file_name=f"formula_{product_format.replace(' ', '_')}_{skin_type.replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True,
            )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — GLOBAL LOGISTICS / DOCUMENT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:

    st.markdown("""
        <div style="margin-bottom:6px">
            <span style="font-weight:700;font-size:1.1rem">🌍 Global Logistics Partner</span><br>
            <span style="color:#64748b;font-size:0.85rem">AI-powered document generator</span>
        </div>
    """, unsafe_allow_html=True)
    st.divider()

    with st.form("docs_form"):

        # Product details
        st.markdown('<div class="section-label">Product</div>', unsafe_allow_html=True)
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            doc_product_name = st.text_input("Product Name", placeholder="e.g. Hydra Mist Essence",
                                             key="doc_product_name")
            doc_sku          = st.text_input("SKU / Batch Code", placeholder="e.g. HYD-MS-003",
                                             key="doc_sku")
            doc_format       = st.selectbox("Product Format",
                                            ["Serum", "Moisturiser", "Cleanser",
                                             "SPF", "Eye Care", "Body Care", "Mask"],
                                            key="doc_format")
        with d_col2:
            doc_quantity   = st.number_input("Quantity (units)", min_value=1, value=1000, step=100,
                                             key="doc_quantity")
            doc_unit_price = st.number_input("Unit Price (£)", min_value=0.01, value=10.0, step=0.5,
                                             key="doc_unit_price")

        # Exporter / Consignee
        st.markdown('<div class="section-label">Parties</div>', unsafe_allow_html=True)
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            doc_exporter_name    = st.text_input("Exporter Name",
                                                 value="Lumina Beauty Ltd", key="doc_exp_name")
            doc_exporter_address = st.text_input("Exporter Address",
                                                 value="123 Beauty Lane, London, UK",
                                                 key="doc_exp_addr")
        with p_col2:
            doc_consignee_name    = st.text_input("Consignee Name",
                                                  placeholder="e.g. Dubai Beauty Dist. LLC",
                                                  key="doc_con_name")
            doc_consignee_address = st.text_input("Consignee Address",
                                                  placeholder="e.g. Dubai, UAE",
                                                  key="doc_con_addr")

        # Destination country chips
        st.markdown('<div class="section-label">Destination Country</div>', unsafe_allow_html=True)
        doc_destination = st.radio(
            label="",
            options=DESTINATION_COUNTRIES,
            horizontal=True,
            label_visibility="collapsed",
            key="doc_destination",
        )

        # Document type
        st.markdown('<div class="section-label">Document Type</div>', unsafe_allow_html=True)
        doc_type = st.radio(
            label="",
            options=DOCUMENT_TYPES,
            label_visibility="collapsed",
            key="doc_type",
        )

        # AI note
        st.markdown("""
            <div style="background:#eff6ff;border-left:3px solid #38bdf8;
                        border-radius:8px;padding:12px 16px;margin-top:12px">
                <span style="color:#0284c7;font-weight:700">⚡ AI-Powered Generation</span><br>
                <span style="color:#334155;font-size:0.82rem">
                Our AI automatically generates compliant customs and export documents
                based on destination country regulations, HS codes, and product classifications.
                </span>
            </div>
        """, unsafe_allow_html=True)

        doc_submitted = st.form_submit_button("📄 Generate Document", use_container_width=True)

    # ── Document output ───────────────────────────────────────────────────────
    if doc_submitted:
        if not doc_product_name.strip() or not doc_sku.strip():
            st.warning("Please enter a product name and SKU.")
        else:
            with st.spinner(f"Generating {doc_type}…"):
                try:
                    doc_text = generate_document(
                        product_name=doc_product_name,
                        sku=doc_sku,
                        destination_country=doc_destination,
                        document_type=doc_type,
                        quantity=int(doc_quantity),
                        unit_price=float(doc_unit_price),
                        product_format=doc_format,
                        exporter_name=doc_exporter_name,
                        exporter_address=doc_exporter_address,
                        consignee_name=doc_consignee_name,
                        consignee_address=doc_consignee_address,
                    )
                except Exception as e:
                    st.error(f"Error generating document: {e}")
                    st.stop()

            st.success(f"{doc_type} generated!")

            # Display document in a clean box
            st.markdown('<div class="section-label">Generated Document</div>',
                        unsafe_allow_html=True)
            st.markdown(
                f"<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;"
                f"padding:24px;font-family:monospace;font-size:0.82rem;"
                f"white-space:pre-wrap;line-height:1.7;color:#1e293b'>{doc_text}</div>",
                unsafe_allow_html=True,
            )

            # Download as .txt
            st.download_button(
                label=f"⬇️ Download {doc_type} (.txt)",
                data=doc_text,
                file_name=f"{doc_type.replace(' ', '_')}_{doc_sku}_{doc_destination.replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True,
            )