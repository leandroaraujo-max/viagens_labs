/**
 * Viagens Labs — Relay de Aprovação via Google Apps Script
 * ─────────────────────────────────────────────────────────
 * Script ID : 1VqosNh6_Sqv8vr_210MKHp0G5anbZJDmYtIAUw1WnfbPCVWOXtwMI8lY
 *
 * Deploy    : Apps Script → Implantar → Nova implantação
 *             Tipo: App da Web | Executar como: Eu | Quem tem acesso: Qualquer pessoa
 *
 * Setup (executar UMA vez no editor):
 *   1. Execute setup()  → cria a planilha e registra SHEET_ID
 *   2. Arquivo → Propriedades do projeto → Propriedades do script:
 *        SECRET = <string aleatória compartilhada com o FastAPI>
 *
 * Endpoints:
 *   GET  ?token=UUID          → Portal HTML para o aprovador (celular / qualquer browser)
 *   POST {action:"registrar"} → FastAPI registra nova aprovação pendente
 *   POST {action:"poll"}      → FastAPI busca decisões não processadas
 *   POST {action:"processar"} → FastAPI marca decisão como processada
 *   (google.script.run.submitDecision) → aprovador envia APROVADO/REPROVADO
 */

// ── Helpers ───────────────────────────────────────────────────────────────────

function _secret() {
  return PropertiesService.getScriptProperties().getProperty('SECRET') || '';
}

function _ss() {
  var id = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  if (!id) throw new Error('SHEET_ID nao configurado. Execute setup() primeiro.');
  return SpreadsheetApp.openById(id);
}

function _json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function _html(content) {
  return HtmlService
    .createHtmlOutput(content)
    .setTitle('Viagens Labs — Aprovação de Viagem')
    .setSandboxMode(HtmlService.SandboxMode.IFRAME);
}

function _buscarPorToken(sheet, token) {
  var vals = sheet.getDataRange().getValues();
  if (vals.length < 2) return null;
  var header = vals[0];
  for (var i = 1; i < vals.length; i++) {
    if (String(vals[i][0]) === token) {
      var obj = {};
      header.forEach(function(h, j) { obj[h] = vals[i][j]; });
      obj._row = i + 1;
      return obj;
    }
  }
  return null;
}

// ── Setup (executar uma vez) ──────────────────────────────────────────────────

function setup() {
  var ss     = SpreadsheetApp.create('Viagens Labs — Fila de Aprovações');
  var padrao = ss.getSheets()[0];

  var shPend = ss.insertSheet('pendentes');
  shPend.appendRow([
    'token','protocolo','viajante_nome','destino_cidade','destino_estado',
    'data_ida','data_volta','tipo_servico','motivo','nivel',
    'nome_aprovador','expirado_em','criado_em'
  ]);
  shPend.setFrozenRows(1);

  var shDecis = ss.insertSheet('decisoes');
  shDecis.appendRow(['token','decisao','observacao','respondido_em','processado']);
  shDecis.setFrozenRows(1);

  try { ss.deleteSheet(padrao); } catch(_) {}

  PropertiesService.getScriptProperties().setProperty('SHEET_ID', ss.getId());

  Logger.log('✅ Setup concluído!');
  Logger.log('SHEET_ID = ' + ss.getId());
  Logger.log('Planilha: ' + ss.getUrl());
  return 'SHEET_ID = ' + ss.getId();
}

// ── doGet: portal de aprovação (navegador do aprovador) ──────────────────────

function doGet(e) {
  var token = ((e || {}).parameter || {}).token || '';
  if (!token) return _html(tplErro('Link inválido', 'O link não contém um token de aprovação.'));

  try {
    var ss    = _ss();
    var shP   = ss.getSheetByName('pendentes');
    var shD   = ss.getSheetByName('decisoes');

    var pend = _buscarPorToken(shP, token);
    if (!pend) return _html(tplErro('Token não encontrado',
      'Este link pode ter expirado ou já foi processado internamente.'));

    if (new Date() > new Date(pend.expirado_em)) return _html(tplExpirado(pend));

    var dec = _buscarPorToken(shD, token);
    if (dec) return _html(tplJaRespondido(dec, pend));

    return _html(tplPortal(token, pend));
  } catch(err) {
    return _html(tplErro('Erro interno', err.message));
  }
}

// ── doPost: integração com FastAPI (autenticado por SECRET) ──────────────────

