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
            Dúvidas: <a href="mailto:vagenslabs@luizalabs.com"
                        style="color:{_AZUL_MEDIO};text-decoration:none">vagenslabs@luizalabs.com</a>
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
        self.smtp_host  = settings.SMTP_HOST
        self.smtp_port  = settings.SMTP_PORT
        self.smtp_from  = settings.SMTP_FROM
        self.from_name  = getattr(settings, "SMTP_FROM_NAME", "ViagensLabs | Luizalabs")
        self.reply_to   = getattr(settings, "SMTP_REPLY_TO", "")
        self.base_url   = settings.BASE_URL

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
        link    = f"{self.base_url}/portal_aprovacao.html?token={token.uuid}"
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

    def enviar_email_agencias_cotacao(self, solicitacao) -> bool:
        """Envia pedido de cotação para Tastur e Kontrip após pré-aprovação do setor."""
        enviado = False
        for agencia_nome, email_agencia in [
            ("Tastur",  settings.AGENCIA_TASTUR_EMAIL),
            ("Kontrip", settings.AGENCIA_KONTRIP_EMAIL),
        ]:
            if not email_agencia:
                logger.warning(f"[Email] E-mail da {agencia_nome} não configurado. Pulando.")
                continue
            assunto = f"[ViagensLabs] {solicitacao.protocolo} — Solicitação de Cotação"
            html    = self._tpl_agencia_cotacao(solicitacao, agencia_nome)
            if self._enviar(email_agencia, assunto, html):
                enviado = True
        return enviado

    def _tpl_agencia_cotacao(self, solicitacao, agencia_nome: str) -> str:
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
        link = f"{self.base_url}/agencia.html"
        corpo = f"""
          <p style="margin:0 0 16px">Prezada <strong>{agencia_nome}</strong>,</p>
          <p style="margin:0 0 16px;color:#64748b">
            Solicitamos cotação para a seguinte viagem corporativa.
            Por favor, registre sua cotação no portal da agência até a data combinada.
          </p>
          {dados}
          {_botao(link, f"Acessar o Portal da Agência", _AZUL_MEDIO)}
          {_alerta("Acesse o portal, localize o protocolo acima e registre sua cotação.", _AZUL_CLARO, _AZUL_ESCURO)}"""
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

    def enviar_email_agencia_vencedora(self, solicitacao, agencia_nome: str) -> bool:
        """Notifica a agência vencedora escolhida pelo setor."""
        email_map = {
            "Tastur":  settings.AGENCIA_TASTUR_EMAIL,
            "Kontrip": settings.AGENCIA_KONTRIP_EMAIL,
        }
        email_destino = email_map.get(agencia_nome, "")
        if not email_destino:
            logger.warning(f"[Email] E-mail da {agencia_nome} não configurado. Notificação não enviada.")
            return False
        assunto = f"[ViagensLabs] {solicitacao.protocolo} — Cotação Aprovada ✓"
        html    = self._tpl_agencia_vencedora(solicitacao, agencia_nome)
        return self._enviar(email_destino, assunto, html)

    def _tpl_agencia_vencedora(self, solicitacao, agencia_nome: str) -> str:
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
        link = f"{self.base_url}/agencia.html"
        corpo = f"""
          <p style="margin:0 0 16px">Prezada <strong>{agencia_nome}</strong>,</p>
          <p style="margin:0 0 16px;color:#64748b">
            O setor de viagens selecionou sua cotação. Por favor, inicie o processo de reserva assim que possível.
          </p>
          {dados}
          {_botao(link, "Acessar o Portal da Agência", _VERDE)}
          {_alerta("Em caso de dúvidas, entre em contato com o setor de viagens pelo Reply-To deste e-mail.", _VERDE_BG, _VERDE)}"""
        return _base_html(faixa, corpo)

