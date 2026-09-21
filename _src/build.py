"""Gera o site vidadiariaapp.com a partir de modelos + textos por idioma.

Uso (a partir da raiz do repositório do site):
    python _src/build.py

Os textos próprios do site estão em _src/i18n/<idioma>.json. O que já existe na app
(nomes dos módulos, perguntas frequentes, vídeo de apresentação) é lido diretamente
do repositório da app, para o site nunca ficar desatualizado em relação a ela — por isso
APP_DIR tem de apontar para a pasta `app` do projeto.

A pasta _src começa com "_", por isso o GitHub Pages (Jekyll) não a publica.
Os Termos e a Privacidade também são gerados aqui, a partir do texto em
_src/legal/<idioma>/. Em português continuam nos endereços de sempre, /termos/ e
/privacidade/, porque é para lá que a app aponta — não mudar esses dois endereços.
"""
import html
import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
APP_DIR = Path('C:/Users/Eduardo/Desktop/Claude Code/app')
DOMAIN = 'https://vidadiariaapp.com'

# Ordem da grelha e ícones: iguais aos da tela inicial da app (app/lib/modules.ts).
MODULES = [
    ('meuDia', 'today-outline'),
    ('saude', 'fitness-outline'),
    ('financas', 'wallet-outline'),
    ('listaCompras', 'cart-outline'),
    ('contas', 'receipt-outline'),
    ('agenda', 'calendar-outline'),
    ('entretenimento', 'film-outline'),
    ('notasEscolares', 'school-outline'),
    ('veiculoPessoal', 'car-outline'),
]
FAQ_COUNT = 23

# Submódulos com texto próprio (janela ao clicar), na ordem e com os ícones das telas da
# app (ver app/app/modules/saude/index.tsx). Os nomes vêm da app: health.hub.<chave>.
SUBMODULES = {
    'saude': [
        ('dailyLog', 'scale-outline'),
        ('exams', 'flask-outline'),
        ('vaccines', 'medkit-outline'),
        ('hydration', 'water-outline'),
        ('bloodPressure', 'pulse-outline'),
        ('sleep', 'moon-outline'),
        ('medications', 'medical-outline'),
    ],
}
SUBMODULE_NAMES = {'saude': lambda app, k: app['health']['hub'][k]}

# Endereço de cada página de módulo (iguais em todos os idiomas: /pt/modules/health/ ...).
MODULE_SLUGS = {
    'meuDia': 'my-day',
    'saude': 'health',
    'financas': 'expenses',
    'listaCompras': 'groceries',
    'contas': 'bills',
    'agenda': 'schedule',
    'entretenimento': 'entertainment',
    'notasEscolares': 'school',
    'veiculoPessoal': 'vehicle',
}

esc = lambda s: html.escape(s, quote=True)


def asset(path):
    """Endereço de um ficheiro de /assets com marca de versão (resumo do conteúdo).
    Sem isso, o navegador reaproveita a versão antiga guardada em cache e as mudanças de
    estilo ou do leitor não aparecem para quem já tinha visitado o site."""
    import hashlib
    digest = hashlib.sha1((SITE / path.lstrip('/')).read_bytes()).hexdigest()[:10]
    return f'{path}?v={digest}'


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def site_languages():
    return sorted(p.stem for p in (SITE / '_src' / 'i18n').glob('*.json'))


def video_id(key, lang):
    """ID do vídeo daquele módulo (ou 'welcome') no idioma, lido da tabela da app."""
    src = (APP_DIR / 'lib' / 'module-videos.ts').read_text(encoding='utf-8')
    row = re.search(rf"^\s*{key}: \{{(.*?)\}},", src, re.M).group(1)
    m = re.search(rf"\b{lang}: '([^']*)'", row)
    return m.group(1) if m and m.group(1) else None


def welcome_video_id(lang):
    return video_id('welcome', lang)


