from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.sql import func
from app.infrastructure.database import Base


class SolicitacaoModel(Base):
    __tablename__ = "solicitacoes"

    id = Column(Integer, primary_key=True, index=True)
    protocolo = Column(String(20), unique=True, index=True, nullable=False)

    # Solicitante (login AD)
    solicitante_username = Column(String(100), index=True, nullable=False)
    via_delegacao = Column(Boolean, default=False)

    # Passo 2 - Dados da Viagem
    origem_cidade = Column(String(200), default='')
    origem_estado = Column(String(5), default='')
    destino_cidade = Column(String(200), nullable=False)
    destino_estado = Column(String(5), default='')
    data_ida = Column(DateTime, nullable=False)
    data_volta = Column(DateTime, nullable=True)
    motivo_viagem = Column(Text, nullable=False)
    tipo_servico = Column(String(100), nullable=False)  # valores separados por vírgula

    # Classificação calculada automaticamente
    antecedencia_dias = Column(Integer, default=0)
    classificacao = Column(String(20), default='Comum')  # 'Comum' ou 'Emergencial'
    exige_aprovacao_diretoria = Column(Boolean, default=False)

    # Passo 3 - Preferências Aéreo
    aereo_periodo_preferido = Column(String(50), default='')
    aereo_tipo_trecho = Column(String(20), default='')
    bagagem_extra = Column(Boolean, default=False)
    assento_especial = Column(String(100), default='')

    # Passo 3 - Preferências Rodoviário
    rodov_periodo_preferido = Column(String(50), default='')
    rodov_tipo_onibus = Column(String(50), default='')
    rodov_tipo_trecho = Column(String(20), default='')

    # Passo 3 - Preferências Hospedagem
    preferencia_hotel_nome = Column(String(200), default='')
    quarto_excecao_saude = Column(Boolean, default=False)
    hosp_data_checkin  = Column(String(20), default='')   # DD/MM/AAAA — quando sem aéreo
    hosp_data_checkout = Column(String(20), default='')   # DD/MM/AAAA — quando sem aéreo

    # Passo 3 - Preferências Carro
    carro_data_retirada   = Column(String(20), default='')
    carro_hora_retirada   = Column(String(10), default='')
    carro_cidade_retirada = Column(String(200), default='')
    carro_data_devolucao  = Column(String(20), default='')
    carro_hora_devolucao  = Column(String(10), default='')
    carro_cidade_devolucao = Column(String(200), default='')

    # Observações
    observacoes_viajante = Column(Text, default='')

    # Preferência de voo consultiva (Duffel) — texto livre
    preferencia_voo       = Column(Text, nullable=True)
    preferencia_voo_volta = Column(Text, nullable=True)

    # Aprovação — N1 e N2
    aprovador_n1_email = Column(String(200), default='')
    aprovador_n1_nome = Column(String(200), default='')
    aprovador_n2_email = Column(String(200), default='')
    aprovador_n2_nome = Column(String(200), default='')

    # Perfil do viajante (snapshot do BQ no momento da solicitação)
    viajante_nome            = Column(String(200), default='')
    viajante_cpf             = Column(String(20),  default='')
    viajante_matricula       = Column(String(20),  default='')
    viajante_email           = Column(String(200), default='')
    viajante_cargo           = Column(String(200), default='')
    viajante_filial          = Column(String(20),  default='')
    viajante_centro_custo     = Column(String(200), default='')
    viajante_cod_centro_custo = Column(String(20),  default='')
    viajante_data_admissao    = Column(String(20),  default='')
    viajante_celular          = Column(String(20),  default='')  # input manual obrigatório
    viajante_data_nascimento  = Column(String(20),  default='')  # input manual obrigatório

    # Status da solicitação
    status = Column(String(50), default='AGUARDANDO_N1')

    # Agência vencedora escolhida pelo Setor (Fase 4)
    agencia_vencedora = Column(String(100), nullable=True)

    # Contadores de lembretes SLA (usados pelo sla_scheduler)
    lembrete_n1_count  = Column(Integer, default=0)
    lembrete_cot_count = Column(Integer, default=0)

    data_criacao = Column(DateTime(timezone=True), server_default=func.now())
    data_atualizacao = Column(DateTime(timezone=True), onupdate=func.now())


class TokenAprovacaoModel(Base):
    __tablename__ = "tokens_aprovacao"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, nullable=False)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False)
    nivel = Column(String(5), default='N1')  # 'N1' ou 'N2'
    email_aprovador = Column(String(200), nullable=False)
    nome_aprovador = Column(String(200), default='')
    # PENDENTE / APROVADO / REPROVADO / EXPIRADO
    status = Column(String(20), default='PENDENTE')
    data_expiracao = Column(DateTime, nullable=False)
    data_resposta = Column(DateTime, nullable=True)
    observacao_resposta = Column(Text, default='')
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())


