/**
 * Viagens Labs — Relay de Aprovação + Cotação via Google Apps Script
 * ─────────────────────────────────────────────────────
 * Script ID : 1VqosNh6_Sqv8vr_210MKHp0G5anbZJDmYtIAUw1WnfbPCVWOXtwMI8lY
 *
 * Deploy    : Apps Script → Implantar → Nova implantação
 *             Tipo: App da Web | Executar como: Eu | Quem tem acesso: Qualquer pessoa
 *
 * Setup (executar UMA vez no editor):
 *   1. Execute setup()        → cria a planilha com sheets de aprovação
 *   2. Execute setupAgencia()  → adiciona sheets de cotação de agências
 *   3. Propriedades do script: GAS_SECRET = <mesmo valor do .env>
 *
 * Endpoints:
 *   GET  ?token=UUID            → Portal HTML para o aprovador (N1/N2)
 *   GET  ?agencia_token=UUID    → Portal HTML de cotação para a agência
 *   POST {action:"registrar"}   → FastAPI registra aprovação pendente
 *   POST {action:"poll"}        → FastAPI busca decisões de aprovação
 *   POST {action:"processar"}   → FastAPI marca decisão como processada
 *   POST {action:"registrar_agencia"} → FastAPI registra token de cotação
 *   POST {action:"poll_cotacoes"}     → FastAPI busca cotações submetidas
 *   POST {action:"processar_cotacao"} → FastAPI marca cotação como processada
 *   google.script.run.submitDecision(token, decisao, obs) → aprovador
 *   google.script.run.submitCotacao(token, dados)         → agência
 */

// ── Helpers ───────────────────────────────────────────────────────────────────

