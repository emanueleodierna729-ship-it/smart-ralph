#!/usr/bin/env python3
"""
Promo Slide Generator
Genera slide promozionali per Facebook e Instagram.

INSTALLAZIONE (prima volta):
    pip install streamlit Pillow

AVVIO:
    streamlit run promo_slide_generator.py
"""

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import io
import os
import zipfile
from datetime import datetime
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# CARTELLE
# ══════════════════════════════════════════════════════════════════════════════

MEMORY_DIR = Path("memory_images")
SLIDES_DIR = Path("generated_slides")
MEMORY_DIR.mkdir(exist_ok=True)
SLIDES_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# COSTANTI
# ══════════════════════════════════════════════════════════════════════════════

SOCIAL_FORMATS = {
    "Instagram Quadrato (1080x1080)": (1080, 1080),
    "Instagram / Facebook Story (1080x1920)": (1080, 1920),
    "Facebook Post (1200x630)": (1200, 630),
    "Facebook Cover (851x315)": (851, 315),
}

OVERLAY_PRESETS = {
    "Nessuno":           (0,   0,   0,   0),
    "Scuro leggero":     (0,   0,   0,  80),
    "Scuro medio":       (0,   0,   0, 140),
    "Scuro forte":       (0,   0,   0, 200),
    "Sfumatura blu":     (0,  50, 120, 130),
    "Sfumatura viola":   (80,  0, 120, 130),
    "Sfumatura arancio": (200, 80,  0, 110),
    "Bianco leggero":    (255,255,255,  70),
}

MEM_POSITIONS = {
    "Alto destra":    "top_right",
    "Alto sinistra":  "top_left",
    "Basso destra":   "bottom_right",
    "Basso sinistra": "bottom_left",
    "Centro alto":    "top_center",
    "Centro basso":   "bottom_center",
}

# ══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def load_font_safe(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/verdanab.ttf",
            "C:/Windows/Fonts/trebucbd.ttf",
        ]
        if bold else
        [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/verdana.ttf",
            "C:/Windows/Fonts/trebuc.ttf",
        ]
    )
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, int(size))
            except Exception:
                continue
    try:
        return ImageFont.load_default(size=int(size))
    except Exception:
        return ImageFont.load_default()


def load_memory_images_from_disk() -> dict:
    """Legge immagini dalla cartella memoria. NON le modifica mai."""
    images = {}
    for pattern in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        for f in sorted(MEMORY_DIR.glob(pattern)):
            try:
                images[f.name] = Image.open(f).convert("RGBA")
            except Exception:
                pass
    return images


def save_uploaded_to_memory(uploaded_file) -> str:
    """Salva file in memoria. Non sovrascrive mai i file esistenti."""
    dest = MEMORY_DIR / uploaded_file.name
    if dest.exists():
        stem, ext = dest.stem, dest.suffix
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = MEMORY_DIR / f"{stem}_{ts}{ext}"
    dest.write_bytes(uploaded_file.getvalue())
    return dest.name


def fit_cover(img: Image.Image, w: int, h: int) -> Image.Image:
    """Ridimensiona e ritaglia al centro per coprire l'area (cover)."""
    ratio = max(w / img.width, h / img.height)
    nw, nh = int(img.width * ratio), int(img.height * ratio)
    img = img.resize((nw, nh), Image.LANCZOS)
    x, y = (nw - w) // 2, (nh - h) // 2
    return img.crop((x, y, x + w, y + h))


def hex_to_rgb(hex_str: str) -> tuple:
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def get_text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple:
    try:
        bb = draw.textbbox((0, 0), text, font=font)
        return bb[2] - bb[0], bb[3] - bb[1]
    except AttributeError:
        return draw.textsize(text, font=font)