class VoucherModel(Base):
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, index=True)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False)
    tipo_voucher = Column(String(50), nullable=False)  # VOO, HOSPEDAGEM, CARRO
    caminho_arquivo = Column(String(500), nullable=False)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())


class CotacaoModel(Base):
    """Cotação enviada pela agência (Tastur/Kontrip) para uma solicitação aprovada."""
    __tablename__ = "cotacoes"

    id = Column(Integer, primary_key=True, index=True)
    # unique por (solicitacao_id, agencia_nome) — permite Tastur e Kontrip cotarem a mesma solicitação
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False, index=True)
    agencia_nome = Column(String(100), default='')       # Tastur / Kontrip
    agencia_usuario = Column(String(100), default='')    # login da agência

    # Aéreo
    aereo_companhia   = Column(String(100), default='')
    aereo_numero_voo  = Column(String(50),  default='')
    aereo_horario_ida = Column(String(30),  default='')
    aereo_horario_volta = Column(String(30), default='')
    aereo_valor       = Column(Numeric(10, 2), nullable=True)

    # Hospedagem
    hotel_nome          = Column(String(200), default='')
    hotel_categoria     = Column(String(50),  default='')
    hotel_valor_diaria  = Column(Numeric(10, 2), nullable=True)

    # Rodoviário
    rodov_empresa       = Column(String(100), default='')
    rodov_horario_ida   = Column(String(30),  default='')
    rodov_horario_volta = Column(String(30),  default='')
    rodov_valor         = Column(Numeric(10, 2), nullable=True)

    # Carro
    carro_locadora      = Column(String(100), default='')
    carro_modelo        = Column(String(100), default='')
    carro_valor_diaria  = Column(Numeric(10, 2), nullable=True)

    valor_total  = Column(Numeric(10, 2), nullable=True)
    observacoes  = Column(Text, default='')
    # PENDENTE / ACEITA / REJEITADA
    status = Column(String(20), default='PENDENTE')
    data_criacao     = Column(DateTime(timezone=True), server_default=func.now())
    data_atualizacao = Column(DateTime(timezone=True), onupdate=func.now())


class CasamentoModel(Base):
    """Par de solicitações 'casadas' pelo motor de matching."""
    __tablename__ = "casamentos"

    id = Column(Integer, primary_key=True, index=True)
    solicitacao_a_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False)
    solicitacao_b_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False)
    # TOTAL / PARCIAL_A (mesmos serviços, datas próximas) / PARCIAL_B (mesmo destino, datas diferentes)
    tipo_match   = Column(String(20), default='TOTAL')
    destino      = Column(String(200), default='')
    servicos_comuns = Column(String(200), default='')   # serviços em comum
    data_casamento  = Column(DateTime(timezone=True), server_default=func.now())

    # Ação do operador
    status         = Column(String(20), default='PENDENTE')   # PENDENTE / VINCULADO / IGNORADO
    operador_acao  = Column(String(100), default='')
    data_acao      = Column(DateTime, nullable=True)
    grupo_viagem   = Column(String(20), nullable=True)        # código do grupo quando VINCULADO

class AgenciaModel(Base):
    """Agências de viagens — participam do fluxo via e-mail/portal GAS, sem login."""
    __tablename__ = "usuarios_agencia"

    id                        = Column(Integer, primary_key=True, index=True)
    # Identificação
    agencia_nome              = Column(String(100), nullable=False, index=True)   # nome fantasia — referência interna
    razao_social              = Column(String(200), default='')
    cnpj                      = Column(String(20),  default='', unique=True, index=True)
    inscricao_estadual        = Column(String(50),  default='')
    email                     = Column(String(200), default='')
    # Endereço
    cep                       = Column(String(10),  default='')
    logradouro                = Column(String(200), default='')
    numero                    = Column(String(20),  default='')
    complemento               = Column(String(100), default='')
    bairro                    = Column(String(100), default='')
    municipio                 = Column(String(100), default='')
    uf                        = Column(String(2),   default='')
    # Dados bancários
    banco_nome                = Column(String(100), default='')
    banco_codigo              = Column(String(10),  default='')
    agencia_bancaria          = Column(String(20),  default='')
    conta_bancaria            = Column(String(20),  default='')
    tipo_conta                = Column(String(5),   default='CC')  # CC ou CP
    titularidade_cnpj         = Column(String(20),  default='')
    titularidade_razao_social = Column(String(200), default='')
    # Status
    ativo                     = Column(Boolean, default=True)
    data_criacao              = Column(DateTime(timezone=True), server_default=func.now())

