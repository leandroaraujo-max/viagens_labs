from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

# --- SCHEMAS DE VIAGENS ---

class SolicitacaoCreate(BaseModel):
    """Schema completo para criação de solicitação de viagem (Passos 1, 2 e 3)."""
    # Passo 1 - Contexto
    via_delegacao: bool = False

    # Passo 2 - Dados da Viagem
    origem_cidade: str = ''
    origem_estado: str = ''
    destino_cidade: str
    destino_estado: str = ''
    data_ida: datetime
    data_volta: Optional[datetime] = None
    motivo_viagem: str
    tipo_servico: List[str]  # ['Aereo', 'Rodoviario', 'Hospedagem', 'Carro']

    # Passo 3 - Preferências Aéreo
    aereo_periodo_preferido: str = ''
    aereo_tipo_trecho: str = 'ambos'
    bagagem_extra: bool = False
    assento_especial: str = ''

    # Passo 3 - Preferências Rodoviário
    rodov_periodo_preferido: str = ''
    rodov_tipo_onibus: str = ''
    rodov_tipo_trecho: str = 'ambos'

    # Passo 3 - Preferências Hospedagem
    preferencia_hotel_nome: str = ''
    quarto_excecao_saude: bool = False
    hosp_data_checkin:  str = ''   # DD/MM/AAAA — obrigatório quando hospedagem sem aéreo
    hosp_data_checkout: str = ''   # DD/MM/AAAA — obrigatório quando hospedagem sem aéreo

    # Passo 3 - Preferências Carro
    carro_data_retirada:   str = ''
    carro_hora_retirada:   str = ''
    carro_cidade_retirada: str = ''
    carro_data_devolucao:  str = ''
    carro_hora_devolucao:  str = ''
    carro_cidade_devolucao: str = ''

    # Observações
    observacoes_viajante: str = ''

    # Preferência de voo consultiva (Duffel) — preenchida pelo frontend opcionalmente
    preferencia_voo:       Optional[str] = None
    preferencia_voo_volta: Optional[str] = None

    # Cadeia de aprovação (extraída do BQ no frontend — Passo 1)
    aprovador_n1_email: str = ''
    aprovador_n1_nome: str = ''
    aprovador_n2_email: str = ''
    aprovador_n2_nome: str = ''

    # Perfil do viajante — dados BQ (snapshot) + campos preenchidos manualmente
    viajante_nome:            str = ''
    viajante_cpf:             str = ''
    viajante_matricula:       str = ''
    viajante_email:           str = ''
    viajante_cargo:           str = ''
    viajante_filial:          str = ''
    viajante_centro_custo:    str = ''
    viajante_cod_centro_custo: str = ''
    viajante_data_admissao:   str = ''
    viajante_celular:         str = ''   # input manual obrigatório
    viajante_data_nascimento: str = ''   # input manual obrigatório


class UserProfileData(BaseModel):
    """Perfil do viajante — dados manuais salvos para reuso."""
    celular:          str = ''
    data_nascimento:  str = ''
    model_config = ConfigDict(from_attributes=True)


class SolicitacaoResponse(BaseModel):
    """Schema de saída após criação da solicitação."""
    id: int
    protocolo: str
    solicitante_username: str
    destino_cidade: str
    status: str
    classificacao: str
    data_criacao: datetime

    model_config = ConfigDict(from_attributes=True)


# --- SCHEMAS DE APROVAÇÃO ---

class AprovacaoAcaoRequest(BaseModel):
    """Body para processar aprovação ou reprovação."""
    acao: str           # 'aprovar' ou 'reprovar'
    observacao: str = ''


# --- SCHEMAS DE AUTENTICAÇÃO ---

