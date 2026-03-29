# =========================
# SECTION WITH DIMENSION
# =========================
st.subheader("AutoCAD Style Section")

import plotly.graph_objects as go

colors = ["#000000", "#3498DB", "#8E5A2B", "#F4D03F"]
text_colors = ["white", "black", "white", "black"]

fig = go.Figure()

y_base = 0
depth_labels = []

for i, r in edited.iterrows():

    t = r["D(cm)"]

    # layer block
    fig.add_trace(go.Bar(
        x=[0],
        y=[t],
        base=y_base,
        marker_color=colors[i],
        width=0.6,
        text=f"{r['Layer']}<br>{t} cm",
        textposition="inside",
        textfont=dict(color=text_colors[i], size=14),
        hoverinfo="skip"
    ))

    # dimension line
    fig.add_shape(
        type="line",
        x0=0.5, x1=0.8,
        y0=y_base, y1=y_base,
        line=dict(color="white", width=2)
    )

    fig.add_shape(
        type="line",
        x0=0.5, x1=0.8,
        y0=y_base+t, y1=y_base+t,
        line=dict(color="white", width=2)
    )

    fig.add_shape(
        type="line",
        x0=0.65, x1=0.65,
        y0=y_base, y1=y_base+t,
        line=dict(color="white", width=2, dash="dot")
    )

    # dimension text
    fig.add_annotation(
        x=0.9,
        y=y_base + t/2,
        text=f"D{i+1} = {t} cm",
        showarrow=False,
        font=dict(color="white", size=12)
    )

    y_base += t

# layout
fig.update_layout(
    height=650,
    showlegend=False,
    xaxis=dict(visible=False),
    yaxis=dict(autorange="reversed", title="Depth (cm)"),
    plot_bgcolor="#111111",
    paper_bgcolor="#111111",
    margin=dict(l=40, r=40, t=40, b=40)
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# EXPORT PDF (WITH SECTION)
# =========================
st.subheader("Export Report")

try:
    import plotly.io as pio
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    if st.button("📄 Export PDF Report"):

        # save figure image
        img_path = "section.png"
        pio.write_image(fig, img_path, width=800, height=600)

        # create pdf
        doc = SimpleDocTemplate("report.pdf")
        styles = getSampleStyleSheet()

        content = []
        content.append(Paragraph("AASHTO 1993 PAVEMENT REPORT", styles['Title']))
        content.append(Spacer(1,12))

        content.append(Paragraph("Layer Section", styles['Heading2']))
        content.append(Spacer(1,12))

        content.append(Image(img_path, width=400, height=300))

        doc.build(content)

        with open("report.pdf","rb") as f:
            st.download_button("Download PDF", f)

except:
    st.warning("Install plotly + kaleido + reportlab for PDF export")