def player_html(video, title, play_label):
    """Leitor igual ao da app — ver assets/player.js."""
    return f"""
  <div class="player" data-video="{video}">
    <div class="player-frame"><div class="player-slot"></div></div>
    <div class="player-head">
      <img src="/assets/mascot.png" alt="" width="36" height="36" />
      <span><strong>{esc(title)}</strong><span>Vida Diária App</span></span>
    </div>
    <div class="player-click"></div>
    <div class="player-progress"><span></span></div>
    <button class="player-poster" type="button" aria-label="{esc(play_label)}">
      <img src="/assets/mascot-blue.png" alt="" />
      <span class="player-play"><ion-icon name="play" aria-hidden="true"></ion-icon></span>
    </button>
  </div>
  <script src="{asset('/assets/player.js')}" defer></script>"""


def legal_links(lang):
    # Em português ficam os endereços de sempre, para onde a app aponta.
    if lang == 'pt':
        return '/termos/', '/privacidade/'
    return f'/{lang}/terms/', f'/{lang}/privacy/'


def name_html(text):
    """Nome de módulo: permite quebrar a linha depois da barra ("Ausgaben/Verbrauch"),
    senão o nome inteiro conta como uma só palavra e passa da largura do telemóvel."""
    return esc(text).replace('/', '/<wbr>')


def paragraphs(text):
    """Converte o texto da app (com quebras de linha) em parágrafos HTML."""
    blocks = [b.strip() for b in text.split('\n') if b.strip()]
    return ''.join(f'<p>{esc(b)}</p>' for b in blocks)


def page(lang, s, langs, current, title, body, path_suffix, alt_paths=None):
    terms, privacy = legal_links(lang)
    href_for = (lambda l: alt_paths[l]) if alt_paths else (lambda l: f'/{l}/{path_suffix}')
    switch = ''.join(
        f'<a href="{href_for(l)}" hreflang="{l}"'
        f'{" aria-current=\"true\"" if l == lang else ""}>{l.upper()}</a>'
        for l in langs
    )
    alternates = ''.join(
        f'<link rel="alternate" hreflang="{l}" href="{DOMAIN}{href_for(l)}" />' for l in langs
    )
    nav_items = [('home', ''), ('faq', 'faq/'), ('support', 'support/')]
    nav = ''.join(
        f'<a href="/{lang}/{href}"{" aria-current=\"page\"" if key == current else ""}>{esc(s["nav"][key])}</a>'
        for key, href in nav_items
    )
    full_title = f'{title} — Vida Diária' if current != 'home' else 'Vida Diária'
    return f"""<!doctype html>
<html lang="{s['html_lang']}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(s['meta_description'])}" />
<link rel="icon" href="/assets/icon.png" />
{alternates}
<link rel="stylesheet" href="{asset('/assets/site.css')}" />
<script type="module" src="https://unpkg.com/ionicons@7.1.0/dist/ionicons/ionicons.esm.js"></script>
</head>
<body class="page-{current}">
<header class="topbar">
  <div class="topbar-inner">
    <a class="brand" href="/{lang}/">
      <img src="/assets/mascot.png" alt="" width="40" height="40" />
      <span>Vida Diária</span>
    </a>
    {store_buttons(s, 'stores-top')}
    <nav class="nav" aria-label="{esc(s['nav']['home'])}">{nav}</nav>
    <nav class="langs" aria-label="{esc(s['nav']['language'])}">{switch}</nav>
  </div>
</header>
<main>
{body}
</main>
<footer class="footer">
  <div class="footer-inner">
    <a href="{terms}">{esc(s['footer_terms'])}</a>
    <a href="{privacy}">{esc(s['footer_privacy'])}</a>
    <a href="/{lang}/delete-account/">{esc(s['footer_delete'])}</a>
    <a href="mailto:contato@vidadiariaapp.com">contato@vidadiariaapp.com</a>
  </div>
</footer>
</body>
</html>
"""


def store_buttons(s, extra_class=''):
    def button(icon, name):
        return (
            f'<span class="store" aria-disabled="true">'
            f'<ion-icon name="{icon}" aria-hidden="true"></ion-icon>'
            f'<span class="store-text"><span class="store-soon">{esc(s["stores_soon"])}</span>'
            f'<span class="store-name">{esc(name)}</span></span></span>'
        )
    cls = f'stores {extra_class}'.strip()
    return f'<div class="{cls}">{button("logo-google-playstore", s["store_google"])}{button("logo-apple", s["store_apple"])}</div>'