function doPost(e) {
  try {
    var body   = JSON.parse(((e || {}).postData || {}).contents || '{}');
    var action = body.action || '';
    var secret = body.secret || '';

    if (!_secret() || secret !== _secret()) {
      return _json({ ok: false, msg: 'unauthorized' });
    }

    if (action === 'registrar') return _json(_registrar(body));
    if (action === 'poll')      return _json(_poll());
    if (action === 'processar') return _json(_processar(body.token));

    return _json({ ok: false, msg: 'action desconhecida: ' + action });
  } catch(err) {
    return _json({ ok: false, msg: err.message });
  }
}

// ── Função chamada pelo navegador via google.script.run ──────────────────────

function submitDecision(token, decisao, observacao) {
  if (!token || ['APROVADO','REPROVADO'].indexOf(decisao) === -1) {
    return { ok: false, msg: 'token e decisao (APROVADO|REPROVADO) obrigatórios' };
  }

  var ss   = _ss();
  var shP  = ss.getSheetByName('pendentes');
  var shD  = ss.getSheetByName('decisoes');

  var pend = _buscarPorToken(shP, token);
  if (!pend)                                   return { ok: false, msg: 'token não encontrado' };
  if (new Date() > new Date(pend.expirado_em)) return { ok: false, msg: 'token expirado' };
  if (_buscarPorToken(shD, token))             return { ok: true,  msg: 'já respondido' };

  shD.appendRow([token, decisao, observacao || '', new Date().toISOString(), 'false']);
  return { ok: true };
}

// ── Lógica interna ────────────────────────────────────────────────────────────

function _registrar(body) {
  var token         = body.token         || '';
  var protocolo     = body.protocolo     || '';
  var viajante_nome = body.viajante_nome || '';
  var destino_cid   = body.destino_cidade  || '';
  var destino_est   = body.destino_estado  || '';
  var data_ida      = body.data_ida        || '';
  var data_volta    = body.data_volta      || '';
  var tipo_servico  = body.tipo_servico    || '';
  var motivo        = body.motivo          || '';
  var nivel         = body.nivel           || '';
  var nome_apr      = body.nome_aprovador  || '';
  var expirado_em   = body.expirado_em     || '';

  if (!token || !protocolo) return { ok: false, msg: 'token e protocolo obrigatórios' };

  var shP = _ss().getSheetByName('pendentes');
  if (_buscarPorToken(shP, token)) return { ok: true, msg: 'já registrado' };

  shP.appendRow([
    token, protocolo, viajante_nome, destino_cid, destino_est,
    data_ida, data_volta, tipo_servico, motivo, nivel,
    nome_apr, expirado_em, new Date().toISOString()
  ]);
  return { ok: true };
}

function _poll() {
  var ss   = _ss();
  var shD  = ss.getSheetByName('decisoes');
  var shP  = ss.getSheetByName('pendentes');
  var vals = shD.getDataRange().getValues();
  if (vals.length < 2) return { ok: true, decisoes: [] };

  var header = vals[0];
  var result = [];
  for (var i = 1; i < vals.length; i++) {
    var row = {};
    header.forEach(function(h, j) { row[h] = vals[i][j]; });
    if (String(row.processado).toLowerCase() !== 'true') {
      var pend = _buscarPorToken(shP, row.token);
      if (pend) { row.protocolo = pend.protocolo; row.nivel = pend.nivel; }
      result.push(row);
    }
  }
  return { ok: true, decisoes: result };
}

function _processar(token) {
  if (!token) return { ok: false, msg: 'token obrigatório' };

  var shD = _ss().getSheetByName('decisoes');
  var dec = _buscarPorToken(shD, token);
  if (!dec) return { ok: false, msg: 'não encontrado em decisoes' };

  var header = shD.getRange(1, 1, 1, shD.getLastColumn()).getValues()[0];
  var col    = header.indexOf('processado') + 1;
  shD.getRange(dec._row, col).setValue('true');
  return { ok: true };
}

// ── CSS compartilhado ─────────────────────────────────────────────────────────

