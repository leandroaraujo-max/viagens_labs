/**
 * ViagensLabs — Transição de página com avião vetorizado
 * Uso: chamar vlNavigate('/pagina.html') ao invés de window.location.href
 */
(function () {
  'use strict';

  var KEY = 'vl_pg_trans';

  /* ── SVG do avião comercial (vista lateral, voo da esquerda para direita) ── */
  var PLANE_SVG = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 88" fill="none">',
    /* Fuselagem principal */
    '<path d="M42,44 Q90,30 162,36 L200,36 Q222,36 234,44 Q222,52 200,52 L162,52 Q90,58 42,44Z" fill="white"/>',
    /* Cockpit azulado */
    '<path d="M200,36 L234,44 L200,52 Q216,44 200,36Z" fill="#bfdbfe"/>',
    /* Asa superior */
    '<path d="M130,37 L74,6 L80,5 L140,37Z" fill="white" opacity="0.93"/>',
    /* Asa inferior */
    '<path d="M130,51 L74,82 L80,83 L140,51Z" fill="white" opacity="0.93"/>',
    /* Motor 1 (asa superior) */
    '<rect x="76" y="8" width="28" height="8" rx="4" fill="#93c5fd" opacity="0.85"/>',
    /* Motor 2 (asa inferior) */
    '<rect x="76" y="72" width="28" height="8" rx="4" fill="#93c5fd" opacity="0.85"/>',
    /* Cauda vertical */
    '<path d="M50,44 L47,22 L52,21 L58,44Z" fill="white"/>',
    /* Estabilizador horizontal superior */
    '<path d="M54,41 L35,26 L38,25 L58,40Z" fill="white" opacity="0.88"/>',
    /* Estabilizador horizontal inferior */
    '<path d="M54,47 L35,62 L38,63 L58,48Z" fill="white" opacity="0.88"/>',
    /* Janelas */
    '<circle cx="183" cy="43" r="3" fill="#dbeafe" opacity="0.7"/>',
    '<circle cx="172" cy="43" r="3" fill="#dbeafe" opacity="0.7"/>',
    '<circle cx="161" cy="43" r="3" fill="#dbeafe" opacity="0.7"/>',
    '<circle cx="150" cy="43" r="3" fill="#dbeafe" opacity="0.6"/>',
    '<circle cx="139" cy="42" r="3" fill="#dbeafe" opacity="0.5"/>',
    /* Faixa azul na fuselagem */
    '<path d="M60,41 Q120,38 195,40 L195,43 Q120,45 60,47Z" fill="#3b82f6" opacity="0.18"/>',
    '</svg>'
  ].join('');

  /* ── Nuvens decorativas ── */
  var CLOUDS_SVG = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 100" fill="none" style="position:absolute;width:100%;height:100%;top:0;left:0;pointer-events:none;opacity:0.12">',
    '<ellipse cx="60" cy="35" rx="55" ry="18" fill="white"/>',
    '<ellipse cx="90" cy="25" rx="40" ry="16" fill="white"/>',
    '<ellipse cx="40" cy="30" rx="32" ry="13" fill="white"/>',
    '<ellipse cx="310" cy="70" rx="60" ry="20" fill="white"/>',
    '<ellipse cx="345" cy="60" rx="42" ry="17" fill="white"/>',
    '<ellipse cx="290" cy="65" rx="35" ry="14" fill="white"/>',
    '<ellipse cx="190" cy="20" rx="38" ry="12" fill="white"/>',
    '<ellipse cx="215" cy="15" rx="28" ry="11" fill="white"/>',
    '</svg>'
  ].join('');

  /* ── CSS das animações ── */
  var ANIM_CSS = [
    '@keyframes vl-plane-fly{',
    '  0%  {transform:translate(-60vw,35vh) rotate(-14deg);opacity:0}',
    '  12% {opacity:1}',
    '  50% {transform:translate(0,0) rotate(-9deg);opacity:1}',
    '  88% {opacity:1}',
    '  100%{transform:translate(60vw,-35vh) rotate(-4deg);opacity:0}',
    '}',
    '@keyframes vl-trail{',
    '  0%  {opacity:0;transform:scaleX(0) rotate(-10deg)}',
    '  25% {opacity:0.45;transform:scaleX(1) rotate(-10deg)}',
    '  75% {opacity:0.25}',
    '  100%{opacity:0}',
    '}',
    '@keyframes vl-stars{',
    '  0%  {opacity:0.3}',
    '  50% {opacity:0.7}',
    '  100%{opacity:0.3}',
    '}'
  ].join('');

  /* ── Pontos de estrela aleatórios ── */
  function buildStars() {
    var html = '<svg xmlns="http://www.w3.org/2000/svg" style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none;animation:vl-stars 3s ease-in-out infinite">';
    var positions = [
      [8,12],[15,78],[22,35],[30,55],[38,20],[45,88],[52,10],[60,65],
      [70,40],[78,85],[85,18],[92,50],[96,30],[5,60],[25,92],[55,45],
      [65,72],[80,8],[88,62],[12,48],[35,82],[48,25],[72,58],[90,35]
    ];
    for (var i = 0; i < positions.length; i++) {
      var r = (i % 3 === 0) ? 1.5 : (i % 3 === 1) ? 1 : 0.8;
      html += '<circle cx="' + positions[i][0] + '%" cy="' + positions[i][1] + '%" r="' + r + '" fill="white" opacity="' + (0.2 + (i % 5) * 0.1) + '"/>';
    }
    html += '</svg>';
    return html;
  }

  /* ── Cria o overlay de transição ── */
  function createOverlay() {
    // Inject CSS
    if (!document.getElementById('vl-trans-css')) {
      var style = document.createElement('style');
      style.id = 'vl-trans-css';
      style.textContent = ANIM_CSS;
      document.head.appendChild(style);
    }

    var el = document.createElement('div');
    el.id = 'vl-trans-overlay';
    el.style.cssText = [
      'position:fixed',
      'inset:0',
      'z-index:99999',
      'background-image:linear-gradient(135deg,rgba(15,23,42,0.97) 0%,rgba(0,45,160,0.90) 100%),url("/img/bg-aviao.jpg")',
      'background-size:cover',
      'background-position:center',
      'display:flex',
      'align-items:center',
      'justify-content:center',
      'overflow:hidden',
      'transition:opacity 0.55s ease',
      'pointer-events:none'
    ].join(';');

    el.innerHTML = [
      /* Estrelas */
      buildStars(),
      /* Nuvens */
      CLOUDS_SVG,
      /* Rastro do avião */
      '<div style="',
        'position:absolute;',
        'height:2px;',
        'width:clamp(140px,22vw,260px);',
        'background:linear-gradient(90deg,rgba(147,197,253,0),rgba(147,197,253,0.5) 35%,rgba(255,255,255,0.7));',
        'border-radius:2px;',
        'transform-origin:right center;',
        'animation:vl-trail 1.5s ease-in-out forwards;',
      '"></div>',
      /* Avião */
      '<div style="',
        'position:absolute;',
        'width:clamp(190px,22vw,300px);',
        'filter:drop-shadow(0 0 20px rgba(120,170,255,0.55));',
        'will-change:transform;',
        'backface-visibility:hidden;',
        'animation:vl-plane-fly 1.5s ease-in-out forwards;',
      '">' + PLANE_SVG + '</div>',
      /* Logo central */
      '<div style="',
        'position:relative;z-index:2;',
        'display:flex;flex-direction:column;align-items:center;gap:14px;',
        'user-select:none;',
      '">',
        '<img src="/img/luizalabs-logo.png"',
          ' style="height:46px;object-fit:contain;filter:brightness(0) invert(1)"',
          ' onerror="this.style.display=\'none\'">',
        '<div style="color:white;font-size:17px;font-weight:700;font-family:Inter,system-ui,sans-serif;letter-spacing:2px">',
          'Portal de Viagens',
        '</div>',
        '<div style="color:rgba(255,255,255,0.42);font-size:10px;font-family:Inter,system-ui,sans-serif;letter-spacing:4px;text-transform:uppercase">',
          'ViagensLabs &bull; Magalu',
        '</div>',
      '</div>'
    ].join('');

    return el;
  }

  /* ── Ao carregar a página de destino: mostrar overlay e fazer fade out ── */
  function onEntry() {
    sessionStorage.removeItem(KEY);
    var overlay = createOverlay();
    overlay.style.opacity = '1';

    function appendAndScheduleFadeOut() {
      document.body.style.overflow = 'hidden';
      document.body.appendChild(overlay);
      // Timer começa DEPOIS de appendar para garantir visibilidade real de 900ms
      setTimeout(function () {
        overlay.style.opacity = '0';
        setTimeout(function () {
          if (overlay.parentNode) overlay.remove();
          document.body.style.overflow = '';
        }, 600);
      }, 900);
    }

    if (document.body) {
      appendAndScheduleFadeOut();
    } else {
      document.addEventListener('DOMContentLoaded', appendAndScheduleFadeOut);
    }
  }

  /* ── Verificar ao carregar ── */
  if (sessionStorage.getItem(KEY)) {
    onEntry();
  }

  /* ── Navegar com animação de saída ── */
  window.vlNavigate = function (url) {
    if (window._vlNavigating) return; // evitar duplo clique
    window._vlNavigating = true;

    var overlay = createOverlay();
    overlay.style.opacity = '0';
    document.body.style.overflow = 'hidden';
    document.body.appendChild(overlay);

    // Força reflow antes de animar
    void overlay.offsetHeight;
    overlay.style.opacity = '1';

    sessionStorage.setItem(KEY, '1');
    setTimeout(function () {
      window.location.href = url;
    }, 620);
  };

})();
