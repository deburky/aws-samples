import marimo

__generated_with = "0.13.13"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    from pathlib import Path as _Path
    from dotenv import load_dotenv as _load_dotenv
    import base64 as _b64
    _load_dotenv(_Path(__file__).parent.parent / ".env")
    _logo_path = _Path(__file__).parent.parent / "unnamed.png"
    logo_src = (
        "data:image/png;base64," + _b64.b64encode(_logo_path.read_bytes()).decode()
        if _logo_path.exists() else ""
    )
    return (logo_src,)


@app.cell(hide_code=True)
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo, logo_src):
    _logo_html = f'<img src="{logo_src}" style="height:48px;width:auto;display:block;margin-bottom:12px;" alt="logo" />' if logo_src else ""
    mo.Html(f"""
<style>
  .rc-hero {{ color: #1f2937; margin: 0 0 24px; overflow: hidden; }}
  .rc-hero__grid {{
    align-items: stretch; display: grid; gap: 22px;
    grid-template-columns: minmax(0, 1.4fr) minmax(220px, 0.6fr);
    padding: 30px 28px;
  }}
  @media (max-width: 760px) {{
    .rc-hero__grid {{ grid-template-columns: 1fr; padding: 24px 18px; }}
    .rc-hero h1 {{ font-size: 1.9rem !important; }}
  }}
</style>
<div class="rc-hero">
  <div class="rc-hero__grid">
    <div>
      {_logo_html}
      <h1 style="margin:0 0 10px;color:#111827;font-size:2.35rem;line-height:1.06;font-weight:850;">
        RenCode - Text2SQL Self-Service
      </h1>
      <p style="margin:0;max-width:600px;color:#374151;font-size:1.05rem;line-height:1.52;">
        Ask questions about your data in plain English. Claude generates the SQL,
        executes it against Redshift via the Data API, and returns results — no SQL knowledge required.
      </p>
      <div style="margin-top:18px;color:#475569;font-size:0.92rem;">
        Powered by <b style="color:#111827;">Claude</b> + <b style="color:#111827;">Redshift Data API</b>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;justify-content:center;gap:10px;border:1px solid rgba(148,163,184,0.35);background:rgba(255,255,255,0.62);border-radius:8px;padding:18px 16px;box-shadow:0 12px 30px rgba(148,163,184,0.13);">
      <div style="color:#64748b;font-size:0.72rem;font-weight:850;text-transform:uppercase;margin-bottom:4px;">How it works</div>
      <div style="display:flex;align-items:flex-start;gap:10px;">
        <div style="min-width:22px;height:22px;border-radius:50%;background:#dcfce7;color:#15803d;font-size:0.75rem;font-weight:800;display:flex;align-items:center;justify-content:center;">1</div>
        <div style="font-size:0.88rem;color:#374151;line-height:1.4;">Type your question in plain English</div>
      </div>
      <div style="display:flex;align-items:flex-start;gap:10px;">
        <div style="min-width:22px;height:22px;border-radius:50%;background:#dcfce7;color:#15803d;font-size:0.75rem;font-weight:800;display:flex;align-items:center;justify-content:center;">2</div>
        <div style="font-size:0.88rem;color:#374151;line-height:1.4;">Claude generates a read-only SQL query</div>
      </div>
      <div style="display:flex;align-items:flex-start;gap:10px;">
        <div style="min-width:22px;height:22px;border-radius:50%;background:#dcfce7;color:#15803d;font-size:0.75rem;font-weight:800;display:flex;align-items:center;justify-content:center;">3</div>
        <div style="font-size:0.88rem;color:#374151;line-height:1.4;">Results returned from Redshift via Data API</div>
      </div>
    </div>
  </div>
</div>
""")
    return


@app.cell(hide_code=True)
def _(mo):
    import os as _os
    _ttyd_url = _os.environ.get("TTYD_URL", "http://localhost:7681")
    mo.Html(f"""
<iframe
  id="ttyd-frame"
  src="{_ttyd_url}"
  style="width:100%;height:600px;border:none;border-radius:8px;"
  allow="keyboard"
></iframe>
<script>
  const frame = document.getElementById('ttyd-frame');
  frame.addEventListener('load', () => {{ frame.contentWindow.focus(); }});
  frame.addEventListener('click', () => {{ frame.contentWindow.focus(); }});
</script>
""")
    return


if __name__ == "__main__":
    app.run()
