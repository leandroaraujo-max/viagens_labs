/**
 * ViagensLabs — Transicao de pagina com aviao vetorizado
 * Uso: vlNavigate('/pagina.html') ao inves de window.location.href
 *
 * Anti-flash: ao detectar chegada (sessionStorage key), injeta body::before
 * escuro no <head> ANTES que qualquer conteudo do body seja pintado.
 * Isso elimina o flash branco/cinza entre a pagina de origem e o overlay.
 */
(function () {
  'use strict';

  var KEY = 'vl_pg_trans';

  /* ─── Anti-flash imediato ──────────────────────────────────────────────────
     Executado sincronamente no <head>, antes de <body> existir.
     O body::before cobre todo o viewport assim que o browser cria o <body>,
     impedindo qualquer frame com bg-labs-gray / bg-aviao / conteudo visivel. */
  if (sessionStorage.getItem(KEY)) {
    var cover = document.createElement('style');
    cover.id = 'vl-cover';
    cover.textContent = 'body::before{'
      + 'content:"";position:fixed;inset:0;'
      + 'background:linear-gradient(135deg,#0f172a 0%,#001e7a 100%);'
      + 'z-index:99998;pointer-events:none}';
    document.head.appendChild(cover);
  }

  var PLANE = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 88" fill="none">'
    + '<path d="M42,44 Q90,30 162,36 L200,36 Q222,36 234,44 Q222,52 200,52 L162,52 Q90,58 42,44Z" fill="white"/>'
    + '<path d="M200,36 L234,44 L200,52 Q216,44 200,36Z" fill="#bfdbfe"/>'
    + '<path d="M130,37 L74,6 L80,5 L140,37Z" fill="white" opacity="0.93"/>'
    + '<path d="M130,51 L74,82 L80,83 L140,51Z" fill="white" opacity="0.93"/>'
    + '<rect x="76" y="8"  width="28" height="8" rx="4" fill="#93c5fd" opacity="0.85"/>'
    + '<rect x="76" y="72" width="28" height="8" rx="4" fill="#93c5fd" opacity="0.85"/>'
    + '<path d="M50,44 L47,22 L52,21 L58,44Z" fill="white"/>'
    + '<path d="M54,41 L35,26 L38,25 L58,40Z" fill="white" opacity="0.88"/>'
    + '<path d="M54,47 L35,62 L38,63 L58,48Z" fill="white" opacity="0.88"/>'
    + '<circle cx="183" cy="43" r="3" fill="#dbeafe" opacity="0.7"/>'
    + '<circle cx="172" cy="43" r="3" fill="#dbeafe" opacity="0.7"/>'
    + '<circle cx="161" cy="43" r="3" fill="#dbeafe" opacity="0.6"/>'
    + '<circle cx="150" cy="43" r="3" fill="#dbeafe" opacity="0.5"/>'
    + '</svg>';

  var CSS = '@keyframes vl-fly{'
    + 'from{transform:translate3d(-400px,200px,0) rotate(-12deg)}'
    + 'to{transform:translate3d(calc(100vw + 200px),-200px,0) rotate(-6deg)}'
    + '}'
    + '@keyframes vl-trail{'
    + '0%{transform:scaleX(0);opacity:0}'
    + '30%{opacity:0.5}'
    + '80%{opacity:0.3}'
    + '100%{transform:scaleX(1);opacity:0}'
    + '}';

  function injectCSS() {
    if (document.getElementById('vl-css')) return;
    var s = document.createElement('style');
    s.id = 'vl-css';
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function makeOverlay() {
    injectCSS();
    var el = document.createElement('div');
    el.style.cssText = 'position:fixed;inset:0;z-index:99999'
      + ';background:linear-gradient(135deg,#0f172a 0%,#001e7a 100%)'
      + ';display:flex;align-items:center;justify-content:center'
      + ';overflow:hidden;opacity:0;transition:opacity .2s ease;pointer-events:all';

    var clouds = '<svg xmlns="http://www.w3.org/2000/svg" style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none" viewBox="0 0 1200 600" preserveAspectRatio="xMidYMid slice">'
      + '<ellipse cx="150" cy="120" rx="130" ry="40" fill="white" opacity="0.05"/>'
      + '<ellipse cx="200" cy="100" rx="90"  ry="35" fill="white" opacity="0.04"/>'
      + '<ellipse cx="900" cy="450" rx="140" ry="45" fill="white" opacity="0.05"/>'
      + '<ellipse cx="960" cy="430" rx="100" ry="38" fill="white" opacity="0.04"/>'
      + '<ellipse cx="550" cy="80"  rx="80"  ry="28" fill="white" opacity="0.04"/>'
      + '</svg>';

    var trail = '<div style="position:absolute;left:0;bottom:calc(50% - 1px);height:2px'
      + ';width:300px;transform-origin:left center;transform:scaleX(0)'
      + ';background:linear-gradient(90deg,transparent,rgba(147,197,253,0.6) 50%,rgba(255,255,255,0.8))'
      + ';border-radius:2px;animation:vl-trail 1.4s linear forwards"></div>';

    var plane = '<div style="position:absolute;bottom:calc(50% - 44px);left:0'
      + ';width:220px;will-change:transform'
      + ';filter:drop-shadow(0 0 16px rgba(100,160,255,0.6))'
      + ';animation:vl-fly 1.4s linear forwards">'
      + PLANE + '</div>';

    var logo = '<div style="position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;gap:14px;user-select:none">'
      + '<img src="/img/luizalabs-logo.png" style="height:44px;object-fit:contain;filter:brightness(0) invert(1)" onerror="this.style.display=\'none\'">'
      + '<div style="color:#fff;font:700 17px/1 Inter,system-ui,sans-serif;letter-spacing:2px">Portal de Viagens</div>'
      + '<div style="color:rgba(255,255,255,.38);font:400 10px/1 Inter,system-ui,sans-serif;letter-spacing:4px;text-transform:uppercase">ViagensLabs &bull; Magalu</div>'
      + '</div>';

    el.innerHTML = clouds + trail + plane + logo;
    return el;
  }

  function fadeIn(el) {
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        el.style.opacity = '1';
      });
    });
  }

  function onArrival() {
    sessionStorage.removeItem(KEY);
    function run() {
      var ov = makeOverlay();
      ov.style.opacity = '1';
      document.body.style.overflow = 'hidden';
      document.body.appendChild(ov);
      // Remove o body::before agora que o overlay real cobre tudo
      var c = document.getElementById('vl-cover');
      if (c) c.remove();
      setTimeout(function () {
        ov.style.opacity = '0';
        setTimeout(function () {
          if (ov.parentNode) ov.remove();
          document.body.style.overflow = '';
        }, 450);
      }, 850);
    }
    if (document.body) { run(); }
    else { document.addEventListener('DOMContentLoaded', run, { once: true }); }
  }

  if (sessionStorage.getItem(KEY)) { onArrival(); }

  window.vlNavigate = function (url) {
    if (window._vln) return;
    window._vln = true;
    var ov = makeOverlay();
    document.body.style.overflow = 'hidden';
    document.body.appendChild(ov);
    fadeIn(ov);
    sessionStorage.setItem(KEY, '1');
    setTimeout(function () { window.location.href = url; }, 480);
  };

})();