var _CSS = [
  '* { box-sizing:border-box; margin:0; padding:0; }',
  'body { font-family:Inter,sans-serif; background:#0f172a; min-height:100vh;',
  '       display:flex; align-items:center; justify-content:center; padding:16px; }',
  '.card { background:#fff; border-radius:16px; padding:28px 32px;',
  '        max-width:560px; width:100%; box-shadow:0 25px 50px rgba(0,0,0,.45); }',
  '.logo { font-size:11px; font-weight:800; color:#0055ff; letter-spacing:.12em;',
  '        text-transform:uppercase; margin-bottom:20px; }',
  'h1 { font-size:19px; font-weight:700; color:#0f172a; margin-bottom:4px; }',
  '.sub { font-size:13px; color:#64748b; margin-bottom:20px; }',
  '.row { display:flex; justify-content:space-between; align-items:flex-start;',
  '       gap:8px; padding:9px 0; border-bottom:1px solid #f1f5f9; font-size:13.5px; }',
  '.row .lbl { color:#64748b; font-weight:500; white-space:nowrap; }',
  '.row .val { color:#0f172a; font-weight:600; text-align:right; max-width:280px; }',
  '.btns { display:flex; gap:10px; margin-top:20px; }',
  '.btn { flex:1; padding:13px; border-radius:10px; font-family:inherit;',
  '       font-size:14px; font-weight:700; cursor:pointer; border:none; transition:opacity .15s; }',
  '.btn:disabled { opacity:.5; cursor:not-allowed; }',
  '.btn-ok  { background:#0055ff; color:#fff; }',
  '.btn-nok { background:#fff; color:#ef4444; border:2px solid #ef4444; }',
  '.obs-area { display:none; margin-top:14px; }',
  '.obs-area.show { display:block; }',
  '.obs-area label { font-size:12px; font-weight:600; color:#64748b; display:block; margin-bottom:6px; }',
  'textarea { width:100%; border:1.5px solid #e2e8f0; border-radius:10px; padding:11px;',
  '           font-family:inherit; font-size:13px; resize:vertical; min-height:72px; }',
  'textarea:focus { outline:none; border-color:#0055ff; }',
  '.msg { border-radius:10px; padding:14px; font-size:13px; margin-top:14px; }',
  '.msg-ok   { background:#f0fdf4; border:1.5px solid #bbf7d0; color:#15803d; }',
  '.msg-err  { background:#fef2f2; border:1.5px solid #fecaca; color:#b91c1c; }',
  '.msg-warn { background:#fffbeb; border:1.5px solid #fde68a; color:#92400e; }',
  '.spin { display:inline-block; width:14px; height:14px; border:2px solid #bbf7d0;',
  '        border-top-color:#15803d; border-radius:50%; animation:spin .7s linear infinite;',
  '        vertical-align:middle; margin-right:6px; }',
  '@keyframes spin { to { transform:rotate(360deg); } }'
].join('');

// ── Templates HTML ─────────────────────────────────────────────────────────────

function _tplBase(titulo, corpo) {
  return '<!DOCTYPE html><html lang="pt-BR"><head>'
    + '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    + '<title>Viagens Labs \u2014 ' + titulo + '</title>'
    + '<link rel="preconnect" href="https://fonts.googleapis.com">'
    + '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    + '<style>' + _CSS + '</style></head>'
    + '<body><div class="card"><div class="logo">&#9992; Viagens Labs</div>'
    + corpo
    + '</div></body></html>';
}