# Alias de compatibilidade — código legado que usa UsuarioAgenciaModel continua funcionando
UsuarioAgenciaModel = AgenciaModel


class UserProfileModel(Base):
    """Perfil persistido do viajante — celular e data de nascimento preenchidos manualmente."""
    __tablename__ = "user_profiles"

    username         = Column(String(100), primary_key=True, index=True)
    celular          = Column(String(20),  default='')
    data_nascimento  = Column(String(20),  default='')


class TokenAgenciaModel(Base):
    """
    Token de acesso por link para agências externas (Tastur / Kontrip).
    Gerado pelo setor ao pré-aprovar (finalidade=COTACAO) ou ao escolher vencedora (finalidade=VOUCHER).
    Permite acesso sem login — a agência clica no link do e-mail e acessa diretamente.
    """
    __tablename__ = "tokens_agencia"

    id             = Column(Integer, primary_key=True, index=True)
    uuid           = Column(String(36), unique=True, index=True, nullable=False)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False)
    agencia_nome   = Column(String(100), nullable=False)          # Tastur / Kontrip
    finalidade     = Column(String(20),  default='COTACAO')       # COTACAO / VOUCHER
    # PENDENTE / USADO / EXPIRADO
    status         = Column(String(20),  default='PENDENTE')
    data_expiracao = Column(DateTime, nullable=False)
    data_criacao   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LogEventoModel(Base):
    """Trilha de auditoria — registra todas as transições de status e ações relevantes."""
    __tablename__ = "log_eventos"

    id             = Column(Integer, primary_key=True, index=True)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False, index=True)
    evento         = Column(String(100), nullable=False)   # STATUS_CHANGE | APROVACAO | REPROVACAO | VOUCHER
    de_status      = Column(String(50),  default='')
    para_status    = Column(String(50),  default='')
    ator           = Column(String(200), default='')       # username ou 'sistema'
    observacao     = Column(Text, default='')
    data_criacao   = Column(DateTime(timezone=True), server_default=func.now())


class AutorizacaoTerceiroModel(Base):
    """
    Autorização para que um colaborador (solicitante) possa abrir viagens
    em nome de outro colaborador (terceiro) de hierarquia superior.

    Fluxo:
      1. Viajante abre ticket via portal informando o ID Magalu do terceiro + PDF.
      2. Setor aprova ou reprova o ticket.
      3. Enquanto status='APROVADA', o viajante pode criar solicitações via_delegacao para aquele terceiro.
    """
    __tablename__ = "autorizacoes_terceiros"

    id                    = Column(Integer, primary_key=True, index=True)
    # Quem pede (solicitante logado)
    solicitante_username  = Column(String(100), nullable=False, index=True)
    # Para quem (colaborador de hierarquia superior)
    terceiro_username     = Column(String(100), nullable=False, index=True)
    terceiro_nome         = Column(String(200), default='')
    terceiro_email        = Column(String(200), default='')
    # PDF de autorização assinado pelo terceiro
    pdf_path              = Column(String(500), default='')
    # PENDENTE / APROVADA / REPROVADA / REVOGADA
    status                = Column(String(20), default='PENDENTE', index=True)
    # Observação do setor ao aprovar/reprovar
    observacao_setor      = Column(Text, default='')
    # Operador do setor que tomou a decisão
    operador_setor        = Column(String(100), default='')
    data_criacao          = Column(DateTime(timezone=True), server_default=func.now())
    data_decisao          = Column(DateTime, nullable=True)


class UsuarioQATesteModel(Base):
    """
    Usuários registrados para a realização de testes de QA de ponta a ponta.
    Qualquer solicitação criada por esses usuários terá seus e-mails desviados para os testadores.
    """
    __tablename__ = "usuarios_qa_teste"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(200), nullable=False)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())


class LogAcessoModel(Base):
    """Logs de acessos e logins de usuários para monitoramento e auditoria da plataforma."""
    __tablename__ = "log_acessos"

    id             = Column(Integer, primary_key=True, index=True)
    username       = Column(String(100), nullable=False, index=True)
    nome           = Column(String(200), default='')
    perfil         = Column(String(50), default='')
    ip_origem      = Column(String(50), default='')
    status_acesso  = Column(String(50), default='SUCESSO')  # SUCESSO | BLOQUEADO
    observacao     = Column(Text, default='')
    data_criacao   = Column(DateTime(timezone=True), server_default=func.now(), index=True)
