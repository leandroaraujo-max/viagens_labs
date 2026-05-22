
// ?? Estado da sess?o (Vindo do LocalStorage do novo Login JWT) ???????????????
const SESSION_NOME  = localStorage.getItem('nome_usuario') || 'Colaborador';
const SESSION_TOKEN = localStorage.getItem('token') || '';
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
    // Roteamento inteligente: Decide para qual rota do Python mandar dependendo da "acao" do GAS
    let endpoint = '/api/v1/viagens/gas-proxy'; // Criaremos essa rota de transi??o depois
    let method = 'POST';

    const response = await fetch(endpoint, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + SESSION_TOKEN // Manda o token JWT de seguran?a
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    
    _ocultarLoader();
    
    if (!response.ok) {
        if(response.status === 401) { alert("Sess?o expirada. Fa?a login novamente."); fazerLogout(); return;}
        throw new Error(data.detail || 'Erro na comunica??o com a API Python');
    }
    
    // O backend Python devolver? { sucesso: true, dados: {...} } como o seu backend GAS devolvia
    if (onSuccess) onSuccess(data);

  } catch (err) {
    _ocultarLoader();
    if (onError) onError(err);
    else console.error('[runServer failure]', payload.acao, err);
  }
}

function fazerLogout() {
  localStorage.clear();
  window.location.href = '/login.html'; // Mudaremos o nome da tela de login inicial
}