def place_on_canvas(canvas: Image.Image, overlay: Image.Image,
                    position: str, margin: int = 30) -> Image.Image:
    W, H = canvas.size
    ow, oh = overlay.size
    coords = {
        "top_right":     (W - ow - margin, margin),
        "top_left":      (margin, margin),
        "bottom_right":  (W - ow - margin, H - oh - margin),
        "bottom_left":   (margin, H - oh - margin),
        "top_center":    ((W - ow) // 2, margin),
        "bottom_center": ((W - ow) // 2, H - oh - margin),
        "center":        ((W - ow) // 2, (H - oh) // 2),
    }
    px, py = coords.get(position, (margin, margin))
    mask = overlay if overlay.mode == "RGBA" else None
    canvas.paste(overlay, (px, py), mask)
    return canvas


# ══════════════════════════════════════════════════════════════════════════════
# GENERAZIONE SLIDE
# ══════════════════════════════════════════════════════════════════════════════

def generate_slide(cfg: dict) -> Image.Image:
    """
    Genera una slide promozionale dal dizionario di configurazione.
    Non modifica MAI le immagini originali in memoria o di riferimento.
    Restituisce Image.Image in modalità RGB.
    """
    W, H = cfg["size"]

    # 1 — Canvas base
    canvas = Image.new("RGBA", (W, H), (*cfg.get("bg_color", (20, 20, 30)), 255))

    # 2 — Immagine di riferimento come sfondo (COPIA, mai originale)
    ref = cfg.get("reference_image")
    if ref is not None:
        ref = ref.copy().convert("RGBA")
        ref = fit_cover(ref, W, H)

        bri    = cfg.get("brightness", 1.0)
        con    = cfg.get("contrast",   1.0)
        blur_r = cfg.get("blur",       0)

        if bri != 1.0 or con != 1.0:
            rgb_tmp = ref.convert("RGB")
            if bri != 1.0:
                rgb_tmp = ImageEnhance.Brightness(rgb_tmp).enhance(bri)
            if con != 1.0:
                rgb_tmp = ImageEnhance.Contrast(rgb_tmp).enhance(con)
            r, g, b = rgb_tmp.split()
            _, _, _, a = ref.split()
            ref = Image.merge("RGBA", (r, g, b, a))

        if blur_r > 0:
            ref = ref.filter(ImageFilter.GaussianBlur(radius=blur_r))

        canvas = Image.alpha_composite(canvas, ref)

    # 3 — Overlay colore
    ov = cfg.get("overlay_rgba", (0, 0, 0, 0))
    if ov[3] > 0:
        canvas = Image.alpha_composite(canvas, Image.new("RGBA", (W, H), ov))

    # 4 — Immagini dalla memoria (COPIA, mai originali)
    for mem_img_orig, position, size in cfg.get("memory_items", []):
        mem = mem_img_orig.copy().convert("RGBA")
        mem.thumbnail((size, size), Image.LANCZOS)
        canvas = place_on_canvas(canvas, mem, position, margin=30)

    # 5 — Testi
    draw = ImageDraw.Draw(canvas)

    title_text = cfg.get("title",    "").strip()
    sub_text   = cfg.get("subtitle", "").strip()
    cta_text   = cfg.get("cta",      "").strip()

    title_font = load_font_safe(cfg.get("title_size",    80), bold=True)
    sub_font   = load_font_safe(cfg.get("subtitle_size", 44), bold=False)
    cta_font   = load_font_safe(cfg.get("cta_size",      52), bold=True)

    t_col = (*hex_to_rgb(cfg.get("title_color",    "#FFFFFF")), 255)
    s_col = (*hex_to_rgb(cfg.get("subtitle_color", "#DDDDDD")), 255)
    c_col = (*hex_to_rgb(cfg.get("cta_color",      "#FFD700")), 255)

    v_pos   = cfg.get("text_position",  "bottom")
    h_align = cfg.get("text_align",     "center")
    text_bg = cfg.get("text_background", False)
    pad     = 60
    spacing = 22

    lines = []
    if title_text:
        tw, th = get_text_size(draw, title_text, title_font)
        lines.append((title_text, title_font, t_col, tw, th))
    if sub_text:
        sw, sh = get_text_size(draw, sub_text, sub_font)
        lines.append((sub_text, sub_font, s_col, sw, sh))
    if cta_text:
        cw, ch = get_text_size(draw, cta_text, cta_font)
        lines.append((cta_text, cta_font, c_col, cw, ch))

    if lines:
        total_h = sum(l[4] for l in lines) + spacing * (len(lines) - 1)

        if v_pos == "top":
            y = pad
        elif v_pos == "center":
            y = (H - total_h) // 2
        else:
            y = H - total_h - pad

        for ltext, lfont, lcol, lw, lh in lines:
            if h_align == "left":
                lx = pad
            elif h_align == "right":
                lx = W - lw - pad
            else:
                lx = (W - lw) // 2

            if text_bg:
                rp = 15
                draw.rectangle(
                    [lx - rp, y - rp // 2, lx + lw + rp, y + lh + rp // 2],
                    fill=(0, 0, 0, 160),
                )

            sh_off = max(2, lh // 18)
            draw.text((lx + sh_off, y + sh_off), ltext, font=lfont, fill=(0, 0, 0, 170))
            draw.text((lx, y), ltext, font=lfont, fill=lcol)
            y += lh + spacing

    return canvas.convert("RGB")


# ══════════════════════════════════════════════════════════════════════════════
# EXPORT
# ══════════════════════════════════════════════════════════════════════════════

def to_jpeg_bytes(img: Image.Image, quality: int = 92) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def to_pdf_bytes(images: list) -> bytes:
    if not images:
        return b""
    buf = io.BytesIO()
    rgbs = [img.convert("RGB") for img in images]
    rgbs[0].save(buf, format="PDF", save_all=True, append_images=rgbs[1:], resolution=150)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# UI — CONFIG PAGINA
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Promo Slide Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# UI — SIDEBAR (MEMORIA)
# ══════════════════════════════════════════════════════════════════════════════

def sidebar_memory() -> dict:
    st.sidebar.header("Immagini in Memoria")
    st.sidebar.caption("Caricate una volta, disponibili sempre. Non vengono mai modificate.")

    with st.sidebar.expander("Aggiungi immagini alla memoria", expanded=False):
        new_files = st.file_uploader(
            "Scegli immagini",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key="mem_uploader",
        )
        if new_files and st.button("Salva in memoria"):
            for f in new_files:
                saved = save_uploaded_to_memory(f)
                st.success(f"Salvata: {saved}")
            st.rerun()

    mem = load_memory_images_from_disk()

    if mem:
        st.sidebar.caption(f"{len(mem)} immagine/i disponibile/i")
        cols = st.sidebar.columns(2)
        for i, (name, img) in enumerate(mem.items()):
            thumb = img.copy()
            thumb.thumbnail((110, 110), Image.LANCZOS)
            label = name if len(name) <= 14 else name[:12] + "..."
            cols[i % 2].image(thumb, caption=label, use_container_width=True)
    else:
        st.sidebar.info("Nessuna immagine in memoria.\nCaricane con il pulsante sopra.")

    return mem


# ══════════════════════════════════════════════════════════════════════════════
# UI — TAB CREA SLIDE
# ══════════════════════════════════════════════════════════════════════════════

def render_create_tab(mem: dict):
    st.header("Crea Slide Promozionale")

    left, right = st.columns([1, 1], gap="large")

    # ── COLONNA SINISTRA ─────────────────────────────────────────────────────
    with left:
        st.subheader("Immagine di riferimento (sfondo)")
        ref_file = st.file_uploader(
            "Carica immagine di sfondo",
            type=["png", "jpg", "jpeg", "webp"],
            key="ref_uploader",
        )
        ref_img = None
        if ref_file:
            ref_img = Image.open(ref_file).convert("RGBA")
            preview = ref_img.copy()
            preview.thumbnail((420, 320), Image.LANCZOS)
            st.image(preview, caption="Immagine di riferimento caricata", use_container_width=True)

        st.subheader("Formato social media")
        fmt_label  = st.selectbox("Formato", list(SOCIAL_FORMATS.keys()))
        slide_size = SOCIAL_FORMATS[fmt_label]
        st.caption(f"Dimensioni output: {slide_size[0]} x {slide_size[1]} px")

        st.subheader("Regolazioni sfondo")
        bg_color_hex = "#1a1a2e"
        brightness = contrast = 1.0
        blur = 0

        if ref_img:
            c1, c2, c3 = st.columns(3)
            brightness = c1.slider("Luminosita", 0.3, 2.0, 1.0, 0.05)
            contrast   = c2.slider("Contrasto",  0.3, 2.0, 1.0, 0.05)
            blur       = c3.slider("Sfocatura",  0, 20, 0)
        else:
            bg_color_hex = st.color_picker("Colore sfondo (nessuna immagine)", "#1a1a2e")

        st.subheader("Overlay colore")
        ov_label = st.selectbox("Tipo overlay", list(OVERLAY_PRESETS.keys()))
        ov_rgba  = list(OVERLAY_PRESETS[ov_label])
        if ov_rgba[3] > 0:
            ov_rgba[3] = st.slider("Intensita overlay", 0, 255, ov_rgba[3])
        ov_rgba = tuple(ov_rgba)

    # ── COLONNA DESTRA ───────────────────────────────────────────────────────
    with right:
        st.subheader("Elementi dalla memoria")
        mem_items = []

        if mem:
            for name, img in mem.items():
                with st.expander(f"{name}", expanded=False):
                    c1, c2, c3 = st.columns([1, 2, 2])
                    thumb = img.copy()
                    thumb.thumbnail((80, 80), Image.LANCZOS)
                    c1.image(thumb, use_container_width=True)
                    use_it = c2.checkbox("Includi nella slide", key=f"use_{name}")
                    if use_it:
                        pos_label = c3.selectbox(
                            "Posizione", list(MEM_POSITIONS.keys()), key=f"pos_{name}"
                        )
                        item_size = st.slider(
                            f"Dimensione px ({name})", 50, 600, 200, 10, key=f"sz_{name}"
                        )
                        mem_items.append((img, MEM_POSITIONS[pos_label], item_size))
        else:
            st.info("Nessuna immagine in memoria.\nCaricane dalla barra laterale sinistra.")

        st.subheader("Testi promozionali")

        title_text = st.text_input("Titolo principale", placeholder="Es: Offerta Speciale")
        c1, c2 = st.columns(2)
        title_size  = c1.slider("Dimensione titolo", 20, 160, 80)
        title_color = c2.color_picker("Colore titolo", "#FFFFFF", key="kc_title")

        sub_text = st.text_input("Sottotitolo", placeholder="Es: Solo per oggi, -50%")
        c1, c2 = st.columns(2)
        sub_size  = c1.slider("Dimensione sottotitolo", 15, 100, 44)
        sub_color = c2.color_picker("Colore sottotitolo", "#DDDDDD", key="kc_sub")

        cta_text = st.text_input("Call to Action (CTA)", placeholder="Es: Acquista ora!")
        c1, c2 = st.columns(2)
        cta_size  = c1.slider("Dimensione CTA", 15, 120, 52)
        cta_color = c2.color_picker("Colore CTA", "#FFD700", key="kc_cta")

        c1, c2 = st.columns(2)
        v_pos = c1.selectbox(
            "Posizione testi",
            ["bottom", "center", "top"],
            format_func=lambda x: {"bottom": "Basso", "center": "Centro", "top": "Alto"}[x],
        )
        h_align = c2.selectbox(
            "Allineamento testi",
            ["center", "left", "right"],
            format_func=lambda x: {"center": "Centro", "left": "Sinistra", "right": "Destra"}[x],
        )
        text_bg = st.checkbox("Sfondo scuro dietro i testi", value=False)

    # ── PULSANTE GENERA ──────────────────────────────────────────────────────
    st.divider()

    if st.button("GENERA SLIDE", type="primary", use_container_width=True):
        cfg = {
            "size":             slide_size,
            "reference_image":  ref_img,
            "bg_color":         hex_to_rgb(bg_color_hex),
            "brightness":       brightness,
            "contrast":         contrast,
            "blur":             blur,
            "overlay_rgba":     ov_rgba,
            "memory_items":     mem_items,
            "title":            title_text,
            "title_size":       title_size,
            "title_color":      title_color,
            "subtitle":         sub_text,
            "subtitle_size":    sub_size,
            "subtitle_color":   sub_color,
            "cta":              cta_text,
            "cta_size":         cta_size,
            "cta_color":        cta_color,
            "text_position":    v_pos,
            "text_align":       h_align,
            "text_background":  text_bg,
        }
        with st.spinner("Generazione in corso..."):
            slide = generate_slide(cfg)

        st.session_state["last_slide"] = slide

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = SLIDES_DIR / f"slide_{ts}.jpg"
        out_path.write_bytes(to_jpeg_bytes(slide))
        st.success(f"Slide generata e salvata: {out_path.name}")

    # ── ANTEPRIMA E DOWNLOAD ─────────────────────────────────────────────────
    if "last_slide" in st.session_state:
        slide = st.session_state["last_slide"]

        st.subheader("Anteprima")
        preview = slide.copy()
        preview.thumbnail((820, 820), Image.LANCZOS)
        st.image(preview, use_container_width=False)

        st.subheader("Download")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        c1, c2 = st.columns(2)

        c1.download_button(
            label="Scarica JPEG",
            data=to_jpeg_bytes(slide),
            file_name=f"promo_{ts}.jpg",
            mime="image/jpeg",
            use_container_width=True,
        )
        c2.download_button(
            label="Scarica PDF",
            data=to_pdf_bytes([slide]),
            file_name=f"promo_{ts}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        # Genera per tutti i formati
        st.divider()
        if st.button("Genera per TUTTI i formati social (batch)", use_container_width=True):
            cfg_base = {
                "reference_image": ref_img if ref_file else None,
                "bg_color":        hex_to_rgb(bg_color_hex),
                "brightness":      brightness,
                "contrast":        contrast,
                "blur":            blur,
                "overlay_rgba":    ov_rgba,
                "memory_items":    mem_items,
                "title":           title_text,
                "title_size":      title_size,
                "title_color":     title_color,
                "subtitle":        sub_text,
                "subtitle_size":   sub_size,
                "subtitle_color":  sub_color,
                "cta":             cta_text,
                "cta_size":        cta_size,
                "cta_color":       cta_color,
                "text_position":   v_pos,
                "text_align":      h_align,
                "text_background": text_bg,
            }
            batch_imgs = []
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

            with st.spinner("Generazione batch..."):
                for label, size in SOCIAL_FORMATS.items():
                    cfg_base["size"] = size
                    img = generate_slide(cfg_base)
                    batch_imgs.append((label, img))
                    fname = label.split("(")[0].strip().replace(" ", "_").replace("/", "_")
                    (SLIDES_DIR / f"{fname}_{ts}.jpg").write_bytes(to_jpeg_bytes(img))

            # ZIP download
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for label, img in batch_imgs:
                    fname = label.split("(")[0].strip().replace(" ", "_").replace("/", "_")
                    zf.writestr(f"{fname}.jpg", to_jpeg_bytes(img))
            st.download_button(
                "Scarica tutte come ZIP",
                data=buf.getvalue(),
                file_name=f"promo_batch_{ts}.zip",
                mime="application/zip",
                use_container_width=True,
            )

            # PDF download
            all_imgs = [img for _, img in batch_imgs]
            st.download_button(
                "Scarica tutte come PDF",
                data=to_pdf_bytes(all_imgs),
                file_name=f"promo_batch_{ts}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

            st.success(f"Batch completato: {len(batch_imgs)} slide generate")


# ══════════════════════════════════════════════════════════════════════════════
# UI — TAB GALLERIA
# ══════════════════════════════════════════════════════════════════════════════

def render_gallery_tab():
    st.header("Galleria Slide Generate")

    slides = sorted(SLIDES_DIR.glob("*.jpg"), reverse=True)
    if not slides:
        st.info("Nessuna slide ancora. Creane una dalla scheda 'Crea Slide'.")
        return

    st.caption(f"{len(slides)} slide generate in totale")

    c1, c2 = st.columns(2)

    if c1.button("Scarica tutte come ZIP", use_container_width=True):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for s in slides:
                zf.write(s, s.name)
        st.download_button(
            "Download ZIP",
            data=buf.getvalue(),
            file_name=f"slide_{datetime.now().strftime('%Y%m%d')}.zip",
            mime="application/zip",
        )

    if c2.button("Scarica tutte come PDF", use_container_width=True):
        imgs = []
        for s in slides:
            try:
                imgs.append(Image.open(s))
            except Exception:
                pass
        if imgs:
            st.download_button(
                "Download PDF",
                data=to_pdf_bytes(imgs),
                file_name=f"slide_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
            )

    st.divider()

    cols = st.columns(3)
    for i, path in enumerate(slides):
        try:
            img = Image.open(path)
            thumb = img.copy()
            thumb.thumbnail((380, 380), Image.LANCZOS)
            col = cols[i % 3]
            col.image(thumb, caption=path.name, use_container_width=True)
            col.download_button(
                "JPEG",
                data=to_jpeg_bytes(img),
                file_name=path.name,
                mime="image/jpeg",
                key=f"dl_{path.name}",
                use_container_width=True,
            )
        except Exception as e:
            cols[i % 3].warning(f"Errore: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    st.title("Promo Slide Generator")
    st.caption("Genera slide promozionali per Facebook e Instagram • Scarica in JPEG o PDF")

    mem = sidebar_memory()

    tab_create, tab_gallery = st.tabs(["Crea Slide", "Galleria"])

    with tab_create:
        render_create_tab(mem)

    with tab_gallery:
        render_gallery_tab()


if __name__ == "__main__":
    main()
