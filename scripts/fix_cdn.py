"""
Script para substituir CDNs externos por bibliotecas locais no frontend.
Executar da raiz do projeto:
    python scripts/fix_cdn.py
"""
import os
import glob

# Encontra a pasta frontend de forma robusta relativa ao diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))
frontend = os.path.abspath(os.path.join(script_dir, '..', 'frontend'))

htmls = glob.glob(os.path.join(frontend, '*.html'))

replacements = [
    ('https://cdn.tailwindcss.com', '/js/lib/tailwind.browser.min.js'),
    ('https://unpkg.com/vue@3/dist/vue.global.prod.js', '/js/lib/vue.global.prod.js'),
    ('https://unpkg.com/vue@3/dist/vue.global.js', '/js/lib/vue.global.prod.js'),
]

for html_path in htmls:
    with open(html_path, encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    changed = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            changed = True
    
    if changed:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'[OK] {os.path.basename(html_path)}')
    else:
        print(f'[--] {os.path.basename(html_path)} (sem alteracoes)')