def home_body(lang, s, app):
    video = welcome_video_id(lang)
    video_html = ''
    if video:
        # Mesmo leitor da app (ver assets/player.js): o nosso cabeçalho no lugar do título
        # do YouTube. Na app, o vídeo de apresentação tem o nome do app como título.
        video_html = f"""
<section class="video">
  <h2>{esc(s['video_title'])}</h2>
  {player_html(video, app['app']['name'], app['day']['watchVideoButton'])}
</section>"""
    # Mesmo arranjo da tela inicial da app: o primeiro (Meu Dia) em destaque a toda a
    # largura, os outros oito em duas colunas, na mesma ordem.
    cards = ''.join(
        f'<li class="module{" module-wide" if i == 0 else ""}"><a href="/{lang}/modules/{MODULE_SLUGS[key]}/">'
        f'<span class="chip"><ion-icon name="{icon}" aria-hidden="true"></ion-icon></span>'
        f'<span class="module-text"><strong>{name_html(app["modules"][key])}</strong><span>{esc(s["modules"][key])}</span>'
        f'<span class="module-more">{esc(s["module_labels"]["more"])} →</span></span></a></li>'
        for i, (key, icon) in enumerate(MODULES)
    )
    features = ''.join(
        f'<li><strong>{esc(f["title"])}</strong><span>{esc(f["text"])}</span></li>' for f in s['features']
    )
    return f"""
<section class="hero">
  <img class="hero-mascot" src="/assets/mascot.png" alt="DAY" width="180" height="180" />
  <div class="hero-text">
    <h1>{esc(s['hero_title'])}</h1>
    <p>{esc(s['hero_sub'])}</p>
    {store_buttons(s)}
  </div>
</section>
<div class="home-grid{' has-video' if video else ''}">
<section class="modules" id="modules">
  <h2>{esc(s['modules_title'])}</h2>
  <p class="lead">{esc(s['modules_sub'])}</p>
  <div class="module-board"><ul class="module-grid">{cards}</ul></div>
</section>
{video_html}
</div>
<section class="features">
  <ul>{features}</ul>
</section>"""


def submodules_html(lang, s, app, key):
    """Botões das telas do módulo; cada um abre uma janela com os dois parágrafos."""
    items = SUBMODULES.get(key)
    texts = s.get('submodules', {}).get(key)
    if not items or not texts:
        return ''
    labels = s['module_labels']
    name = SUBMODULE_NAMES[key]
    buttons, dialogs = [], []
    for sub, icon in items:
        t = texts[sub]
        title = name(app, sub)
        buttons.append(
            f'<li><button type="button" class="submodule-btn" data-dialog="sub-{sub}">'
            f'<span class="chip"><ion-icon name="{icon}" aria-hidden="true"></ion-icon></span>'
            f'<span>{esc(title)}</span></button></li>'
        )
        dialogs.append(f"""
<dialog id="sub-{sub}" class="submodule-dialog" aria-labelledby="sub-{sub}-title">
  <div class="submodule-dialog-head">
    <span class="chip"><ion-icon name="{icon}" aria-hidden="true"></ion-icon></span>
    <h2 id="sub-{sub}-title">{esc(title)}</h2>
    <button type="button" class="submodule-close" aria-label="{esc(labels['close'])}">
      <ion-icon name="close" aria-hidden="true"></ion-icon>
    </button>
  </div>
  <h3>{esc(labels['what'])}</h3>
  <p>{esc(t['p1'])}</p>
  <h3>{esc(labels['start'])}</h3>
  <p>{esc(t['p2'])}</p>
</dialog>""")
    return f"""
      <section class="submodules">
        <h2>{esc(labels['submodules'])}</h2>
        <p class="submodules-hint">{esc(labels['submodules_hint'])}</p>
        <ul class="submodule-grid">{''.join(buttons)}</ul>
      </section>
      {''.join(dialogs)}
      <script>
        // Abre a janela da tela escolhida; fecha no "X", no Esc ou tocando fora dela.
        document.querySelectorAll('.submodule-btn').forEach(function (btn) {{
          btn.addEventListener('click', function () {{
            document.getElementById(btn.dataset.dialog).showModal();
          }});
        }});
        document.querySelectorAll('.submodule-dialog').forEach(function (dlg) {{
          dlg.querySelector('.submodule-close').addEventListener('click', function () {{ dlg.close(); }});
          dlg.addEventListener('click', function (e) {{ if (e.target === dlg) dlg.close(); }});
        }});
      </script>"""