function tplPortal(token, d) {
  var tipos = (d.tipo_servico || '').split(',').map(function(s){ return s.trim(); })
              .filter(function(s){ return s.length > 0; }).join(' · ');

  var corpo = '<h1>Solicita\u00e7\u00e3o de Viagem</h1>'
    + '<p class="sub">Protocolo <strong>' + d.protocolo + '</strong>'
    + ' \u2014 Aprova\u00e7\u00e3o <strong>' + d.nivel + '</strong></p>'
    + '<div class="row"><span class="lbl">Viajante</span><span class="val">'   + (d.viajante_nome   || '\u2014') + '</span></div>'
    + '<div class="row"><span class="lbl">Destino</span><span class="val">'    + (d.destino_cidade  || '\u2014') + ' / ' + (d.destino_estado || '\u2014') + '</span></div>'
    + '<div class="row"><span class="lbl">Data de ida</span><span class="val">' + (d.data_ida        || '\u2014') + '</span></div>'
    + '<div class="row"><span class="lbl">Data de volta</span><span class="val">'+ (d.data_volta     || '\u2014') + '</span></div>'
    + '<div class="row"><span class="lbl">Servi\u00e7os</span><span class="val">'+ (tipos            || '\u2014') + '</span></div>'
    + '<div class="row" style="border:none"><span class="lbl">Motivo</span>'
    + '<span class="val">' + (d.motivo || '\u2014') + '</span></div>'
    + '<div class="btns">'
    + '<button class="btn btn-ok"  id="bAp" onclick="aprovar()">&#10004; Aprovar</button>'
    + '<button class="btn btn-nok" id="bRp" onclick="mostrarObs()">&#10008; Reprovar</button>'
    + '</div>'
    + '<div class="obs-area" id="obsArea">'
    + '<label>Motivo da reprova\u00e7\u00e3o</label>'
    + '<textarea id="obs" placeholder="Descreva o motivo..."></textarea>'
    + '<button class="btn btn-nok" style="width:100%;margin-top:10px" onclick="reprovar()">Confirmar Reprova\u00e7\u00e3o</button>'
    + '</div>'
    + '<div id="msg"></div>'
    + '<script>'
    + 'var TOKEN="' + token + '";'
    + 'function mostrarObs(){document.getElementById("obsArea").classList.add("show");}'
    + 'function _desabilitar(){["bAp","bRp"].forEach(function(id){var b=document.getElementById(id);if(b)b.disabled=true;});}'
    + 'function aprovar(){'
    + '  _desabilitar();'
    + '  document.getElementById("msg").innerHTML=\'<div class="msg msg-ok"><span class="spin"></span>Processando\u2026</div>\';'
    + '  google.script.run'
    + '    .withSuccessHandler(function(r){_resultado(r,"APROVADO");})'
    + '    .withFailureHandler(function(e){_erro(e.message||String(e));})'
    + '    .submitDecision(TOKEN,"APROVADO","");'
    + '}'
    + 'function reprovar(){'
    + '  var obs=document.getElementById("obs").value.trim();'
    + '  _desabilitar();'
    + '  document.getElementById("msg").innerHTML=\'<div class="msg msg-ok"><span class="spin"></span>Processando\u2026</div>\';'
    + '  google.script.run'
    + '    .withSuccessHandler(function(r){_resultado(r,"REPROVADO");})'
    + '    .withFailureHandler(function(e){_erro(e.message||String(e));})'
    + '    .submitDecision(TOKEN,"REPROVADO",obs);'
    + '}'
    + 'function _resultado(r,decisao){'
    + '  if(r&&r.ok){'
    + '    document.querySelector(".btns").style.display="none";'
    + '    document.getElementById("obsArea").style.display="none";'
    + '    document.getElementById("msg").innerHTML=decisao==="APROVADO"'
    + '      ?\'<div class="msg msg-ok"><strong>&#10004; Aprovado com sucesso!</strong><br>Sua decis\u00e3o foi registrada. O setor de viagens ser\u00e1 notificado.</div>\''
    + '      :\'<div class="msg msg-warn"><strong>&#10008; Reprovado.</strong><br>Sua decis\u00e3o foi registrada. O solicitante ser\u00e1 notificado.</div>\';'
    + '  }else{_erro((r&&r.msg)||"Erro desconhecido");}'
    + '}'
    + 'function _erro(msg){'
    + '  ["bAp","bRp"].forEach(function(id){var b=document.getElementById(id);if(b)b.disabled=false;});'
    + '  document.getElementById("msg").innerHTML=\'<div class="msg msg-err">Erro: \'+msg+\'</div>\';'
    + '}'
    + '<\/script>';

  return _tplBase('Aprovar Viagem', corpo);
}

function tplJaRespondido(d, pend) {
  var ok    = (d.decisao === 'APROVADO');
  var cls   = ok ? 'msg-ok' : 'msg-warn';
  var icone = ok ? '&#10004;' : '&#10008;';
  var texto = ok ? 'aprovada' : 'reprovada';
  var corpo = '<h1>' + icone + ' J\u00e1 ' + (ok ? 'aprovado' : 'reprovado') + '</h1>'
    + '<p class="sub">Protocolo <strong>' + (pend ? pend.protocolo : '') + '</strong></p>'
    + '<p class="msg ' + cls + '" style="margin-top:12px">'
    + 'Esta solicita\u00e7\u00e3o j\u00e1 foi <strong>' + texto + '</strong>'
    + ' em <strong>' + d.respondido_em + '</strong>.'
    + (d.observacao ? '<br><br>Observa\u00e7\u00e3o: ' + d.observacao : '')
    + '</p>';
  return _tplBase('J\u00e1 respondido', corpo);
}

function tplExpirado(d) {
  var corpo = '<h1>&#9200; Link expirado</h1>'
    + '<p class="sub">Protocolo <strong>' + d.protocolo + '</strong></p>'
    + '<p class="msg msg-warn" style="margin-top:12px">'
    + 'Este link expirou em <strong>' + d.expirado_em + '</strong>.<br>'
    + 'Entre em contato com a equipe de viagens: <strong>viagenslabs@luizalabs.com</strong>'
    + '</p>';
  return _tplBase('Link expirado', corpo);
}

function tplErro(titulo, detalhe) {
  var corpo = '<h1>&#10060; ' + titulo + '</h1>'
    + '<p class="msg msg-err" style="margin-top:12px">'
    + detalhe + '<br><br>'
    + 'Em caso de d\u00favidas: <strong>viagenslabs@luizalabs.com</strong>'
    + '</p>';
  return _tplBase(titulo, corpo);
}
