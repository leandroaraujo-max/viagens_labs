import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from app.core.config import settings

logger = logging.getLogger(__name__)

# ─── Paleta / constantes de design ────────────────────────────────────────────
_AZUL_ESCURO  = "#1e3a8a"
_AZUL_MEDIO   = "#1d4ed8"
_AZUL_CLARO   = "#dbeafe"
_VERDE        = "#166534"
_VERDE_BG     = "#dcfce7"
_VERMELHO     = "#991b1b"
_VERMELHO_BG  = "#fee2e2"
_AMARELO      = "#92400e"
_AMARELO_BG   = "#fef3c7"
_CINZA_TEXTO  = "#334155"
_CINZA_BG     = "#f8fafc"
_BORDA        = "#e2e8f0"


def _base_html(cabecalho_html: str, corpo_html: str) -> str:
    """Wrapper padrão de toda mensagem — define estrutura, fontes e rodapé."""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>ViagensLabs</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:'Segoe UI',Arial,sans-serif">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="background:#f1f5f9;padding:32px 16px">
  <tr><td align="center">

    <!-- Card principal -->
    <table role="presentation" width="600" cellpadding="0" cellspacing="0"
           style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;
                  overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.10)">

      <!-- Cabeçalho da marca -->
      <tr>
        <td style="background:{_AZUL_ESCURO};padding:20px 28px 16px">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td>
                <span style="font-size:22px;font-weight:800;color:#ffffff;letter-spacing:-.3px">
                  ✈&nbsp;Viagens
                </span><span style="font-size:22px;font-weight:300;color:#93c5fd">Labs</span>
              </td>
              <td align="right">
                <span style="font-size:11px;color:#93c5fd;letter-spacing:.5px">
                  LUIZALABS &nbsp;|&nbsp; MAGAZINE LUIZA
                </span>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- Faixa colorida do assunto -->
      {cabecalho_html}

      <!-- Corpo -->
      <tr>
        <td style="padding:28px 32px;color:{_CINZA_TEXTO};font-size:14px;line-height:1.6">
          {corpo_html}
        </td>
      </tr>

      <!-- Rodapé -->
      <tr>
        <td style="background:{_CINZA_BG};border-top:1px solid {_BORDA};
                   padding:14px 32px;text-align:center">
          <p style="margin:0;font-size:11px;color:#94a3b8;line-height:1.6">
            Luizalabs — Viagens Corporativas &nbsp;|&nbsp;
            Este é um e-mail automático, não responda.<br>
            Dúvidas: <a href="mailto:viagenslabs@luizalabs.com"
                        style="color:{_AZUL_MEDIO};text-decoration:none">viagenslabs@luizalabs.com</a>
          </p>
        </td>
      </tr>

    </table>
    <!-- /Card -->

  </td></tr>
</table>
</body>
</html>"""


def _faixa(cor_bg: str, cor_texto: str, icone: str, titulo: str, subtitulo: str = "") -> str:
    sub = f'<p style="margin:4px 0 0;font-size:13px;opacity:.85">{subtitulo}</p>' if subtitulo else ""
    return f"""
      <tr>
        <td style="background:{cor_bg};padding:18px 32px">
          <h1 style="margin:0;font-size:18px;font-weight:700;color:{cor_texto}">
            {icone}&nbsp; {titulo}
          </h1>
          {sub}
        </td>
      </tr>"""


def _tabela_dados(linhas: list[tuple]) -> str:
    """Gera tabela zebrada de dados. linhas = [(label, valor), ...]"""
    html = f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:14px;margin:20px 0">'
    for i, (label, valor) in enumerate(linhas):
        bg = _CINZA_BG if i % 2 == 0 else "#ffffff"
        html += f"""
      <tr>
        <td style="background:{bg};padding:10px 14px;border:1px solid {_BORDA};
                   font-weight:600;color:#475569;width:42%">{label}</td>
        <td style="background:{bg};padding:10px 14px;border:1px solid {_BORDA};
                   color:{_CINZA_TEXTO}">{valor}</td>
      </tr>"""
    html += "</table>"
    return html


def _botao(link: str, texto: str, cor: str = _AZUL_MEDIO) -> str:
    return f"""
      <table role="presentation" cellpadding="0" cellspacing="0" style="margin:24px auto">
        <tr>
          <td align="center" style="border-radius:8px;background:{cor}">
            <a href="{link}"
               style="display:inline-block;padding:14px 40px;color:#ffffff;
                      font-size:15px;font-weight:700;text-decoration:none;
                      border-radius:8px;letter-spacing:.2px">
              {texto}
            </a>
          </td>
        </tr>
      </table>"""


def _alerta(texto: str, cor_bg: str, cor_texto: str) -> str:
    return f"""<p style="background:{cor_bg};color:{cor_texto};border-radius:6px;
               padding:10px 14px;font-size:13px;margin:16px 0">{texto}</p>"""


# ─────────────────────────────────────────────────────────────────────────────