class LoginCredentials(BaseModel):
    """Schema para receber o usuário e a senha da requisição de login (Apenas AD)."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema para a devolução do Token JWT gerado."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    nome_usuario: str
    username: str          # username do AD — usado para busca no BQ
    perfil: str


# --- SCHEMAS DA AGÊNCIA ---

class CotacaoCreate(BaseModel):
    """Body enviado pela agência ao registrar uma cotação."""
    # Aéreo
    aereo_companhia: str = ''
    aereo_numero_voo: str = ''
    aereo_horario_ida: str = ''
    aereo_horario_volta: str = ''
    aereo_valor: Optional[float] = None

    # Hospedagem
    hotel_nome: str = ''
    hotel_categoria: str = ''
    hotel_valor_diaria: Optional[float] = None

    # Rodoviário
    rodov_empresa: str = ''
    rodov_horario_ida: str = ''
    rodov_horario_volta: str = ''
    rodov_valor: Optional[float] = None

    # Carro
    carro_locadora: str = ''
    carro_modelo: str = ''
    carro_valor_diaria: Optional[float] = None

    valor_total: Optional[float] = None
    observacoes: str = ''


class CotacaoResponse(BaseModel):
    id: int
    solicitacao_id: int
    agencia_nome: str
    agencia_usuario: str
    aereo_companhia: str
    aereo_numero_voo: str
    aereo_horario_ida: str
    aereo_horario_volta: str
    aereo_valor: Optional[float]
    hotel_nome: str
    hotel_categoria: str
    hotel_valor_diaria: Optional[float]
    rodov_empresa: str
    rodov_horario_ida: str
    rodov_horario_volta: str
    rodov_valor: Optional[float]
    carro_locadora: str
    carro_modelo: str
    carro_valor_diaria: Optional[float]
    valor_total: Optional[float]
    observacoes: str
    status: str
    data_criacao: datetime

    model_config = ConfigDict(from_attributes=True)


class SolicitacaoAgenciaResponse(BaseModel):
    """Visão resumida de uma solicitação para o portal da agência."""
    id: int
    protocolo: str
    solicitante_username: str
    destino_cidade: str
    destino_estado: str
    origem_cidade: str
    data_ida: datetime
    data_volta: Optional[datetime]
    tipo_servico: str
    classificacao: str
    status: str
    motivo_viagem: str
    # preferências relevantes para cotação
    aereo_periodo_preferido: str
    aereo_tipo_trecho: str
    bagagem_extra: bool
    assento_especial: str
    preferencia_voo: str = ''
    preferencia_voo_volta: str = ''
    rodov_periodo_preferido: str
    rodov_tipo_onibus: str
    rodov_tipo_trecho: str = ''
    preferencia_hotel_nome: str
    quarto_excecao_saude: bool = False
    carro_data_retirada: str = ''
    carro_hora_retirada: str
    carro_cidade_retirada: str
    carro_data_devolucao: str = ''
    carro_hora_devolucao: str
    carro_cidade_devolucao: str
    observacoes_viajante: str
    # Perfil do viajante (para cotação)
    viajante_nome: str = ''
    viajante_matricula: str = ''
    viajante_cargo: str = ''
    viajante_filial: str = ''
    viajante_cpf: str = ''
    viajante_email: str = ''
    viajante_centro_custo: str = ''
    viajante_cod_centro_custo: str = ''
    viajante_celular: str = ''
    viajante_data_nascimento: str = ''
    cotacao: Optional[CotacaoResponse] = None
    casamentos: List[dict] = []

    model_config = ConfigDict(from_attributes=True)


class CasamentoResponse(BaseModel):
    solicitacao_a_id: int
    solicitacao_b_id: int
    tipo_match: str
    destino: str
    servicos_comuns: str
    data_casamento: datetime

    model_config = ConfigDict(from_attributes=True)


# --- SCHEMAS DO SETOR ---

class SetorAcaoRequest(BaseModel):
    """
    Body para ações do setor sobre uma solicitação.
    ação: PRE_APROVAR | PRE_REPROVAR | APROVAR_TASTUR | APROVAR_KONTRIP | REPROVAR | REENVIAR_AGENCIAS
    """
    acao: str
    observacao: str = ''


class SolicitacaoSetorResponse(BaseModel):
    """Visão completa de uma solicitação para o portal do setor."""
    id: int
    protocolo: str
    solicitante_username: str
    via_delegacao: bool = False
    destino_cidade: str
    destino_estado: str
    origem_cidade: str
    origem_estado: str = ''
    data_ida: datetime
    data_volta: Optional[datetime]
    tipo_servico: str
    classificacao: str
    status: str
    motivo_viagem: str
    # Preferências Aéreo
    aereo_periodo_preferido: str
    aereo_tipo_trecho: str
    bagagem_extra: bool
    assento_especial: str
    preferencia_voo: str = ''
    preferencia_voo_volta: str = ''
    # Preferências Rodoviário
    rodov_periodo_preferido: str
    rodov_tipo_onibus: str
    rodov_tipo_trecho: str = ''
    # Preferências Hospedagem
    preferencia_hotel_nome: str
    quarto_excecao_saude: bool = False
    # Preferências Carro
    carro_data_retirada: str = ''
    carro_hora_retirada: str
    carro_cidade_retirada: str
    carro_data_devolucao: str = ''
    carro_hora_devolucao: str
    carro_cidade_devolucao: str
    # Observações
    observacoes_viajante: str
    # Cadeia de aprovação
    aprovador_n1_email: str = ''
    aprovador_n1_nome: str = ''
    aprovador_n2_email: str = ''
    aprovador_n2_nome: str = ''
    # Perfil do viajante (snapshot)
    viajante_nome: str = ''
    viajante_cpf: str = ''
    viajante_matricula: str = ''
    viajante_email: str = ''
    viajante_cargo: str = ''
    viajante_filial: str = ''
    viajante_centro_custo: str = ''
    viajante_cod_centro_custo: str = ''
    viajante_data_admissao: str = ''
    viajante_celular: str = ''
    viajante_data_nascimento: str = ''
    # Agência e cotações
    agencia_vencedora: Optional[str] = None
    cotacao_tastur: Optional[CotacaoResponse] = None
    cotacao_kontrip: Optional[CotacaoResponse] = None
    todas_cotacoes: List[CotacaoResponse] = []
    casamentos: List[dict] = []

    model_config = ConfigDict(from_attributes=True)


# --- SCHEMAS DE AGÊNCIAS (gestão pelo setor) ---

class AgenciaCreate(BaseModel):
    """Cadastro completo de agência — sem usuário/senha (acesso via e-mail/GAS)."""
    agencia_nome:              str               # Nome fantasia (ex: Tastur)
    razao_social:              str = ''
    cnpj:                      str = ''
    inscricao_estadual:        str = ''
    email:                     str = ''
    # Endereço
    cep:                       str = ''
    logradouro:                str = ''
    numero:                    str = ''
    complemento:               str = ''
    bairro:                    str = ''
    municipio:                 str = ''
    uf:                        str = ''
    # Dados bancários
    banco_nome:                str = ''
    banco_codigo:              str = ''
    agencia_bancaria:          str = ''
    conta_bancaria:            str = ''
    tipo_conta:                str = 'CC'
    titularidade_cnpj:         str = ''
    titularidade_razao_social: str = ''


class AgenciaUpdate(BaseModel):
    """Atualização parcial de agência (todos os campos opcionais)."""
    agencia_nome:              Optional[str]  = None
    razao_social:              Optional[str]  = None
    cnpj:                      Optional[str]  = None
    inscricao_estadual:        Optional[str]  = None
    email:                     Optional[str]  = None
    cep:                       Optional[str]  = None
    logradouro:                Optional[str]  = None
    numero:                    Optional[str]  = None
    complemento:               Optional[str]  = None
    bairro:                    Optional[str]  = None
    municipio:                 Optional[str]  = None
    uf:                        Optional[str]  = None
    banco_nome:                Optional[str]  = None
    banco_codigo:              Optional[str]  = None
    agencia_bancaria:          Optional[str]  = None
    conta_bancaria:            Optional[str]  = None
    tipo_conta:                Optional[str]  = None
    titularidade_cnpj:         Optional[str]  = None
    titularidade_razao_social: Optional[str]  = None
    ativo:                     Optional[bool] = None


class AgenciaResponse(BaseModel):
    """Visão completa da agência para o painel do setor."""
    id:                        int
    agencia_nome:              str
    razao_social:              str = ''
    cnpj:                      str = ''
    inscricao_estadual:        str = ''
    email:                     str = ''
    cep:                       str = ''
    logradouro:                str = ''
    numero:                    str = ''
    complemento:               str = ''
    bairro:                    str = ''
    municipio:                 str = ''
    uf:                        str = ''
    banco_nome:                str = ''
    banco_codigo:              str = ''
    agencia_bancaria:          str = ''
    conta_bancaria:            str = ''
    tipo_conta:                str = 'CC'
    titularidade_cnpj:         str = ''
    titularidade_razao_social: str = ''
    ativo:                     bool
    data_criacao:              Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- SCHEMAS DE USUÁRIOS QA TESTE ---

class UsuarioQATesteCreate(BaseModel):
    username: str
    email: str

class UsuarioQATesteResponse(BaseModel):
    id: int
    username: str
    email: str
    ativo: bool
    data_criacao: datetime

    model_config = ConfigDict(from_attributes=True)