def module_body(lang, s, app, key):
    labels = s['module_labels']
    texts = s['module_pages'][key]
    icon = dict(MODULES)[key]
    keys = [k for k, _ in MODULES]
    i = keys.index(key)
    prev_key, next_key = keys[i - 1], keys[(i + 1) % len(keys)]
    video = video_id(key, lang)
    subs_html = submodules_html(lang, s, app, key)
    aside = f'<aside class="module-video"><h2>{esc(labels["video"])}</h2>{player_html(video, app["modules"][key], app["day"]["watchVideoButton"])}</aside>' if video else ''
    return f"""
<section class="module-page{' has-video' if video else ''}">
  <a class="back" href="/{lang}/#modules">← {esc(labels['back'])}</a>
  <div class="module-page-grid">
    <div class="module-page-text">
      <div class="module-page-title">
        <span class="chip"><ion-icon name="{icon}" aria-hidden="true"></ion-icon></span>
        <h1>{name_html(app['modules'][key])}</h1>
      </div>
      <h2>{esc(labels['what'])}</h2>
      <p>{esc(texts['p1'])}</p>
      <h2>{esc(labels['start'])}</h2>
      <p>{esc(texts['p2'])}</p>
      {subs_html}
    </div>
    {aside}
  </div>
  <nav class="module-pager">
    <a href="/{lang}/modules/{MODULE_SLUGS[prev_key]}/">← {esc(labels['prev'])}<strong>{name_html(app['modules'][prev_key])}</strong></a>
    <a class="next" href="/{lang}/modules/{MODULE_SLUGS[next_key]}/">{esc(labels['next'])} →<strong>{name_html(app['modules'][next_key])}</strong></a>
  </nav>
</section>"""


def faq_body(lang, s, app):
    items = ''.join(
        f'<details><summary>{esc(app["faq"][f"q{i}"])}</summary>{paragraphs(app["faq"][f"a{i}"])}</details>'
        for i in range(1, FAQ_COUNT + 1)
    )
    return f"""
<section class="doc"><article class="doc-card">
  <h1>{esc(s['faq_title'])}</h1>
  <p class="lead">{esc(s['faq_intro'])} <a href="/{lang}/support/">{esc(s['nav']['support'])} →</a></p>
  <div class="faq">{items}</div>
</article></section>"""


def support_body(lang, s, app):
    channels = ''.join(
        f'<li><span>{esc(c["label"])}</span><a href="mailto:{c["email"]}">{c["email"]}</a></li>' for c in s['support_channels']
    )
    return f"""
<section class="doc"><article class="doc-card">
  <h1>{esc(s['support_title'])}</h1>
  <p class="lead">{esc(s['support_intro'])} <a href="/{lang}/faq/">{esc(s['nav']['faq'])} →</a></p>
  <h2>{esc(s['support_channels_title'])}</h2>
  <ul class="channels">{channels}</ul>
  <h2>{esc(s['support_in_app_title'])}</h2>
  <p>{esc(s['support_in_app_text'])}</p>
  <h2>{esc(s['support_password_title'])}</h2>
  <p>{esc(s['support_password_text'])}</p>
  <h2>{esc(s['support_delete_title'])}</h2>
  <p>{esc(s['support_delete_text'])} <a href="/{lang}/delete-account/">{esc(s['footer_delete'])} →</a></p>
</article></section>"""


