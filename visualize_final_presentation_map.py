import os
import io
import base64
import pandas as pd
import numpy as np
import folium
import branca.colormap as cm
import matplotlib.pyplot as plt

CSV_PATH = "tashu_station_net_metrics.csv"
OUT_HTML = "tashu_presentation_map.html"


def sparkline_base64(values):
    fig, ax = plt.subplots(figsize=(2.4, 0.7), dpi=120)
    ax.plot(values, color='#2b8cbe', linewidth=1.4)
    ax.fill_between(range(len(values)), values, color='#a6bddb', alpha=0.4)
    ax.set_axis_off()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('ascii')


def load_and_clean(path):
    df = pd.read_csv(path)
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    hour_cols = [f'net_{i:02d}' for i in range(24)]
    for c in hour_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        else:
            df[c] = 0
    df = df.dropna(subset=['lat', 'lon']).reset_index(drop=True)
    return df, hour_cols


def make_map(df, hour_cols, tiles='OpenStreetMap'):
    center = [df['lat'].mean(), df['lon'].mean()]
    # folium accepts common provider names like 'OpenStreetMap' or URL templates
    m = folium.Map(location=center, zoom_start=12, tiles=tiles)

    # color by target_stock (vivid diverging -> discrete steps)
    vals = pd.to_numeric(df['target_stock'].fillna(0)).values
    vmin, vmax = float(np.nanmin(vals)), float(np.nanmax(vals))
    if vmin == vmax:
        vmin -= 1
        vmax += 1
    colors = ['#2b83ba', '#91bfdb', '#ffffbf', '#fc8d59', '#d7191c']
    colormap = cm.LinearColormap(colors, vmin=vmin, vmax=vmax)
    colormap = colormap.to_step(6)
    colormap.caption = 'Target stock (discrete bins)'
    colormap.add_to(m)

    fg_points = folium.FeatureGroup(name='Stations (target_stock)')

    for _, row in df.iterrows():
        ts = float(row.get('target_stock', 0) or 0)
        # radius scaled between 6 and 24 for visibility
        try:
            frac = (ts - vmin) / (vmax - vmin)
        except Exception:
            frac = 0
        frac = max(0.0, min(1.0, frac))
        radius = 6 + frac * 18
        color = colormap(ts)
        # sparkline from hourly nets
        vals24 = [row[c] for c in hour_cols]
        img_b64 = sparkline_base64(vals24)
        # format numbers
        try:
            mean_net = float(row.get('mean_net', 0))
        except Exception:
            mean_net = 0.0
        try:
            std_net = float(row.get('std_net', 0))
        except Exception:
            std_net = 0.0

        # badge color for mean_net
        mean_color = '#1a9850' if mean_net >= 0 else '#d73027'

        img_tag = f'<img src="data:image/png;base64,{img_b64}" style="width:240px;height:66px;display:block;margin-top:6px;border-radius:4px;"/>'

        popup_html = (
            f"<div style=\"width:360px;font-family: Arial, sans-serif;\">"
            f"<div style=\"display:flex;align-items:center;justify-content:space-between;\">"
            f"<div style=\"font-weight:700;font-size:15px\">{row.get('name','')}</div>"
            f"<div style=\"background:{mean_color};color:#fff;padding:4px 8px;border-radius:6px;font-weight:700;font-size:13px\">{mean_net:.2f}</div>"
            f"</div>"
            f"<div style=\"margin-top:6px;font-size:13px;color:#333;display:flex;justify-content:space-between;\">"
            f"<div style=\"min-width:160px;\">"
            f"<div>Station: <b>{row.get('station_key','')}</b></div>"
            f"<div>Target: <b>{int(ts)}</b></div>"
            f"<div>Initial: <b>{row.get('initial_stock','')}</b></div>"
            f"<div>Rebal: <b>{row.get('rebal_qty','')}</b></div>"
            f"</div>"
            f"<div style=\"text-align:right;min-width:120px;\">"
            f"<div style=\"font-size:12px;color:#666\">Std: {std_net:.2f}</div>"
            f"</div>"
            f"</div>"
            f"{img_tag}"
            f"</div>"
        )

        folium.CircleMarker(
            location=(row['lat'], row['lon']),
            radius=radius,
            color='#222222',
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            weight=0.9,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{row.get('name','')} — target {ts}, mean {row.get('mean_net','')}"
        ).add_to(fg_points)

    fg_points.add_to(m)

    # Add a clean title
    title_html = '''
         <div style="position: fixed; top: 10px; left: 50px; width: 380px; z-index:9999; font-size:18px; 
                     background-color: rgba(255,255,255,0.85); padding:8px; border-radius:6px;">
             <b>타슈 자전거 스테이션 — Target Stock & 24h Trend</b><br>
             <span style="font-size:12px">각 마커를 클릭하면 24시간 스파크라인이 표시됩니다.</span>
         </div>
         '''
    m.get_root().html.add_child(folium.Element(title_html))

    # add numeric legend ticks for clarity
    try:
        ticks = list(np.linspace(vmin, vmax, 6))
        tick_html = "<div style='position: fixed; bottom: 60px; left: 50px; z-index:9999; background: rgba(255,255,255,0.9); padding:8px; border-radius:6px; font-size:12px;'>"
        tick_html += "<b>Target stock</b><br>"
        for i in range(len(ticks)-1):
            c = colormap((ticks[i]+ticks[i+1])/2)
            tick_html += f"<div style='display:flex;align-items:center;margin:3px 0;'><span style='width:18px;height:12px;background:{c};border:1px solid #333;margin-right:8px;'></span> {int(round(ticks[i]))} — {int(round(ticks[i+1]))}</div>"
        tick_html += "</div>"
        m.get_root().html.add_child(folium.Element(tick_html))
    except Exception:
        pass

    folium.LayerControl(collapsed=False).add_to(m)
    return m


def main():
    cwd = os.path.abspath(os.getcwd())
    path = os.path.join(cwd, CSV_PATH)
    if not os.path.exists(path):
        print('CSV not found:', path)
        return
    print('Loading CSV from', path)
    df, hour_cols = load_and_clean(path)
    print('Loaded df rows:', len(df))
    if df.empty:
        print('No data after cleaning, aborting')
        return
    # diagnostic: write a tiny png using matplotlib to ensure backend works
    try:
        import matplotlib.pyplot as _plt
        _plt.figure(figsize=(1,1))
        _plt.plot([0,1], [0,1])
        test_img = os.path.join(cwd, 'diag_test_plot.png')
        _plt.savefig(test_img)
        _plt.close()
        print('Wrote diagnostic image', test_img)
    except Exception as e:
        print('Diagnostic image failed:', e)
    # diagnostic: list some files
    try:
        print('CWD listing:', os.listdir(cwd)[:20])
    except Exception as e:
        print('Listing failed:', e)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--tiles', type=str, default='OpenStreetMap', help='Tile provider name or URL template')
    args = parser.parse_args()
    m = make_map(df, hour_cols, tiles=args.tiles)
    out = os.path.join(cwd, OUT_HTML)
    m.save(out)
    print('Saved presentation map to', out)


if __name__ == '__main__':
    main()
