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

    # Passo 3 - Preferências Carro
    carro_cidade_retirada = Column(String(200), default='')
    carro_hora_retirada = Column(String(10), default='')
    carro_cidade_devolucao = Column(String(200), default='')
    carro_hora_devolucao = Column(String(10), default='')

    # Observações
    observacoes_viajante = Column(Text, default='')

    # Preferência de voo consultiva (Duffel) — texto livre, ex: "LATAM LA3001 GRU→GIG 07:00→08:30"
    preferencia_voo = Column(Text, nullable=True)

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

class UsuarioAgenciaModel(Base):
    """Usuários externos das agências (Tastur/Kontrip) — autenticados por senha hash, não por AD."""
    __tablename__ = "usuarios_agencia"

    id           = Column(Integer, primary_key=True, index=True)
    username     = Column(String(100), unique=True, index=True, nullable=False)
    nome         = Column(String(200), default='')
    agencia_nome = Column(String(100), nullable=False)  # Tastur / Kontrip
    senha_hash   = Column(String(200), nullable=False)
    ativo        = Column(Boolean, default=True)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())


class UserProfileModel(Base):
    """Perfil persistido do viajante — celular e data de nascimento preenchidos manualmente."""
    __tablename__ = "user_profiles"

    username         = Column(String(100), primary_key=True, index=True)
    celular          = Column(String(20),  default='')
    data_nascimento  = Column(String(20),  default='')
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