def delete_body(lang, s, app):
    email = 'privacidade@vidadiariaapp.com'
    steps = ''.join(f'<li>{esc(step)}</li>' for step in s['delete_app_steps'])
    noapp = esc(s['delete_noapp_text']).replace('{email}', f'<a href="mailto:{email}">{email}</a>')
    _, privacy = legal_links(lang)
    what = esc(s['delete_what_text']).replace(
        esc(s['footer_privacy']), f'<a href="{privacy}">{esc(s["footer_privacy"])}</a>'
    )
    return f"""
<section class="doc"><article class="doc-card">
  <h1>{esc(s['delete_title'])}</h1>
  <p class="lead">{esc(s['delete_intro'])}</p>
  <h2>{esc(s['delete_app_title'])}</h2>
  <ol class="steps">{steps}</ol>
  <p class="note">{esc(s['delete_app_note'])}</p>
  <h2>{esc(s['delete_noapp_title'])}</h2>
  <p>{noapp}</p>
  <h2>{esc(s['delete_what_title'])}</h2>
  <p>{what}</p>
</article></section>"""


LEGAL_PAGES = [('termos', 'terms'), ('privacidade', 'privacy')]


def legal_path(lang, pt_name, slug):
    # Em português, os endereços de sempre (a app aponta para eles).
    return f'/{pt_name}/' if lang == 'pt' else f'/{lang}/{slug}/'


def build_legal(langs):
    """Termos e Privacidade: o texto de cada idioma vive em _src/legal/<idioma>/ e entra
    num cartão branco, com o mesmo topo e rodapé do resto do site."""
    for pt_name, slug in LEGAL_PAGES:
        available = [l for l in langs if (SITE / '_src' / 'legal' / l / f'{pt_name}.html').exists()]
        alt = {l: legal_path(l, pt_name, slug) for l in available}
        for lang in available:
            s = load_json(SITE / '_src' / 'i18n' / f'{lang}.json')
            frag = (SITE / '_src' / 'legal' / lang / f'{pt_name}.html').read_text(encoding='utf-8')
            title = s['footer_terms'] if pt_name == 'termos' else s['footer_privacy']
            body = f'<section class="doc"><article class="doc-card legal">\n{frag}</article></section>'
            out = SITE / legal_path(lang, pt_name, slug).strip('/') / 'index.html'
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(page(lang, s, available, 'legal', title, body, '', alt_paths=alt), encoding='utf-8')
        print(f'{pt_name}: {available}')


def root_redirect(langs):
    links = ''.join(f'<li><a href="/{l}/">{l.upper()}</a></li>' for l in langs)
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Vida Diária</title>
<link rel="icon" href="/assets/icon.png" />
<script>
  // Abre o site no idioma do navegador de quem visita; português se não houver versão.
  (function () {{
    var available = {json.dumps(langs)};
    var wanted = (navigator.languages || [navigator.language || 'pt']).map(function (l) {{ return l.slice(0, 2).toLowerCase(); }});
    var pick = wanted.find(function (l) {{ return available.indexOf(l) !== -1; }}) || 'pt';
    location.replace('/' + pick + '/');
  }})();
</script>
</head>
<body>
<noscript><ul>{links}</ul></noscript>
</body>
</html>
"""


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    langs = site_languages()
    pages = [('home', '', home_body), ('faq', 'faq/', faq_body), ('support', 'support/', support_body),
             ('delete', 'delete-account/', delete_body)]
    for lang in langs:
        s = load_json(SITE / '_src' / 'i18n' / f'{lang}.json')
        app = load_json(APP_DIR / 'locales' / f'{lang}.json')
        titles = {'home': 'Vida Diária', 'faq': s['faq_title'], 'support': s['support_title'], 'delete': s['delete_title']}
        for key, suffix, body_fn in pages:
            out = SITE / lang / suffix / 'index.html'
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(page(lang, s, langs, key, titles[key], body_fn(lang, s, app), suffix), encoding='utf-8')
        for key, _ in MODULES:
            suffix = f'modules/{MODULE_SLUGS[key]}/'
            out = SITE / lang / suffix / 'index.html'
            out.parent.mkdir(parents=True, exist_ok=True)
            body = module_body(lang, s, app, key)
            out.write_text(page(lang, s, langs, 'module', app['modules'][key], body, suffix), encoding='utf-8')
        print(f'{lang}: {len(pages)} páginas + {len(MODULES)} de módulos')
    build_legal(langs)
    (SITE / 'index.html').write_text(root_redirect(langs), encoding='utf-8')
    print('raiz: redireciona para', langs)


if __name__ == '__main__':
    main()
