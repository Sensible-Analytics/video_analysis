from pathlib import Path
from typing import List, Dict, Optional
from slugify import slugify
from .utils import write_text_file, SLIDES_DIR
from .diagrams import DiagramSpec

REVEAL_THEME = "black"  # you can change if you like
MERMAID_THEME = "default"  # light theme


def render_slide_section(slide: Dict) -> str:
    title = slide.get("title", "")
    bullets = slide.get("bullets", [])
    notes = slide.get("notes", "")
    diagram: Optional[DiagramSpec] = slide.get("diagram")

    bullets_html = "\n".join(f"<li>{b}</li>" for b in bullets)
    notes_html = f"<aside class='notes'>{notes}</aside>" if notes else ""

    if diagram:
        mermaid_block = f"<pre class='mermaid'>\n{diagram.mermaid}\n</pre>"
    else:
        mermaid_block = "<div>No diagram</div>"

    section = f"""
<section>
  <div class="two-col">
    <div class="left">
      <h2>{title}</h2>
      <ul>{bullets_html}</ul>
      {notes_html}
    </div>
    <div class="right">
      {mermaid_block}
    </div>
  </div>
</section>
"""
    return section


def render_reveal_html(slides: List[Dict], title: str, outpath: Path):
    slide_sections = [render_slide_section(s) for s in slides]

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/reveal.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/theme/{REVEAL_THEME}.css">
  <style>
    .two-col {{
      display: flex;
      gap: 20px;
      align-items: flex-start;
    }}
    .two-col .left {{
      flex: 0 0 40%;
    }}
    .two-col .right {{
      flex: 0 0 60%;
    }}
    .mermaid {{
      font-size: 0.9rem;
    }}
  </style>
</head>
<body>
  <div class="reveal">
    <div class="slides">
      {''.join(slide_sections)}
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/reveal.js"></script>
  <script>
    Reveal.initialize({{hash:true}});
  </script>
  <script type="module">
    import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
    mermaid.initialize({{ startOnLoad: true, theme: "{MERMAID_THEME}" }});
  </script>
</body>
</html>
"""
    write_text_file(outpath, html)
    print(f"[INFO] Slides written → {outpath}")


def slides_output_path(video_id: str) -> Path:
    return SLIDES_DIR / f"{slugify(video_id)}.html"