class EmailService:

    def __init__(self):
        self.smtp_host       = settings.SMTP_HOST
        self.smtp_port       = settings.SMTP_PORT
        self.smtp_from       = settings.SMTP_FROM
        self.from_name       = getattr(settings, "SMTP_FROM_NAME", "ViagensLabs | Luizalabs")
        self.reply_to        = getattr(settings, "SMTP_REPLY_TO", "")
        self.base_url        = settings.BASE_URL
        # URL usada nos links para agências externas (pode ser diferente — publica/VPN)
        self.base_url_agencia = getattr(settings, "BASE_URL_AGENCIA", settings.BASE_URL)
        # URL usada nos links de aprovação (N1/N2 — acessam fora da intranet, ex: celular)
        self.base_url_aprovacao = getattr(settings, "BASE_URL_APROVACAO", settings.BASE_URL)

    # ── Envio base ────────────────────────────────────────────────────────────

    def _enviar(self, para: str | list, assunto: str, html: str) -> bool:
        destinatarios = [para] if isinstance(para, str) else para
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"]  = assunto
            msg["From"]     = formataddr((self.from_name, self.smtp_from))
            msg["To"]       = ", ".join(destinatarios)
            if self.reply_to:
                msg["Reply-To"] = self.reply_to
            msg.attach(MIMEText(html, "html", "utf-8"))
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as smtp:
                smtp.sendmail(self.smtp_from, destinatarios, msg.as_string())
            logger.info(f"E-mail enviado → {destinatarios} | {assunto}")
            return True
        except Exception as e:
            logger.error(f"Falha ao enviar e-mail → {destinatarios}: {e}")
            return False

    # ── Aprovação N1 / N2 ─────────────────────────────────────────────────────

    def enviar_email_aprovacao(self, solicitacao, token) -> bool:
        nivel_label = "Aprovação N1 — Gestor Direto" if token.nivel == "N1" else "Aprovação N2 — Diretoria"
        assunto = f"[ViagensLabs] {solicitacao.protocolo} — {nivel_label} Necessária"
        link    = f"{self.base_url_aprovacao}/portal_aprovacao.html?token={token.uuid}"
        html    = self._tpl_aprovacao(solicitacao, token, link, nivel_label)
        return self._enviar(token.email_aprovador, assunto, html)

    def _tpl_aprovacao(self, solicitacao, token, link: str, nivel_label: str) -> str:
        emergencial = solicitacao.classificacao == "Emergencial"
        sla_txt     = "4 horas" if emergencial else "24 horas"
        servicos    = solicitacao.tipo_servico.replace(",", " &nbsp;·&nbsp; ")
        data_volta  = solicitacao.data_volta.strftime("%d/%m/%Y") if solicitacao.data_volta else "—"

        if emergencial:
            faixa = _faixa(_VERMELHO_BG, _VERMELHO, "⚡", f"Aprovação Necessária — {nivel_label}",
                           "Solicitação EMERGENCIAL · prazo de resposta: 4 horas")
            badge = _alerta("⚡ Esta solicitação é <strong>EMERGENCIAL</strong>. Responda em até 4 horas.", _VERMELHO_BG, _VERMELHO)
        else:
            faixa = _faixa(_AZUL_CLARO, _AZUL_ESCURO, "📋", f"Aprovação Necessária — {nivel_label}",
                           "Solicitação COMUM · prazo de resposta: 24 horas")
            badge = _alerta(f"Prazo para resposta: <strong>{sla_txt}</strong>.", _AZUL_CLARO, _AZUL_ESCURO)

        dados = _tabela_dados([
            ("Protocolo",   f'<strong style="color:{_AZUL_MEDIO}">{solicitacao.protocolo}</strong>'),
            ("Solicitante", solicitacao.solicitante_username),
            ("Viajante",    solicitacao.viajante_nome or solicitacao.solicitante_username),
            ("CPF",         solicitacao.viajante_cpf  or "—"),
            ("Cargo",       solicitacao.viajante_cargo or "—"),
            ("Filial",      solicitacao.viajante_filial or "—"),
            ("Centro de Custo", f"{solicitacao.viajante_centro_custo} (Cód.: {solicitacao.viajante_cod_centro_custo or '—'})"),
            ("Admissão",    solicitacao.viajante_data_admissao or "—"),
            ("Dt. Nascimento", solicitacao.viajante_data_nascimento or "—"),
            ("Celular",     solicitacao.viajante_celular or "—"),
            ("Origem",      solicitacao.origem_cidade or "—"),
            ("Destino",     f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Data de Ida", solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("Retorno",     data_volta),
            ("Serviços",    servicos),
            ("Motivo",      solicitacao.motivo_viagem),
        ])

        corpo = f"""
          <p style="margin:0 0 4px">Olá, <strong>{token.nome_aprovador or token.email_aprovador}</strong>,</p>
          <p style="margin:0 0 16px;color:#64748b">Uma nova solicitação de viagem aguarda sua decisão:</p>
          {dados}
          {badge}
          {_botao(link, "👆&nbsp; Visualizar e Decidir")}
          <p style="text-align:center;font-size:12px;color:#94a3b8;margin:0">
            O link expira em <strong>{sla_txt}</strong> após o envio deste e-mail.
          </p>"""

        return _base_html(faixa, corpo)

    # ── Resultado da decisão (para o solicitante) ─────────────────────────────

    def enviar_email_resultado(self, solicitacao, nivel: str, acao: str, aprovador_nome: str) -> bool:
        aprovado   = acao == "aprovar"
        label      = "APROVADA ✅" if aprovado else "REPROVADA ❌"
        assunto    = f"[ViagensLabs] {solicitacao.protocolo} — Solicitação {label}"
        email_dest = f"{solicitacao.solicitante_username}@magazineluiza.com.br"
        html       = self._tpl_resultado(solicitacao, nivel, acao, aprovador_nome)
        return self._enviar(email_dest, assunto, html)

    def _tpl_resultado(self, solicitacao, nivel: str, acao: str, aprovador_nome: str) -> str:
        aprovado = acao == "aprovar"
        data_volta = solicitacao.data_volta.strftime("%d/%m/%Y") if solicitacao.data_volta else "—"

        if aprovado:
            faixa = _faixa(_VERDE_BG, _VERDE, "✅", "Solicitação Aprovada",
                           f"Aprovação {nivel} concluída com sucesso")
            if nivel == "N1" and getattr(solicitacao, "exige_aprovacao_diretoria", False):
                proximo = _alerta("Sua solicitação avançou para <strong>Aprovação N2 (Diretoria)</strong>. Aguarde o próximo e-mail.", _AZUL_CLARO, _AZUL_ESCURO)
            else:
                proximo = _alerta("🎉 Aprovação concluída! Sua solicitação foi encaminhada à agência de viagens para cotação.", _VERDE_BG, _VERDE)
        else:
            faixa  = _faixa(_VERMELHO_BG, _VERMELHO, "❌", "Solicitação Reprovada",
                            f"Reprovação {nivel}")
            proximo = _alerta("Sua solicitação foi reprovada. Caso tenha dúvidas, entre em contato com seu gestor.", _VERMELHO_BG, _VERMELHO)

        dados = _tabela_dados([
            ("Protocolo",     f'<strong style="color:{_AZUL_MEDIO}">{solicitacao.protocolo}</strong>'),
            ("Destino",       f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Data de Ida",   solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("Retorno",       data_volta),
            ("Serviços",      solicitacao.tipo_servico.replace(",", " · ")),
            (f"Aprovador {nivel}", aprovador_nome),
        ])

        corpo = f"""
          <p style="margin:0 0 16px">Olá, <strong>{solicitacao.solicitante_username}</strong>,</p>
          <p style="margin:0 0 16px;color:#64748b">Segue o resultado da análise da sua solicitação de viagem:</p>
          {dados}
          {proximo}"""

        return _base_html(faixa, corpo)

    # ── Notificação de cotação recebida (para o solicitante) ─────────────────

    def enviar_email_criacao(self, solicitacao) -> bool:
        assunto    = f"[ViagensLabs] {solicitacao.protocolo} — Solicitação Recebida"
        email_dest = f"{solicitacao.solicitante_username}@magazineluiza.com.br"
        html       = self._tpl_criacao(solicitacao)
        return self._enviar(email_dest, assunto, html)

    def _tpl_criacao(self, solicitacao) -> str:
        data_volta = solicitacao.data_volta.strftime("%d/%m/%Y") if solicitacao.data_volta else "—"
        emergencial = solicitacao.classificacao == "Emergencial"

        faixa = _faixa(_AZUL_CLARO, _AZUL_ESCURO, "📬", "Solicitação Recebida com Sucesso",
                       f"Protocolo: {solicitacao.protocolo}")

        if emergencial:
            badge = _alerta("⚡ Classificação <strong>EMERGENCIAL</strong> — seu gestor será notificado imediatamente.", _AMARELO_BG, _AMARELO)
        else:
            badge = _alerta("Sua solicitação foi registrada e enviada ao seu gestor para aprovação.", _AZUL_CLARO, _AZUL_ESCURO)

        dados = _tabela_dados([
            ("Protocolo",      f'<strong style="color:{_AZUL_MEDIO}">{solicitacao.protocolo}</strong>'),
            ("Viajante",       solicitacao.viajante_nome or solicitacao.solicitante_username),
            ("CPF",            solicitacao.viajante_cpf  or "—"),
            ("Data Nascimento",solicitacao.viajante_data_nascimento or "—"),
            ("Celular",        solicitacao.viajante_celular or "—"),
            ("Destino",        f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Data de Ida",    solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("Retorno",        data_volta),
            ("Serviços",       solicitacao.tipo_servico.replace(",", " · ")),
            ("Classificação",  solicitacao.classificacao),
            ("Aprovador N1",   solicitacao.aprovador_n1_nome or "—"),
        ])

        corpo = f"""
          <p style="margin:0 0 16px">Olá, <strong>{solicitacao.solicitante_username}</strong>,</p>
          <p style="margin:0 0 16px;color:#64748b">
            Sua solicitação de viagem foi registrada no sistema. Guarde o protocolo abaixo para acompanhamento:
          </p>
          {dados}
          {badge}
          <p style="font-size:13px;color:#64748b;margin:16px 0 0">
            Você receberá um novo e-mail assim que houver uma atualização na sua solicitação.
          </p>"""

        return _base_html(faixa, corpo)

    # ── Notificação de cotação recebida (para o solicitante) ─────────────────

    def enviar_email_cotacao_recebida(self, solicitacao, cotacao) -> bool:
        assunto    = f"[ViagensLabs] {solicitacao.protocolo} — Cotação Recebida"
        email_dest = f"{solicitacao.solicitante_username}@magazineluiza.com.br"
        html       = self._tpl_cotacao_recebida(solicitacao, cotacao)
        return self._enviar(email_dest, assunto, html)

    def _tpl_cotacao_recebida(self, solicitacao, cotacao) -> str:
        data_volta = solicitacao.data_volta.strftime("%d/%m/%Y") if solicitacao.data_volta else "—"

        faixa = _faixa(_VERDE_BG, _VERDE, "💰", "Cotação Disponível",
                       f"A agência {cotacao.agencia_nome} enviou a cotação da sua viagem")

        linhas_cotacao = []
        servicos = [s.strip() for s in (solicitacao.tipo_servico or "").split(",")]

        if "Aereo" in servicos and cotacao.aereo_companhia:
            val = f"R$ {cotacao.aereo_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if cotacao.aereo_valor else "—"
            linhas_cotacao.append(("✈ Aéreo",
                f"{cotacao.aereo_companhia} · Voo {cotacao.aereo_numero_voo or '—'} · {val}"))
        if "Hospedagem" in servicos and cotacao.hotel_nome:
            val = f"R$ {cotacao.hotel_valor_diaria:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if cotacao.hotel_valor_diaria else "—"
            linhas_cotacao.append(("🏨 Hospedagem", f"{cotacao.hotel_nome} ({cotacao.hotel_categoria}) · {val}/diária"))
        if "Rodoviario" in servicos and cotacao.rodov_empresa:
            val = f"R$ {cotacao.rodov_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if cotacao.rodov_valor else "—"
            linhas_cotacao.append(("🚌 Rodoviário", f"{cotacao.rodov_empresa} · {val}"))
        if "Carro" in servicos and cotacao.carro_locadora:
            val = f"R$ {cotacao.carro_valor_diaria:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if cotacao.carro_valor_diaria else "—"
            linhas_cotacao.append(("🚗 Carro", f"{cotacao.carro_locadora} — {cotacao.carro_modelo or '—'} · {val}/diária"))

        total_fmt = "—"
        if cotacao.valor_total:
            total_fmt = f"R$ {cotacao.valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        dados_viagem = _tabela_dados([
            ("Protocolo",  f'<strong style="color:{_AZUL_MEDIO}">{solicitacao.protocolo}</strong>'),
            ("Destino",    f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Data de Ida", solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("Retorno",    data_volta),
        ])

        dados_cot = _tabela_dados(linhas_cotacao + [
            ("💵 Valor Total",  f'<strong style="font-size:16px;color:{_VERDE}">{total_fmt}</strong>'),
        ]) if linhas_cotacao else ""

        obs_html = ""
        if cotacao.observacoes:
            obs_html = f'<p style="font-size:13px;color:#64748b;font-style:italic;margin:8px 0 0"><strong>Obs.:</strong> {cotacao.observacoes}</p>'

        corpo = f"""
          <p style="margin:0 0 16px">Olá, <strong>{solicitacao.solicitante_username}</strong>,</p>
          <p style="margin:0 0 16px;color:#64748b">
            A agência <strong>{cotacao.agencia_nome}</strong> enviou a cotação para a sua viagem:
          </p>
          {dados_viagem}
          <p style="font-weight:700;color:#1e3a8a;margin:20px 0 4px;font-size:13px">DETALHES DA COTAÇÃO</p>
          {dados_cot}
          {obs_html}
          {_alerta("Em caso de dúvidas sobre a cotação, entre em contato com o setor de viagens.", _AZUL_CLARO, _AZUL_ESCURO)}"""

        return _base_html(faixa, corpo)

    # ── Setor: nova solicitação aguardando pré-aprovação ──────────────────────

    def enviar_email_setor_pendente(self, solicitacao) -> bool:
        """Notifica o setor de viagens que há uma solicitação aguardando pré-aprovação."""
        assunto  = f"[ViagensLabs] {solicitacao.protocolo} — Aguardando Pré-Aprovação do Setor"
        destino  = settings.SETOR_EMAIL
        html     = self._tpl_setor_pendente(solicitacao)
        return self._enviar(destino, assunto, html)

    def _tpl_setor_pendente(self, solicitacao) -> str:
        data_volta = solicitacao.data_volta.strftime("%d/%m/%Y") if solicitacao.data_volta else "—"
        faixa = _faixa(_AMARELO_BG, _AMARELO, "📋", "Nova Solicitação para Pré-Aprovação",
                       f"{solicitacao.protocolo} — {solicitacao.solicitante_username}")
        dados = _tabela_dados([
            ("Protocolo",    f'<strong style="color:{_AZUL_MEDIO}">{solicitacao.protocolo}</strong>'),
            ("Solicitante",  solicitacao.solicitante_username),
            ("Viajante",     solicitacao.viajante_nome or solicitacao.solicitante_username),
            ("CPF",          solicitacao.viajante_cpf  or "—"),
            ("Cargo",        solicitacao.viajante_cargo or "—"),
            ("Filial",       solicitacao.viajante_filial or "—"),
            ("Centro de Custo", f"{solicitacao.viajante_centro_custo} (Cód.: {solicitacao.viajante_cod_centro_custo or '—'})"),
            ("Admissão",     solicitacao.viajante_data_admissao or "—"),
            ("Dt. Nascimento", solicitacao.viajante_data_nascimento or "—"),
            ("Celular",      solicitacao.viajante_celular or "—"),
            ("Destino",      f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Data de Ida",  solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("Retorno",      data_volta),
            ("Tipo",         solicitacao.tipo_servico.replace(",", " + ")),
            ("Classificação",solicitacao.classificacao),
            ("Motivo",       solicitacao.motivo_viagem),
        ])
        link = f"{self.base_url}/painel.html"
        corpo = f"""
          <p style="margin:0 0 16px">Uma nova solicitação de viagem foi aprovada pelos gestores e aguarda <strong>pré-aprovação do setor</strong>:</p>
          {dados}
          {_botao(link, "Acessar o Painel do Setor", _AMARELO)}
          {_alerta("Acesse o painel para pré-aprovar ou reprovar esta solicitação.", _AMARELO_BG, _AMARELO)}"""
        return _base_html(faixa, corpo)

    # ── Setor: solicitar cotações às agências ─────────────────────────────────

    def enviar_email_agencias_cotacao(self, solicitacao, tokens: dict | None = None) -> bool:
        """Envia pedido de cotação para Tastur e Kontrip após pré-aprovação do setor.
        tokens = {'Tastur': uuid_str, 'Kontrip': uuid_str} — se None, usa link genérico (reenvio).
        """
        enviado = False
        for agencia_nome, email_agencia in [
            ("Tastur",  settings.AGENCIA_TASTUR_EMAIL),
            ("Kontrip", settings.AGENCIA_KONTRIP_EMAIL),
        ]:
            if not email_agencia:
                logger.warning(f"[Email] E-mail da {agencia_nome} não configurado. Pulando.")
                continue
            token_uuid = (tokens or {}).get(agencia_nome)
            assunto = f"[ViagensLabs] {solicitacao.protocolo} — Solicitação de Cotação"
            html    = self._tpl_agencia_cotacao(solicitacao, agencia_nome, token_uuid)
            if self._enviar(email_agencia, assunto, html):
                enviado = True
        return enviado

    def _tpl_agencia_cotacao(self, solicitacao, agencia_nome: str, token_uuid: str | None = None) -> str:
        data_volta = solicitacao.data_volta.strftime("%d/%m/%Y") if solicitacao.data_volta else "—"
        faixa = _faixa(_AZUL_CLARO, _AZUL_ESCURO, "✈", f"Solicitação de Cotação — {agencia_nome}",
                       f"Protocolo: {solicitacao.protocolo}")
        servicos = [s.strip() for s in (solicitacao.tipo_servico or "").split(",")]
        linhas = [
            ("Protocolo",    f'<strong style="color:{_AZUL_MEDIO}">{solicitacao.protocolo}</strong>'),
            ("Solicitante",  solicitacao.solicitante_username),
            ("Origem",       f"{solicitacao.origem_cidade} / {solicitacao.origem_estado}" if solicitacao.origem_cidade else "—"),
            ("Destino",      f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Data de Ida",  solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("Retorno",      data_volta),
            ("Serviços",     " + ".join(servicos)),
            ("Classificação",solicitacao.classificacao),
        ]
        if "Aereo" in servicos:
            linhas.append(("Período Aéreo",  solicitacao.aereo_periodo_preferido or "Qualquer"))
            linhas.append(("Trecho Aéreo",   solicitacao.aereo_tipo_trecho or "—"))
            if solicitacao.bagagem_extra:
                linhas.append(("Bagagem Extra", "Sim"))
            if solicitacao.assento_especial:
                linhas.append(("Assento Especial", solicitacao.assento_especial))
        if "Hospedagem" in servicos and solicitacao.preferencia_hotel_nome:
            linhas.append(("Hotel Preferido", solicitacao.preferencia_hotel_nome))
        if "Carro" in servicos:
            linhas.append(("Retirada Carro",   f"{solicitacao.carro_cidade_retirada} às {solicitacao.carro_hora_retirada}"))
            linhas.append(("Devolução Carro",  f"{solicitacao.carro_cidade_devolucao} às {solicitacao.carro_hora_devolucao}"))
        if solicitacao.observacoes_viajante:
            linhas.append(("Observações",     solicitacao.observacoes_viajante))
        dados = _tabela_dados(linhas)

        if token_uuid:
            link   = f"{self.base_url_agencia}/agencia.html?token={token_uuid}"
            instrucao = _alerta(
                "⚠ Este link é único e pessoal para esta solicitação. É válido por <strong>7 dias</strong>. "
                "Clique no botão abaixo para registrar sua cotação diretamente — sem necessidade de login.",
                _AZUL_CLARO, _AZUL_ESCURO
            )
            botao  = _botao(link, "&#128196;&nbsp; Registrar Cotação", _AZUL_MEDIO)
        else:
            # Reenvio sem novo token (link genérico com orientação manual)
            instrucao = _alerta(
                "Solicitação de reenvio. Por favor, entre em contato com o setor de viagens para obter o link de acesso.",
                _AMARELO_BG, _AMARELO
            )
            botao = ""

        corpo = f"""
          <p style="margin:0 0 16px">Prezada <strong>{agencia_nome}</strong>,</p>
          <p style="margin:0 0 16px;color:#64748b">
            Solicitamos cotação para a seguinte viagem corporativa.
          </p>
          {dados}
          {instrucao}
          {botao}"""
        return _base_html(faixa, corpo)

    # ── Setor: ambas as cotações recebidas — aguarda decisão ──────────────────

    def enviar_email_setor_comparativo(self, solicitacao, cotacoes: list) -> bool:
        """Notifica o setor que ambas as agências cotaram e a decisão pode ser tomada."""
        assunto = f"[ViagensLabs] {solicitacao.protocolo} — Cotações Recebidas, Aguardando Decisão"
        destino = settings.SETOR_EMAIL
        html    = self._tpl_setor_comparativo(solicitacao, cotacoes)
        return self._enviar(destino, assunto, html)

    def _tpl_setor_comparativo(self, solicitacao, cotacoes: list) -> str:
        data_volta = solicitacao.data_volta.strftime("%d/%m/%Y") if solicitacao.data_volta else "—"
        faixa = _faixa(_VERDE_BG, _VERDE, "⚖️", "Cotações Recebidas — Aguardando Decisão",
                       f"{solicitacao.protocolo} — {solicitacao.destino_cidade}")
        dados_sol = _tabela_dados([
            ("Protocolo",   f'<strong style="color:{_AZUL_MEDIO}">{solicitacao.protocolo}</strong>'),
            ("Solicitante", solicitacao.solicitante_username),
            ("Destino",     f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Ida",         solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("Retorno",     data_volta),
            ("Serviços",    solicitacao.tipo_servico.replace(",", " + ")),
        ])

        blocos_cot = ""
        for cot in cotacoes:
            total_fmt = f"R$ {cot.valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if cot.valor_total else "—"
            linhas_c = [("Agência", f"<strong>{cot.agencia_nome}</strong>")]
            if cot.aereo_companhia:
                linhas_c.append(("Aéreo", f"{cot.aereo_companhia} voo {cot.aereo_numero_voo or '—'}"))
            if cot.hotel_nome:
                linhas_c.append(("Hotel", f"{cot.hotel_nome} ({cot.hotel_categoria})"))
            if cot.rodov_empresa:
                linhas_c.append(("Rodoviário", cot.rodov_empresa))
            if cot.carro_locadora:
                linhas_c.append(("Carro", f"{cot.carro_locadora} — {cot.carro_modelo or '—'}"))
            linhas_c.append(("💵 Total", f'<strong style="color:{_VERDE};font-size:15px">{total_fmt}</strong>'))
            if cot.observacoes:
                linhas_c.append(("Obs.", cot.observacoes))
            blocos_cot += f'<p style="font-weight:700;color:{_AZUL_ESCURO};margin:20px 0 4px">{cot.agencia_nome.upper()}</p>'
            blocos_cot += _tabela_dados(linhas_c)

        link = f"{self.base_url}/painel.html"
        corpo = f"""
          <p style="margin:0 0 16px">Ambas as agências enviaram suas cotações. Acesse o painel para comparar e <strong>escolher a agência vencedora</strong>:</p>
          {dados_sol}
          <p style="font-weight:700;color:{_AZUL_ESCURO};margin:24px 0 4px;font-size:13px">COTAÇÕES RECEBIDAS</p>
          {blocos_cot}
          {_botao(link, "Acessar o Painel e Escolher", _VERDE)}
          {_alerta("Após escolher a agência no painel, ela será notificada automaticamente.", _VERDE_BG, _VERDE)}"""
        return _base_html(faixa, corpo)

    # ── Notificar agência vencedora ────────────────────────────────────────────

    def enviar_email_agencia_vencedora(self, solicitacao, agencia_nome: str, token_voucher_uuid: str = "") -> bool:
        """Notifica a agência vencedora escolhida pelo setor, com link token para upload de vouchers."""
        email_map = {
            "Tastur":  settings.AGENCIA_TASTUR_EMAIL,
            "Kontrip": settings.AGENCIA_KONTRIP_EMAIL,
        }
        email_destino = email_map.get(agencia_nome, "")
        if not email_destino:
            logger.warning(f"[Email] E-mail da {agencia_nome} não configurado. Notificação não enviada.")
            return False
        assunto = f"[ViagensLabs] {solicitacao.protocolo} — Cotação Aprovada ✓"
        html    = self._tpl_agencia_vencedora(solicitacao, agencia_nome, token_voucher_uuid)
        return self._enviar(email_destino, assunto, html)

    def _tpl_agencia_vencedora(self, solicitacao, agencia_nome: str, token_voucher_uuid: str = "") -> str:
        data_volta = solicitacao.data_volta.strftime("%d/%m/%Y") if solicitacao.data_volta else "—"
        faixa = _faixa(_VERDE_BG, _VERDE, "🏆", f"Cotação Aprovada — {agencia_nome}",
                       f"Protocolo {solicitacao.protocolo} foi aprovado para vocês")
        dados = _tabela_dados([
            ("Protocolo",   f'<strong style="color:{_AZUL_MEDIO}">{solicitacao.protocolo}</strong>'),
            ("Solicitante", solicitacao.solicitante_username),
            ("Destino",     f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Ida",         solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("Retorno",     data_volta),
            ("Serviços",    solicitacao.tipo_servico.replace(",", " + ")),
        ])
        if token_voucher_uuid:
            link  = f"{self.base_url_agencia}/agencia.html?token={token_voucher_uuid}"
            instrucao = _alerta(
                "🎫 Parabéns! Por favor, emita os vouchers e anexe-os clicando no botão abaixo. "
                "O link é único e pessoal — válido por <strong>14 dias</strong>.",
                _VERDE_BG, _VERDE
            )
            botao = _botao(link, "📂&nbsp; Enviar Vouchers", _VERDE)
        else:
            instrucao = _alerta(
                "Em caso de dúvidas, entre em contato com o setor de viagens respondendo este e-mail.",
                _VERDE_BG, _VERDE
            )
            botao = ""
        corpo = f"""
          <p style="margin:0 0 16px">Prezada <strong>{agencia_nome}</strong>,</p>
          <p style="margin:0 0 16px;color:#64748b">
            O setor de viagens selecionou sua cotação. Por favor, inicie o processo de reserva assim que possível.
          </p>
          {dados}
          {instrucao}
          {botao}"""
        return _base_html(faixa, corpo)

    # ── Notificar agência PERDEDORA ───────────────────────────────────────────

    def enviar_email_agencia_perdedora(self, solicitacao, agencia_nome: str) -> bool:
        """Notifica a agência que não foi selecionada pelo setor."""
        email_map = {
            "Tastur":  settings.AGENCIA_TASTUR_EMAIL,
            "Kontrip": settings.AGENCIA_KONTRIP_EMAIL,
        }
        email_destino = email_map.get(agencia_nome, "")
        if not email_destino:
            return False
        assunto = f"[ViagensLabs] {solicitacao.protocolo} — Cotação não selecionada"
        html    = self._tpl_agencia_perdedora(solicitacao, agencia_nome)
        return self._enviar(email_destino, assunto, html)

    def _tpl_agencia_perdedora(self, solicitacao, agencia_nome: str) -> str:
        faixa = _faixa(_CINZA_BG, _CINZA_TEXTO, "📋", f"Cotação Não Selecionada — {agencia_nome}",
                       f"Protocolo {solicitacao.protocolo}")
        corpo = f"""
          <p style="margin:0 0 16px">Prezada <strong>{agencia_nome}</strong>,</p>
          <p style="margin:0 0 16px;color:#64748b">
            Agradecemos sua cotação para o protocolo <strong>{solicitacao.protocolo}</strong>
            ({solicitacao.destino_cidade} / {solicitacao.destino_estado}).
            Neste caso, o setor de viagens optou por outra proposta.
          </p>
          {_alerta("Agradecemos a participação e contamos com vocês nas próximas oportunidades.", _CINZA_BG, _CINZA_TEXTO)}"""
        return _base_html(faixa, corpo)

    # ── Notificar viajante: viagem aprovada pelo setor ────────────────────────

    def enviar_email_viajante_aprovado(self, solicitacao, agencia_nome: str) -> bool:
        """Avisa ao viajante que a viagem foi aprovada e a agência foi escolhida."""
        assunto    = f"[ViagensLabs] {solicitacao.protocolo} — Viagem Aprovada ✈"
        email_dest = f"{solicitacao.solicitante_username}@magazineluiza.com.br"
        html       = self._tpl_viajante_aprovado(solicitacao, agencia_nome)
        return self._enviar(email_dest, assunto, html)

    def _tpl_viajante_aprovado(self, solicitacao, agencia_nome: str) -> str:
        data_volta = solicitacao.data_volta.strftime("%d/%m/%Y") if solicitacao.data_volta else "—"
        faixa = _faixa(_VERDE_BG, _VERDE, "✅", "Viagem Aprovada!",
                       f"Protocolo {solicitacao.protocolo} — aguardando emissão dos vouchers")
        dados = _tabela_dados([
            ("Protocolo",    f'<strong style="color:{_AZUL_MEDIO}">{solicitacao.protocolo}</strong>'),
            ("Destino",      f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Ida",          solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("Retorno",      data_volta),
            ("Serviços",     solicitacao.tipo_servico.replace(",", " · ")),
            ("Agência",      f"<strong>{agencia_nome}</strong>"),
        ])
        corpo = f"""
          <p style="margin:0 0 16px">Olá, <strong>{solicitacao.solicitante_username}</strong>,</p>
          <p style="margin:0 0 16px;color:#64748b">
            Boa notícia! Sua solicitação foi aprovada pelo setor de viagens.
            A agência <strong>{agencia_nome}</strong> irá emitir os vouchers em breve.
          </p>
          {dados}
          {_alerta("Você receberá um novo e-mail com os vouchers assim que forem emitidos.", _VERDE_BG, _VERDE)}"""
        return _base_html(faixa, corpo)

    # ── Notificar viajante: reprova em qualquer etapa ─────────────────────────

    def enviar_email_reprovacao_viajante(self, solicitacao, etapa: str, motivo: str = "") -> bool:
        """Informa ao viajante que a solicitação foi reprovada, com etapa e motivo."""
        assunto    = f"[ViagensLabs] {solicitacao.protocolo} — Solicitação Reprovada"
        email_dest = f"{solicitacao.solicitante_username}@magazineluiza.com.br"
        html       = self._tpl_reprovacao_viajante(solicitacao, etapa, motivo)
        return self._enviar(email_dest, assunto, html)

    def _tpl_reprovacao_viajante(self, solicitacao, etapa: str, motivo: str) -> str:
        data_volta = solicitacao.data_volta.strftime("%d/%m/%Y") if solicitacao.data_volta else "—"
        faixa = _faixa(_VERMELHO_BG, _VERMELHO, "✗", "Solicitação Reprovada",
                       f"Protocolo {solicitacao.protocolo}")
        dados = _tabela_dados([
            ("Protocolo",    f'<strong style="color:{_AZUL_MEDIO}">{solicitacao.protocolo}</strong>'),
            ("Destino",      f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Ida",          solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("Retorno",      data_volta),
            ("Reprovada por", etapa),
        ])
        motivo_html = ""
        if motivo and motivo.strip():
            motivo_html = f"""
              <div style="margin:16px 0;padding:14px 18px;background:{_VERMELHO_BG};
                          border-left:4px solid {_VERMELHO};border-radius:6px">
                <p style="margin:0;font-size:13px;color:{_VERMELHO}">
                  <strong>Motivo informado:</strong><br>{motivo}
                </p>
              </div>"""
        corpo = f"""
          <p style="margin:0 0 16px">Olá, <strong>{solicitacao.solicitante_username}</strong>,</p>
          <p style="margin:0 0 16px;color:#64748b">
            Infelizmente sua solicitação de viagem não foi aprovada.
          </p>
          {dados}
          {motivo_html}
          {_alerta("Em caso de dúvidas entre em contato com o setor de viagens respondendo este e-mail.", _VERMELHO_BG, _VERMELHO)}"""
        return _base_html(faixa, corpo)

    # ── Notificar viajante: vouchers emitidos (CONCLUIDA) ─────────────────────

    def enviar_email_vouchers_viajante(self, solicitacao, vouchers: list) -> bool:
        """Envia os links dos vouchers ao viajante ao concluir a solicitação."""
        assunto    = f"[ViagensLabs] {solicitacao.protocolo} — Seus Vouchers ✈"
        email_dest = f"{solicitacao.solicitante_username}@magazineluiza.com.br"
        html       = self._tpl_vouchers_viajante(solicitacao, vouchers)
        return self._enviar(email_dest, assunto, html)

    def _tpl_vouchers_viajante(self, solicitacao, vouchers: list) -> str:
        data_volta = solicitacao.data_volta.strftime("%d/%m/%Y") if solicitacao.data_volta else "—"
        faixa = _faixa(_VERDE_BG, _VERDE, "🎫", "Sua Viagem está Confirmada!",
                       f"Protocolo {solicitacao.protocolo} — vouchers disponíveis")
        dados = _tabela_dados([
            ("Protocolo", f'<strong style="color:{_AZUL_MEDIO}">{solicitacao.protocolo}</strong>'),
            ("Destino",   f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Ida",       solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("Retorno",   data_volta),
            ("Agência",   solicitacao.agencia_vencedora or "—"),
        ])
        _nomes_voucher = {"aereo": "✈ Passagem Aérea", "hospedagem": "🏨 Hospedagem", "carro": "🚗 Carro", "rodoviario": "🚌 Rodoviário"}
        links_html = ""
        for v in vouchers:
            label = _nomes_voucher.get(v.tipo_voucher, v.tipo_voucher.capitalize())
            url   = f"{self.base_url}/vouchers/{v.caminho_arquivo}"
            links_html += f'<div style="margin:8px 0"><a href="{url}" style="display:inline-block;padding:8px 20px;background:{_AZUL_MEDIO};color:#fff;border-radius:6px;text-decoration:none;font-size:13px">{label} — Download</a></div>'
        corpo = f"""
          <p style="margin:0 0 16px">Olá, <strong>{solicitacao.solicitante_username}</strong>,</p>
          <p style="margin:0 0 16px;color:#64748b">Seus vouchers de viagem já estão disponíveis. Boa viagem! ✈</p>
          {dados}
          <div style="margin:20px 0">{links_html}</div>
          {_alerta("Guarde este e-mail. Os links ficam disponíveis por 90 dias.", _VERDE_BG, _VERDE)}"""
        return _base_html(faixa, corpo)

    # ── Notificar setor: solicitação concluída ────────────────────────────────

    def enviar_email_conclusao_setor(self, solicitacao) -> bool:
        """Cópia interna ao setor quando uma solicitação é concluída."""
        assunto = f"[ViagensLabs] CONCLUÍDA — {solicitacao.protocolo}"
        html    = self._tpl_conclusao_setor(solicitacao)
        return self._enviar(settings.SETOR_EMAIL, assunto, html)

    def _tpl_conclusao_setor(self, solicitacao) -> str:
        faixa = _faixa(_VERDE_BG, _VERDE, "✓", "Solicitação Concluída",
                       f"Protocolo {solicitacao.protocolo} — todos os vouchers emitidos")
        dados = _tabela_dados([
            ("Protocolo",   solicitacao.protocolo),
            ("Solicitante", solicitacao.solicitante_username),
            ("Destino",     f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Ida",         solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("Agência",     solicitacao.agencia_vencedora or "—"),
        ])
        corpo = f"""
          <p style="margin:0 0 16px;color:#64748b">
            Os vouchers foram emitidos e enviados ao viajante. Solicitação encerrada com sucesso.
          </p>
          {dados}"""
        return _base_html(faixa, corpo)

    # ── Lembrete SLA: aprovador N1/N2 ────────────────────────────────────────

    def enviar_email_lembrete_n1(self, solicitacao, token, numero_lembrete: int) -> bool:
        """Lembrete ao aprovador antes do SLA vencer."""
        assunto    = f"[Lembrete {numero_lembrete}/2] Aprovação pendente — {solicitacao.protocolo}"
        email_dest = token.email_aprovador
        html       = self._tpl_lembrete_n1(solicitacao, token, numero_lembrete)
        return self._enviar(email_dest, assunto, html)

    def _tpl_lembrete_n1(self, solicitacao, token, numero_lembrete: int) -> str:
        link         = f"{self.base_url_aprovacao}/portal_aprovacao.html?token={token.uuid}"
        urgencia_cor = _VERMELHO if numero_lembrete >= 2 else _AMARELO
        urgencia_bg  = _VERMELHO_BG if numero_lembrete >= 2 else _AMARELO_BG
        faixa = _faixa(urgencia_bg, urgencia_cor, "⏰",
                       f"Lembrete {numero_lembrete}/2 — Aprovação Pendente",
                       f"Protocolo {solicitacao.protocolo} aguarda sua decisão")
        dados = _tabela_dados([
            ("Protocolo",   solicitacao.protocolo),
            ("Solicitante", solicitacao.solicitante_username),
            ("Destino",     f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Ida",         solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("Expira em",   token.data_expiracao.strftime("%d/%m/%Y %H:%M")),
        ])
        corpo = f"""
          <p style="margin:0 0 16px">Olá, <strong>{token.nome_aprovador}</strong>,</p>
          <p style="margin:0 0 16px;color:#64748b">
            Este é o lembrete <strong>{numero_lembrete}</strong> de 2.
            A solicitação abaixo ainda aguarda sua aprovação.
          </p>
          {dados}
          {_botao(link, "Aprovar ou Reprovar Agora", urgencia_cor)}"""
        return _base_html(faixa, corpo)

    # ── Alerta SLA: escala N2 (N1 emergencial não respondeu) ─────────────────

    def enviar_email_escala_n2(self, solicitacao, token_n2) -> bool:
        """Notifica N2 e setor quando N1 emergencial não respondeu no prazo."""
        link    = f"{self.base_url_aprovacao}/portal_aprovacao.html?token={token_n2.uuid}"
        assunto = f"[ESCALADO N2] {solicitacao.protocolo} — N1 não respondeu a tempo"
        html    = self._tpl_escala_n2(solicitacao, token_n2, link)
        return self._enviar([token_n2.email_aprovador, settings.SETOR_EMAIL], assunto, html)

    def _tpl_escala_n2(self, solicitacao, token_n2, link: str) -> str:
        faixa = _faixa(_VERMELHO_BG, _VERMELHO, "🔺", "Escalado para N2",
                       f"{solicitacao.protocolo} — N1 não respondeu no prazo emergencial")
        dados = _tabela_dados([
            ("Protocolo",   solicitacao.protocolo),
            ("Solicitante", solicitacao.solicitante_username),
            ("Destino",     f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Ida",         solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("SLA N2",      "8 horas a partir deste e-mail"),
        ])
        corpo = f"""
          <p style="margin:0 0 16px">Olá, <strong>{token_n2.nome_aprovador}</strong>,</p>
          <p style="margin:0 0 16px;color:#64748b">
            O aprovador N1 não respondeu dentro do prazo de 4h (viagem emergencial).
            A aprovação foi escalada automaticamente para você.
          </p>
          {dados}
          {_botao(link, "Aprovar ou Reprovar (N2)", _VERMELHO)}"""
        return _base_html(faixa, corpo)

    # ── Alerta SLA: aprovação manual necessária ───────────────────────────────

    def enviar_email_aprovacao_manual(self, solicitacao) -> bool:
        """Alerta o setor quando N1 comum não respondeu após 2 lembretes."""
        assunto = f"[AÇÃO MANUAL] {solicitacao.protocolo} — N1 não respondeu"
        html    = self._tpl_aprovacao_manual(solicitacao)
        return self._enviar(settings.SETOR_EMAIL, assunto, html)

    def _tpl_aprovacao_manual(self, solicitacao) -> str:
        faixa = _faixa(_AMARELO_BG, _AMARELO, "⚠️", "Aprovação Manual Necessária",
                       f"N1 não respondeu após 2 lembretes — {solicitacao.protocolo}")
        dados = _tabela_dados([
            ("Protocolo",    solicitacao.protocolo),
            ("Solicitante",  solicitacao.solicitante_username),
            ("Destino",      f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
            ("Ida",          solicitacao.data_ida.strftime("%d/%m/%Y")),
            ("Aprovador N1", solicitacao.aprovador_n1_nome),
        ])
        corpo = f"""
          <p style="margin:0 0 16px;color:#64748b">
            O aprovador N1 (<strong>{solicitacao.aprovador_n1_nome}</strong>) não respondeu
            dentro do prazo após 2 lembretes automáticos.
            Esta solicitação precisa de intervenção manual pelo setor de viagens.
          </p>
          {dados}
          {_alerta("Acesse o painel do setor para tomar uma decisão sobre esta solicitação.", _AMARELO_BG, _AMARELO)}"""
        return _base_html(faixa, corpo)

    # ── Lembrete SLA: cotação às agências ─────────────────────────────────────

    def enviar_email_lembrete_cotacao(self, solicitacao, numero_lembrete: int) -> bool:
        """Lembrete às agências quando o prazo de cotação está vencendo."""
        assunto = f"[Lembrete {numero_lembrete}/2] Cotação pendente — {solicitacao.protocolo}"
        html    = self._tpl_lembrete_cotacao(solicitacao, numero_lembrete)
        emails  = [e for e in [settings.AGENCIA_TASTUR_EMAIL, settings.AGENCIA_KONTRIP_EMAIL] if e]
        if not emails:
            return False
        return self._enviar(emails, assunto, html)

    def _tpl_lembrete_cotacao(self, solicitacao, numero_lembrete: int) -> str:
        link  = f"{self.base_url}/agencia.html"
        prazo = "4 horas" if solicitacao.classificacao == "Emergencial" else "24 horas"
        faixa = _faixa(_AMARELO_BG, _AMARELO, "⏰",
                       f"Lembrete {numero_lembrete}/2 — Cotação Pendente",
                       f"Protocolo {solicitacao.protocolo} aguarda cotação")
        corpo = f"""
          <p style="margin:0 0 16px;color:#64748b">
            O protocolo abaixo ainda aguarda cotação. Prazo: <strong>{prazo}</strong>.
          </p>
          {_tabela_dados([
              ("Protocolo", solicitacao.protocolo),
              ("Destino",   f"{solicitacao.destino_cidade} / {solicitacao.destino_estado}"),
              ("Ida",       solicitacao.data_ida.strftime("%d/%m/%Y")),
              ("Serviços",  solicitacao.tipo_servico.replace(",", " · ")),
          ])}
          {_botao(link, "Acessar Portal e Enviar Cotação", _AMARELO)}"""
        return _base_html(faixa, corpo)

    # ── Notificar setor: match de casamento detectado ─────────────────────────

    def enviar_email_casamento_setor(self, sol_a, sol_b, tipo_match: str, servicos_comuns: str) -> bool:
        """Avisa o setor que duas solicitações podem ser otimizadas em conjunto."""
        assunto = f"[ViagensLabs] Match {tipo_match} — {sol_a.protocolo} / {sol_b.protocolo}"
        html    = self._tpl_casamento_setor(sol_a, sol_b, tipo_match, servicos_comuns)
        return self._enviar(settings.SETOR_EMAIL, assunto, html)

    def _tpl_casamento_setor(self, sol_a, sol_b, tipo_match: str, servicos_comuns: str) -> str:
        badge_cor = {"TOTAL": _VERDE, "PARCIAL_A": _AZUL_MEDIO, "PARCIAL_B": _AMARELO}.get(tipo_match, _AZUL_MEDIO)
        badge_bg  = {"TOTAL": _VERDE_BG, "PARCIAL_A": _AZUL_CLARO, "PARCIAL_B": _AMARELO_BG}.get(tipo_match, _AZUL_CLARO)
        faixa = _faixa(badge_bg, badge_cor, "🔗", f"Match Detectado — {tipo_match}",
                       f"{sol_a.protocolo} e {sol_b.protocolo} podem ser otimizados")
        bloco_a = _tabela_dados([
            ("Protocolo",  sol_a.protocolo), ("Viajante", sol_a.solicitante_username),
            ("Destino",    f"{sol_a.destino_cidade} / {sol_a.destino_estado}"),
            ("Ida",        sol_a.data_ida.strftime("%d/%m/%Y")),
            ("Serviços",   sol_a.tipo_servico.replace(",", " · ")),
        ])
        bloco_b = _tabela_dados([
            ("Protocolo",  sol_b.protocolo), ("Viajante", sol_b.solicitante_username),
            ("Destino",    f"{sol_b.destino_cidade} / {sol_b.destino_estado}"),
            ("Ida",        sol_b.data_ida.strftime("%d/%m/%Y")),
            ("Serviços",   sol_b.tipo_servico.replace(",", " · ")),
        ])
        link = f"{self.base_url}/painel.html"
        corpo = f"""
          <p style="margin:0 0 16px;color:#64748b">
            O motor de matching detectou que as duas solicitações abaixo compartilham
            <strong>{servicos_comuns}</strong> para o mesmo destino/datas.
            Acesse o painel para <strong>Vincular</strong> ou <strong>Ignorar</strong> o match.
          </p>
          <p style="font-weight:600;margin:16px 0 4px">Solicitação A</p>{bloco_a}
          <p style="font-weight:600;margin:16px 0 4px">Solicitação B</p>{bloco_b}
          {_botao(link, "Gerenciar Casamentos no Painel", badge_cor)}"""
        return _base_html(faixa, corpo)