function _secret() {
  return PropertiesService.getScriptProperties().getProperty('GAS_SECRET') || '';
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
  var params         = (e || {}).parameter || {};
  var token          = params.token         || '';
  var agencia_token  = params.agencia_token || '';

  if (!token && !agencia_token)
    return _html(tplErro('Link inválido', 'O link não contém um token de aprovação.'));

  // ── Portal de cotação para agências ──────────────────────────────────────
  if (agencia_token) {
    try {
      var ss     = _ss();
      var shCot  = ss.getSheetByName('cotacoes_agencia');
      var shResp = ss.getSheetByName('respostas_agencia');
      if (!shCot || !shResp)
        return _html(tplErro('Configuração pendente',
          'Execute setupAgencia() no editor do script para criar as sheets necessárias.'));
      var cot = _buscarPorToken(shCot, agencia_token);
      if (!cot)
        return _html(tplErro('Token não encontrado',
          'Este link pode ter expirado ou já foi utilizado.'));
      if (new Date() > new Date(cot.expirado_em))
        return _html(tplAgenciaExpirado(cot));
      if (_buscarPorToken(shResp, agencia_token))
        return _html(tplAgenciaJaRespondido(cot));
      return _html(tplAgenciaCotacao(agencia_token, cot));
    } catch(err) {
      return _html(tplErro('Erro interno', err.message));
    }
  }

  // ── Portal de aprovação para gestores ───────────────────────────────────
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

    if (action === 'registrar')         return _json(_registrar(body));
    if (action === 'poll')               return _json(_poll());
    if (action === 'processar')          return _json(_processar(body.token));
    if (action === 'registrar_agencia')  return _json(_registrarAgencia(body));
    if (action === 'poll_cotacoes')      return _json(_pollCotacoes());
    if (action === 'processar_cotacao')  return _json(_processarCotacao(body.token));

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

// ── Setup da parte Agência (executar UMA vez após setup()) ────────────────────

function setupAgencia() {
  var ss = _ss();
  if (!ss.getSheetByName('cotacoes_agencia')) {
    var shCot = ss.insertSheet('cotacoes_agencia');
    shCot.appendRow([
      'token','protocolo','agencia_nome','tipo_servico',
      'solicitante','destino','data_ida','data_volta',
      'aereo_periodo','aereo_trecho','bagagem_extra','assento',
      'rodov_periodo','rodov_tipo','hotel_nome_pref',
      'carro_retirada_cidade','carro_devolucao_cidade',
      'observacoes_viajante','expirado_em','criado_em',
      'viajante_nome','viajante_cpf','viajante_data_nascimento','viajante_celular',
      'viajante_matricula','viajante_centro_custo','preferencia_voo','preferencia_voo_volta'
    ]);
    shCot.setFrozenRows(1);
  }
  if (!ss.getSheetByName('respostas_agencia')) {
    var shResp = ss.insertSheet('respostas_agencia');
    shResp.appendRow([
      'token','agencia_nome','protocolo',
      'aereo_companhia','aereo_numero_voo','aereo_horario_ida','aereo_horario_volta','aereo_valor',
      'hotel_nome','hotel_categoria','hotel_valor_diaria',
      'rodov_empresa','rodov_horario_ida','rodov_horario_volta','rodov_valor',
      'carro_locadora','carro_modelo','carro_valor_diaria',
      'valor_total','observacoes','respondido_em','processado'
    ]);
    shResp.setFrozenRows(1);
  }
  Logger.log('✅ Setup Agência concluído!');
  return 'Sheets cotacoes_agencia e respostas_agencia criados.';
}

// ── Lógica interna — Agência ──────────────────────────────────────────────────

function _registrarAgencia(body) {
  var token = body.token || '';
  if (!token || !body.protocolo) return { ok: false, msg: 'token e protocolo obrigatórios' };
  var shCot = _ss().getSheetByName('cotacoes_agencia');
  if (!shCot) return { ok: false, msg: 'sheet cotacoes_agencia não encontrada — execute setupAgencia()' };
  if (_buscarPorToken(shCot, token)) return { ok: true, msg: 'já registrado' };
  shCot.appendRow([
    token, body.protocolo, body.agencia_nome || '', body.tipo_servico || '',
    body.solicitante || '', body.destino || '', body.data_ida || '', body.data_volta || '',
    body.aereo_periodo || '', body.aereo_trecho || '', body.bagagem_extra ? 'Sim' : 'Não', body.assento || '',
    body.rodov_periodo || '', body.rodov_tipo || '', body.hotel_nome_pref || '',
    body.carro_retirada_cidade || '', body.carro_devolucao_cidade || '',
    body.observacoes_viajante || '', body.expirado_em || '', new Date().toISOString(),
    body.viajante_nome || '', body.viajante_cpf || '', body.viajante_data_nascimento || '',
    body.viajante_celular || '', body.viajante_matricula || '', body.viajante_centro_custo || '',
    body.preferencia_voo || '', body.preferencia_voo_volta || ''
  ]);
  return { ok: true };
}

function _pollCotacoes() {
  var ss     = _ss();
  var shResp = ss.getSheetByName('respostas_agencia');
  var shCot  = ss.getSheetByName('cotacoes_agencia');
  if (!shResp) return { ok: true, cotacoes: [] };
  var vals = shResp.getDataRange().getValues();
  if (vals.length < 2) return { ok: true, cotacoes: [] };
  var header = vals[0];
  var result = [];
  for (var i = 1; i < vals.length; i++) {
    var row = {};
    header.forEach(function(h, j) { row[h] = vals[i][j]; });
    if (String(row.processado).toLowerCase() !== 'true') {
      var cot = shCot ? _buscarPorToken(shCot, row.token) : null;
      if (cot) { row.protocolo = cot.protocolo; row.agencia_nome = cot.agencia_nome; }
      result.push(row);
    }
  }
  return { ok: true, cotacoes: result };
}

function _processarCotacao(token) {
  if (!token) return { ok: false, msg: 'token obrigatório' };
  var shResp = _ss().getSheetByName('respostas_agencia');
  if (!shResp) return { ok: false, msg: 'sheet respostas_agencia não encontrada' };
  var dec = _buscarPorToken(shResp, token);
  if (!dec) return { ok: false, msg: 'não encontrado em respostas_agencia' };
  var header = shResp.getRange(1, 1, 1, shResp.getLastColumn()).getValues()[0];
  var col    = header.indexOf('processado') + 1;
  shResp.getRange(dec._row, col).setValue('true');
  return { ok: true };
}

function submitCotacao(agencia_token, dados) {
  if (!agencia_token || !dados) return { ok: false, msg: 'token e dados obrigatórios' };
  var ss     = _ss();
  var shCot  = ss.getSheetByName('cotacoes_agencia');
  var shResp = ss.getSheetByName('respostas_agencia');
  if (!shCot || !shResp) return { ok: false, msg: 'sheets não encontradas' };
  var cot = _buscarPorToken(shCot, agencia_token);
  if (!cot)                                     return { ok: false, msg: 'token não encontrado' };
  if (new Date() > new Date(cofunction _tplBase(titulo, corpo, headExtra) {
  headExtra = headExtra || '';
  return '<!DOCTYPE html>'
    + '<html lang="pt-BR">'
    + '<head>'
    + '  <meta charset="UTF-8">'
    + '  <meta name="viewport" content="width=device-width, initial-scale=1.0">'
    + '  <title>Viagens Labs \u2014 ' + titulo + '</title>'
    + '  <script src="https://cdn.tailwindcss.com"></script>'
    + '  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    + '  <script>'
    + '    tailwind.config = {'
    + '      theme: {'
    + '        extend: {'
    + '          fontFamily: { sans: ["Inter", "sans-serif"], display: ["Outfit", "sans-serif"] },'
    + '          colors: {'
    + '            labs: {'
    + '              blue: "#0055ff",'
    + '              dark: "#0f172a",'
    + '              border: "#334155",'
    + '              accent: "#3b82f6"'
    + '            }'
    + '          }'
    + '        }'
    + '      }'
    + '    }'
    + '  </script>'
    + '  <style>'
    + '    body { font-family: "Inter", sans-serif; background-color: #0b0f19; }'
    + '    .glass-effect {'
    + '      background: rgba(15, 23, 42, 0.65);'
    + '      backdrop-filter: blur(16px);'
    + '      -webkit-backdrop-filter: blur(16px);'
    + '      border: 1px solid rgba(255, 255, 255, 0.08);'
    + '    }'
    + '    .glow-dot {'
    + '      filter: blur(100px);'
    + '      opacity: 0.15;'
    + '    }'
    + '    .spin {'
    + '      animation: spin 1s linear infinite;'
    + '    }'
    + '    @keyframes spin {'
    + '      from { transform: rotate(0deg); }'
    + '      to { transform: rotate(360deg); }'
    + '    }'
    + '  </style>'
    + headExtra
    + '</head>'
    + '<body class="min-h-screen text-slate-100 flex items-center justify-center p-4 relative overflow-x-hidden select-none selection:bg-labs-blue selection:text-white">'
    + '  <!-- Background decorative glows -->'
    + '  <div class="absolute w-[400px] h-[400px] rounded-full bg-labs-blue glow-dot -top-40 -left-40 pointer-events-none"></div>'
    + '  <div class="absolute w-[450px] h-[450px] rounded-full bg-indigo-500 glow-dot -bottom-40 -right-40 pointer-events-none"></div>'
    + '  '
    + '  <div class="glass-effect w-full max-w-2xl rounded-2xl p-6 sm:p-8 shadow-2xl relative z-10 transition-all duration-300 hover:shadow-labs-blue/5">'
    + '    <!-- Logo Header -->'
    + '    <div class="flex items-center justify-between border-b border-white/10 pb-4 mb-6">'
    + '      <div class="flex items-center gap-2">'
    + '        <span class="text-2xl text-labs-blue">\u2708\ufe0f</span>'
    + '        <span class="font-display font-extrabold text-lg tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-labs-blue via-blue-400 to-indigo-400 uppercase">Viagens Labs</span>'
    + '      </div>'
    + '      <span class="text-xs bg-white/5 border border-white/10 text-slate-400 px-2 py-0.5 rounded-full font-medium tracking-wide">Portal Externo</span>'
    + '    </div>'
    + '    '
    + corpo
    + '  </div>'
    + '</body>'
    + '</html>';
}

function tplPortal(token, d) {
  var tipos = (d.tipo_servico || '').split(',').map(function(s){ return s.trim(); })
              .filter(function(s){ return s.length > 0; }).join(' · ');

  var corpo = '<h1 class="text-2xl font-display font-bold text-white mb-1">Solicita\u00e7\u00e3o de Viagem</h1>'
    + '<p class="text-sm text-slate-400 mb-6">Protocolo <strong class="font-semibold text-slate-200 font-mono">#' + d.protocolo + '</strong>'
    + ' \u2014 Aprova\u00e7\u00e3o <span class="bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs px-2 py-0.5 rounded font-bold uppercase tracking-wider">' + d.nivel + '</span></p>'
    + ' '
    + '<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 border border-white/10 rounded-xl p-4 bg-white/5 mb-6 text-sm">'
    + '  <div><span class="text-slate-500 text-xs uppercase font-semibold tracking-wide">Viajante</span><p class="font-medium text-slate-200 mt-0.5">' + (d.viajante_nome || '\u2014') + '</p></div>'
    + '  <div><span class="text-slate-500 text-xs uppercase font-semibold tracking-wide">Destino</span><p class="font-medium text-slate-200 mt-0.5">' + (d.destino_cidade || '\u2014') + ' / ' + (d.destino_estado || '\u2014') + '</p></div>'
    + '  <div><span class="text-slate-500 text-xs uppercase font-semibold tracking-wide">Data de Ida</span><p class="font-medium text-slate-200 mt-0.5">' + (d.data_ida || '\u2014') + '</p></div>'
    + '  <div><span class="text-slate-500 text-xs uppercase font-semibold tracking-wide">Data de Volta</span><p class="font-medium text-slate-200 mt-0.5">' + (d.data_volta || '\u2014') + '</p></div>'
    + '  <div class="sm:col-span-2"><span class="text-slate-500 text-xs uppercase font-semibold tracking-wide">Servi\u00e7os Solicitados</span><p class="font-medium text-slate-200 mt-0.5">' + (tipos || '\u2014') + '</p></div>'
    + '  <div class="sm:col-span-2 border-t border-white/5 pt-3"><span class="text-slate-500 text-xs uppercase font-semibold tracking-wide">Motivo da Viagem</span><p class="font-medium text-slate-300 mt-0.5 italic leading-relaxed">' + (d.motivo || '\u2014') + '</p></div>'
    + '</div>'
    + ' '
    + '<div class="flex flex-col sm:flex-row gap-3 mb-6" id="btnsContainer">'
    + '  <button class="flex-1 bg-labs-blue hover:bg-blue-600 text-white font-bold py-3 px-4 rounded-xl shadow-lg transition-all duration-200 transform hover:-translate-y-0.5 hover:shadow-labs-blue/20 active:translate-y-0 flex items-center justify-center gap-2" id="bAp" onclick="aprovar()">\u2714\ufe0f Aprovar</button>'
    + '  <button class="flex-1 bg-transparent hover:bg-red-500/10 text-red-400 border border-red-500/30 hover:border-red-500/50 font-bold py-3 px-4 rounded-xl transition-all duration-200 flex items-center justify-center gap-2" id="bRp" onclick="mostrarObs()">\u2716\ufe0f Reprovar</button>'
    + '</div>'
    + ' '
    + '<div class="hidden border border-red-500/20 bg-red-500/5 rounded-xl p-4 mb-6 transition-all duration-300" id="obsArea">'
    + '  <label class="text-xs text-red-400 font-bold uppercase tracking-wider block mb-2">Motivo da reprova\u00e7\u00e3o *</label>'
    + '  <textarea id="obs" class="w-full bg-slate-900 border border-white/10 rounded-lg p-3 text-sm text-slate-200 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 min-h-[80px]" placeholder="Descreva o motivo da reprovação..."></textarea>'
    + '  <button class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2.5 px-4 rounded-lg mt-3 transition shadow-lg" onclick="reprovar()">Confirmar Reprova\u00e7\u00e3o</button>'
    + '</div>'
    + ' '
    + '<div id="msg"></div>'
    + ' '
    + '<script>'
    + '  var TOKEN="' + token + '";'
    + '  function mostrarObs(){'
    + '    var area = document.getElementById("obsArea");'
    + '    area.classList.remove("hidden");'
    + '    area.scrollIntoView({ behavior: "smooth" });'
    + '  }'
    + '  function _desabilitar(){'
    + '    ["bAp","bRp"].forEach(function(id){'
    + '      var b=document.getElementById(id);'
    + '      if(b)b.disabled=true;'
    + '    });'
    + '  }'
    + '  function aprovar(){'
    + '    _desabilitar();'
    + '    document.getElementById("msg").innerHTML=\'<div class="flex items-center gap-3 bg-white/5 border border-white/10 rounded-xl p-4 text-slate-300 text-sm"><svg class="spin h-5 w-5 border-2 border-labs-blue border-t-transparent rounded-full" viewBox="0 0 24 24"></svg>Processando aprova\u00e7\u00e3o\u2026</div>\';'
    + '    google.script.run'
    + '      .withSuccessHandler(function(r){_resultado(r,"APROVADO");})'
    + '      .withFailureHandler(function(e){_erro(e.message||String(e));})'
    + '      .submitDecision(TOKEN,"APROVADO","");'
    + '  }'
    + '  function reprovar(){'
    + '    var obs=document.getElementById("obs").value.trim();'
    + '    if(!obs){'
    + '      alert("Por favor, preencha o motivo da reprova\u00e7\u00e3o.");'
    + '      return;'
    + '    }'
    + '    _desabilitar();'
    + '    document.getElementById("msg").innerHTML=\'<div class="flex items-center gap-3 bg-white/5 border border-white/10 rounded-xl p-4 text-slate-300 text-sm"><svg class="spin h-5 w-5 border-2 border-red-500 border-t-transparent rounded-full" viewBox="0 0 24 24"></svg>Processando reprova\u00e7\u00e3o\u2026</div>\';'
    + '    google.script.run'
    + '      .withSuccessHandler(function(r){_resultado(r,"REPROVADO");})'
    + '      .withFailureHandler(function(e){_erro(e.message||String(e));})'
    + '      .submitDecision(TOKEN,"REPROVADO",obs);'
    + '  }'
    + '  function _resultado(r,decisao){'
    + '    if(r&&r.ok){'
    + '      document.getElementById("btnsContainer").style.display="none";'
    + '      document.getElementById("obsArea").style.display="none";'
    + '      document.getElementById("msg").innerHTML=decisao==="APROVADO"'
    + '        ? \'<div class="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl p-4 text-sm font-medium">\u2714\ufe0f <strong>Aprovada com sucesso!</strong><br>Sua decis\u00e3o foi registrada. O setor de viagens ser\u00e1 notificado.</div>\''
    + '        : \'<div class="bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-xl p-4 text-sm font-medium">\u2716\ufe0f <strong>Reprovada com sucesso.</strong><br>Sua decis\u00e3o foi registrada. O solicitante ser\u00e1 notificado.</div>\';'
    + '    }else{_erro((r&&r.msg)||"Erro desconhecido");}'
    + '  }'
    + '  function _erro(msg){'
    + '    ["bAp","bRp"].forEach(function(id){'
    + '      var b=document.getElementById(id);'
    + '      if(b)b.disabled=false;'
    + '    });'
    + '    document.getElementById("msg").innerHTML=\'<div class="bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl p-4 text-sm">Erro ao processar: \'+msg+\'</div>\';'
    + '  }'
    + '<\/script>';

  return _tplBase('Aprovar Viagem', corpo);
}

function tplJaRespondido(d, pend) {
  var ok    = (d.decisao === 'APROVADO');
  var cls   = ok ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-amber-500/10 border-amber-500/20 text-amber-400';
  var icone = ok ? '\u2714\ufe0f' : '\u2716\ufe0f';
  var texto = ok ? 'aprovada' : 'reprovada';
  var corpo = '<h1 class="text-2xl font-display font-bold text-white mb-1">' + icone + ' Solicita\u00e7\u00e3o J\u00e1 ' + (ok ? 'Aprovada' : 'Reprovada') + '</h1>'
    + '<p class="text-sm text-slate-400 mb-6">Protocolo <strong class="font-semibold text-slate-200 font-mono">#' + (pend ? pend.protocolo : '') + '</strong></p>'
    + '<div class="' + cls + ' border rounded-xl p-5 text-sm font-medium leading-relaxed">'
    + '  Esta solicita\u00e7\u00e3o j\u00e1 foi <strong>' + texto + '</strong>'
    + ' em <span class="font-mono text-xs opacity-90">' + d.respondido_em + '</span>.'
    + (d.observacao ? '<br><br><span class="text-xs opacity-75 uppercase block tracking-wider font-semibold mb-0.5">Observa\u00e7\u00e3o:</span><span class="italic text-slate-300 font-normal">"' + d.observacao + '"</span>' : '')
    + '</div>';
  return _tplBase('J\u00e1 respondido', corpo);
}

function tplExpirado(d) {
  var corpo = '<h1 class="text-2xl font-display font-bold text-white mb-1">\u23f0 Link Expirado</h1>'
    + '<p class="text-sm text-slate-400 mb-6">Protocolo <strong class="font-semibold text-slate-200 font-mono">#' + d.protocolo + '</strong></p>'
    + '<div class="bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-xl p-5 text-sm font-medium leading-relaxed">'
    + '  Este link de aprova\u00e7\u00e3o expirou em <span class="font-mono text-xs opacity-90">' + d.expirado_em + '</span>.<br><br>'
    + '  Entre em contato com a equipe de viagens: <strong class="text-slate-100 font-semibold underline">viagenslabs@luizalabs.com</strong>'
    + '</div>';
  return _tplBase('Link expirado', corpo);
}

function tplErro(titulo, detalhe) {
  var corpo = '<h1 class="text-2xl font-display font-bold text-white mb-1">\u274c ' + titulo + '</h1>'
    + '<div class="bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl p-5 mt-4 text-sm font-medium leading-relaxed">'
    + '  ' + detalhe + '<br><br>'
    + '  Em caso de d\u00favidas: <strong class="text-slate-100 font-semibold underline">viagenslabs@luizalabs.com</strong>'
    + '</div>';
  return _tplBase(titulo, corpo);
}

// ── Templates HTML — Ag\u00eancia ──────────────────────────────────────────────────

function tplAgenciaCotacao(agencia_token, d) {
  var servicos = (d.tipo_servico || '').split(',').map(function(s){ return s.trim(); });
  var temAereo = servicos.indexOf('Aereo') !== -1;
  var temHosp  = servicos.indexOf('Hospedagem') !== -1;
  var temRodov = servicos.indexOf('Rodoviario') !== -1;
  var temCarro = servicos.indexOf('Carro') !== -1;

  var cardViajante = '';
  if (d.viajante_nome || d.viajante_cpf) {
    cardViajante = '<div class="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 mb-6 text-xs text-slate-300">'
      + '  <h3 class="font-display font-bold text-blue-400 text-sm mb-3 flex items-center gap-2">'
      + '    <span class="text-base">\ud83d\udc64</span> Dados do Viajante'
      + '  </h3>'
      + '  <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">'
      + (d.viajante_nome ? '    <div><span class="text-slate-500 block uppercase font-bold tracking-wide">Nome Completo</span><span class="text-slate-200 font-medium">' + d.viajante_nome + '</span></div>' : '')
      + (d.viajante_cpf ? '    <div><span class="text-slate-500 block uppercase font-bold tracking-wide">CPF</span><span class="text-slate-200 font-mono">' + d.viajante_cpf + '</span></div>' : '')
      + (d.viajante_data_nascimento ? '    <div><span class="text-slate-500 block uppercase font-bold tracking-wide">Nascimento</span><span class="text-slate-200">' + d.viajante_data_nascimento + '</span></div>' : '')
      + (d.viajante_celular ? '    <div><span class="text-slate-500 block uppercase font-bold tracking-wide">Telefone</span><span class="text-slate-200">' + d.viajante_celular + '</span></div>' : '')
      + (d.viajante_matricula ? '    <div><span class="text-slate-500 block uppercase font-bold tracking-wide">Matr\u00edcula</span><span class="text-slate-200 font-mono">' + d.viajante_matricula + '</span></div>' : '')
      + (d.viajante_centro_custo ? '    <div><span class="text-slate-500 block uppercase font-bold tracking-wide">Centro de Custo</span><span class="text-slate-200">' + d.viajante_centro_custo + '</span></div>' : '')
      + '  </div>'
      + '</div>';
  }

  var camposAereo = !temAereo ? '' :
    '<div class="border border-sky-500/20 bg-sky-500/5 rounded-xl p-4 mb-5 text-sm">'
    + '  <div class="font-display font-bold text-sky-400 text-base mb-3 flex items-center gap-1.5 border-b border-sky-500/10 pb-2">\u2708\ufe0f Passagem A\u00e9rea</div>'
    + '  <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">'
    + '    <div>'
    + '      <label class="text-xs font-medium text-slate-400">Companhia A\u00e9rea</label>'
    + '      <input id="aereo_companhia" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-400 mt-1" placeholder="Ex: LATAM">'
    + '    </div>'
    + '    <div>'
    + '      <label class="text-xs font-medium text-slate-400">N\u00ba do Voo</label>'
    + '      <input id="aereo_numero_voo" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-400 mt-1" placeholder="Ex: LA3456" value="' + (d.preferencia_voo || '') + '">'
    + '    </div>'
    + '    <div>'
    + '      <label class="text-xs font-medium text-slate-400">Hor\u00e1rio Ida</label>'
    + '      <input id="aereo_horario_ida" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-400 mt-1" placeholder="Ex: 10:30" value="' + (d.aereo_periodo || '') + '">'
    + '    </div>'
    + '    <div>'
    + '      <label class="text-xs font-medium text-slate-400">Hor\u00e1rio Volta</label>'
    + '      <input id="aereo_horario_volta" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-400 mt-1" placeholder="Ex: 18:45" value="' + (d.preferencia_voo_volta || '') + '">'
    + '    </div>'
    + '    <div>'
    + '      <label class="text-xs font-medium text-slate-400">Valor A\u00e9reo (R$)</label>'
    + '      <input id="aereo_valor" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-400 mt-1" type="number" min="0" step="0.01" placeholder="0,00">'
    + '    </div>'
    + '  </div>'
    + '</div>';

  var camposHosp = !temHosp ? '' :
    '<div class="border border-purple-500/20 bg-purple-500/5 rounded-xl p-4 mb-5 text-sm">'
    + '  <div class="font-display font-bold text-purple-400 text-base mb-3 flex items-center gap-1.5 border-b border-purple-500/10 pb-2">\ud83c\udfe8 Hospedagem</div>'
    + '  <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">'
    + '    <div class="sm:col-span-2 md:col-span-1">'
    + '      <label class="text-xs font-medium text-slate-400">Nome do Hotel</label>'
    + '      <input id="hotel_nome" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-purple-400 focus:ring-1 focus:ring-purple-400 mt-1" placeholder="Ex: Ibis Paulista" value="' + (d.hotel_nome_pref || '') + '">'
    + '    </div>'
    + '    <div>'
    + '      <label class="text-xs font-medium text-slate-400">Categoria</label>'
    + '      <input id="hotel_categoria" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-purple-400 focus:ring-1 focus:ring-purple-400 mt-1" placeholder="Ex: Superior, Executive, Standard...">'
    + '    </div>'
    + '    <div>'
    + '      <label class="text-xs font-medium text-slate-400">Valor Di\u00e1ria (R$)</label>'
    + '      <input id="hotel_valor_diaria" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-purple-400 focus:ring-1 focus:ring-purple-400 mt-1" type="number" min="0" step="0.01" placeholder="0,00">'
    + '    </div>'
    + '  </div>'
    + '</div>';

  var camposRodov = !temRodov ? '' :
    '<div class="border border-amber-500/20 bg-amber-500/5 rounded-xl p-4 mb-5 text-sm">'
    + '  <div class="font-display font-bold text-amber-400 text-base mb-3 flex items-center gap-1.5 border-b border-amber-500/10 pb-2">\ud83d\ude8c Transporte Rodovi\u00e1rio</div>'
    + '  <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">'
    + '    <div>'
    + '      <label class="text-xs font-medium text-slate-400">Empresa</label>'
    + '      <input id="rodov_empresa" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400 mt-1" placeholder="Ex: Cometa" value="' + (d.rodov_tipo || '') + '">'
    + '    </div>'
    + '    <div>'
    + '      <label class="text-xs font-medium text-slate-400">Hor\u00e1rio Ida</label>'
    + '      <input id="rodov_horario_ida" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400 mt-1" placeholder="Ex: 22:00" value="' + (d.rodov_periodo || '') + '">'
    + '    </div>'
    + '    <div>'
    + '      <label class="text-xs font-medium text-slate-400">Hor\u00e1rio Volta</label>'
    + '      <input id="rodov_horario_volta" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400 mt-1" placeholder="Ex: 06:00">'
    + '    </div>'
    + '    <div>'
    + '      <label class="text-xs font-medium text-slate-400">Valor Rodovi\u00e1rio (R$)</label>'
    + '      <input id="rodov_valor" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400 mt-1" type="number" min="0" step="0.01" placeholder="0,00">'
    + '    </div>'
    + '  </div>'
    + '</div>';

  var camposCarro = !temCarro ? '' :
    '<div class="border border-emerald-500/20 bg-emerald-500/5 rounded-xl p-4 mb-5 text-sm">'
    + '  <div class="font-display font-bold text-emerald-400 text-base mb-3 flex items-center gap-1.5 border-b border-emerald-500/10 pb-2">\ud83d\ude97 Loca\u00e7\u00e3o de Carro</div>'
    + '  <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">'
    + '    <div>'
    + '      <label class="text-xs font-medium text-slate-400">Locadora</label>'
    + '      <input id="carro_locadora" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-400 focus:ring-1 focus:ring-emerald-400 mt-1" placeholder="Ex: Localiza">'
    + '    </div>'
    + '    <div>'
    + '      <label class="text-xs font-medium text-slate-400">Modelo</label>'
    + '      <input id="carro_modelo" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-400 focus:ring-1 focus:ring-emerald-400 mt-1" placeholder="Ex: HB20 ou similar">'
    + '    </div>'
    + '    <div>'
    + '      <label class="text-xs font-medium text-slate-400">Valor Di\u00e1ria (R$)</label>'
    + '      <input id="carro_valor_diaria" class="w-full bg-slate-900/80 border border-white/10 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-400 focus:ring-1 focus:ring-emerald-400 mt-1" type="number" min="0" step="0.01" placeholder="0,00">'
    + '    </div>'
    + '  </div>'
    + '</div>';

  var corpo = '<h1 class="text-2xl font-display font-bold text-white mb-1">Cota\u00e7\u00e3o de Viagem</h1>'
    + '<p class="text-sm text-slate-400 mb-6">Protocolo <strong class="font-semibold text-slate-200 font-mono">#' + (d.protocolo||'') + '</strong>'
    + ' \u2014 Ag\u00eancia <span class="bg-white/5 border border-white/10 text-slate-300 text-xs px-2 py-0.5 rounded font-bold uppercase tracking-wider">' + (d.agencia_nome||'') + '</span></p>'
    + ' '
    + cardViajante
    + ' '
    + '<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 border border-white/10 rounded-xl p-4 bg-white/5 mb-6 text-sm">'
    + '  <div><span class="text-slate-500 text-xs uppercase font-semibold tracking-wide">Destino</span><p class="font-medium text-slate-200 mt-0.5">' + (d.destino||'\u2014') + '</p></div>'
    + '  <div><span class="text-slate-500 text-xs uppercase font-semibold tracking-wide">Solicitante</span><p class="font-medium text-slate-200 mt-0.5">' + (d.solicitante||'\u2014') + '</p></div>'
    + '  <div><span class="text-slate-500 text-xs uppercase font-semibold tracking-wide">Data de Ida</span><p class="font-medium text-slate-200 mt-0.5">' + (d.data_ida||'\u2014') + '</p></div>'
    + '  <div><span class="text-slate-500 text-xs uppercase font-semibold tracking-wide">Retorno</span><p class="font-medium text-slate-200 mt-0.5">' + (d.data_volta||'\u2014') + '</p></div>'
    + (d.observacoes_viajante ? '  <div class="sm:col-span-2 border-t border-white/5 pt-3"><span class="text-slate-500 text-xs uppercase font-semibold tracking-wide">Observa\u00e7\u00f5es do Viajante</span><p class="font-medium text-slate-300 mt-0.5 italic leading-relaxed">' + d.observacoes_viajante + '</p></div>' : '')
    + '</div>'
    + ' '
    + camposAereo + camposHosp + camposRodov + camposCarro
    + ' '
    + '<div class="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 mb-5">'
    + '  <label class="text-xs font-bold text-blue-400 uppercase tracking-wider block mb-1">Valor Total da Cota\u00e7\u00e3o (R$) *</label>'
    + '  <input id="valor_total" class="w-full bg-slate-900 border border-blue-500/30 rounded-lg p-3 text-sm text-slate-200 font-bold focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400 mt-1" type="number" min="0" step="0.01" placeholder="0,00">'
    + '</div>'
    + ' '
    + '<div class="mb-6">'
    + '  <label class="text-xs font-medium text-slate-400 block mb-1">Observa\u00e7\u00f5es Adicionais</label>'
    + '  <textarea id="observacoes" class="w-full bg-slate-900 border border-white/10 rounded-lg p-3 text-sm text-slate-200 focus:outline-none focus:border-labs-blue focus:ring-1 focus:ring-labs-blue mt-1 min-h-[72px]" placeholder="Informações adicionais relevantes sobre a cotação..."></textarea>'
    + '</div>'
    + ' '
    + '<button class="w-full bg-labs-blue hover:bg-blue-600 text-white font-bold py-3 px-4 rounded-xl shadow-lg transition-all duration-200 transform hover:-translate-y-0.5 hover:shadow-labs-blue/20 active:translate-y-0 flex items-center justify-center gap-2" id="bSub" onclick="enviar()">\ud83d\udcc4 Enviar Cota\u00e7\u00e3o</button>'
    + '<div id="msg" class="mt-4"></div>'
    + ' '
    + '<script>'
    + '  var TOKEN="' + agencia_token + '";'
    + '  function _v(id){var el=document.getElementById(id);return el?el.value.trim():""}'
    + '  function _n(id){var v=_v(id);return v?parseFloat(v):null}'
    + '  function enviar(){'
    + '    var tot=_n("valor_total");'
    + '    if(!tot||tot<=0){'
    + '      document.getElementById("msg").innerHTML=\'<div class="bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl p-4 text-sm font-medium">Por favor, informe o valor total da cota\u00e7\u00e3o.</div>\';'
    + '      return;'
    + '    }'
    + '    document.getElementById("bSub").disabled=true;'
    + '    document.getElementById("msg").innerHTML=\'<div class="flex items-center gap-3 bg-white/5 border border-white/10 rounded-xl p-4 text-slate-300 text-sm"><svg class="spin h-5 w-5 border-2 border-labs-blue border-t-transparent rounded-full" viewBox="0 0 24 24"></svg>Enviando cota\u00e7\u00e3o\u2026</div>\';'
    + '    var d={'
    + '      aereo_companhia:_v("aereo_companhia"),aereo_numero_voo:_v("aereo_numero_voo"),'
    + '      aereo_horario_ida:_v("aereo_horario_ida"),aereo_horario_volta:_v("aereo_horario_volta"),'
    + '      aereo_valor:_n("aereo_valor"),'
    + '      hotel_nome:_v("hotel_nome"),hotel_categoria:_v("hotel_categoria"),'
    + '      hotel_valor_diaria:_n("hotel_valor_diaria"),'
    + '      rodov_empresa:_v("rodov_empresa"),rodov_horario_ida:_v("rodov_horario_ida"),'
    + '      rodov_horario_volta:_v("rodov_horario_volta"),rodov_valor:_n("rodov_valor"),'
    + '      carro_locadora:_v("carro_locadora"),carro_modelo:_v("carro_modelo"),'
    + '      carro_valor_diaria:_n("carro_valor_diaria"),'
    + '      valor_total:tot,observacoes:_v("observacoes")'
    + '    };'
    + '    google.script.run'
    + '      .withSuccessHandler(function(r){'
    + '        if(r&&r.ok){'
    + '          document.getElementById("bSub").style.display="none";'
    + '          document.getElementById("msg").innerHTML=\'<div class="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl p-4 text-sm font-medium">\u2714\ufe0f <strong>Cota\u00e7\u00e3o enviada com sucesso!</strong><br>Obrigado! O Setor de Viagens analisar\u00e1 e entrar\u00e1 em contato.</div>\';'
    + '        }else{_erro((r&&r.msg)||"Erro ao enviar cota\u00e7\u00e3o");}'
    + '      })'
    + '      .withFailureHandler(function(e){_erro(e.message||String(e));})'
    + '      .submitCotacao(TOKEN,d);'
    + '  }'
    + '  function _erro(msg){'
    + '    document.getElementById("bSub").disabled=false;'
    + '    document.getElementById("msg").innerHTML=\'<div class="bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl p-4 text-sm">Erro ao enviar: \'+msg+\'</div>\';'
    + '  }'
    + '<\/script>';

  return _tplBase('Cota\u00e7\u00e3o de Viagem', corpo);
}

function tplAgenciaJaRespondido(d) {
  var corpo = '<h1 class="text-2xl font-display font-bold text-white mb-1">\u2714\ufe0f Cota\u00e7\u00e3o J\u00e1 Enviada</h1>'
    + '<p class="text-sm text-slate-400 mb-6">Protocolo <strong class="font-semibold text-slate-200 font-mono">#' + (d.protocolo||'') + '</strong></p>'
    + '<div class="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl p-5 text-sm font-medium leading-relaxed">'
    + '  A cota\u00e7\u00e3o para este protocolo j\u00e1 foi registrada e processada.<br><br>'
    + '  O Setor de Viagens est\u00e1 analisando e entrar\u00e1 em contato em breve.'
    + '</div>';
  return _tplBase('J\u00e1 respondido', corpo);
}

function tplAgenciaExpirado(d) {
  var corpo = '<h1 class="text-2xl font-display font-bold text-white mb-1">\u23f0 Link Expirado</h1>'
    + '<p class="text-sm text-slate-400 mb-6">Protocolo <strong class="font-semibold text-slate-200 font-mono">#' + (d.protocolo||'') + '</strong></p>'
    + '<div class="bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-xl p-5 text-sm font-medium leading-relaxed">'
    + '  Este link de cota\u00e7\u00e3o expirou.<br><br>'
    + '  Entre em contato com o Setor de Viagens: <strong class="text-slate-100 font-semibold underline">viagenslabs@luizalabs.com</strong>'
    + '</div>';
  return _tplBase('Link expirado', corpo);
}
