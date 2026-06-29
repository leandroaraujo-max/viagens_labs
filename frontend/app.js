const appSession = window.VLAuthSession?.createNamespace('portal');
const SESSION_NOME = appSession?.getNome() || localStorage.getItem('nome_usuario') || 'Colaborador';
const SESSION_TOKEN = appSession?.getToken() || localStorage.getItem('token') || '';
const SESSION_TELEFONE = '';

// ?? Loader global para chamadas ao servidor ???????????????????
let _loaderAtivo = 0;
let _loaderTimer = null;

function _mostrarLoader(msg) {
  _loaderAtivo++;
  var barra = document.getElementById('barra-loading');
  var toast = document.getElementById('toast-loading');
  if (barra) barra.classList.add('ativo');
  if (toast) {
    document.getElementById('toast-msg').textContent = msg || 'Aguardando servidor...';
    toast.style.display = 'flex';
  }
}

function _ocultarLoader() {
  _loaderAtivo = Math.max(0, _loaderAtivo - 1);
  if (_loaderAtivo === 0) {
    var barra = document.getElementById('barra-loading');
    var toast = document.getElementById('toast-loading');
    if (barra) barra.classList.remove('ativo');
    if (toast) toast.style.display = 'none';
  }
}

// ?? NOVA FUN??O RUNSERVER QUE CHAMA O FASTAPI EM PYTHON ???????????????????
async function runServer(payload, onSuccess, onError, opts) {
  var msg = (opts && opts.msgLoader) ? opts.msgLoader : null;
  _mostrarLoader(msg);

  try {
    const apiClient = window.VLApiClient?.create({
      baseUrl: '',
      getToken: () => SESSION_TOKEN,
      onUnauthorized: () => {
        alert('Sessão expirada. Faça login novamente.');
        fazerLogout();
      }
    });

    if (!apiClient) {
      throw new Error('VLApiClient não inicializado. Carregue /js/services/api-client.js antes de app.js.');
    }

    const data = await apiClient.requestJson('/api/v1/viagens/gas-proxy', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    _ocultarLoader();

    // O backend Python devolver? { sucesso: true, dados: {...} } como o seu backend GAS devolvia
    if (onSuccess) onSuccess(data);

  } catch (err) {
    _ocultarLoader();
    if (onError) onError(err);
    else console.error('[runServer failure]', payload.acao, err);
  }
}

function fazerLogout() {
  appSession?.clearAll();
  localStorage.removeItem('token');
  localStorage.removeItem('nome_usuario');
  localStorage.removeItem('perfil');
  localStorage.removeItem('username_ad');
  window.location.href = '/login.html'; // Mudaremos o nome da tela de login inicial
}
