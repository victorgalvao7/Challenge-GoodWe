# WeCharge — Registro da integração dos dois projetos

> Este arquivo documenta, passo a passo, como os dois projetos originais
> foram unidos num só. Serve de registro para o time e para qualquer
> pessoa (ou instância do Claude) continuar o trabalho depois.

## 1. O que foi recebido

Dois projetos separados, feitos por integrantes diferentes do time:

1. **`wecharge_site.zip`** — protótipo em **Flask** do site do
   carregador (adicionar → liberar → carregar → finalizar → pagar), com
   um usuário simulado (`SIMULATED_USER`) porque a autenticação estava
   sendo feita por outro colega. Continha um `CONTEXT_LOG.md` próprio
   documentando o fluxo, as fórmulas de energia e os dados de mercado
   pesquisados (potência, tarifa, capacidade de bateria).

2. **`WeCharge_interface_modernizada.zip`** — projeto em **Django**,
   com cadastro, login, logout, verificação de usuário e banco de dados
   de usuário já prontos (app `contas`), além de dois painéis
   **propositalmente deixados como protótipo/mock** para receber essa
   integração: `painel` (usuário comum / motorista) e `operador`
   (administrador do eletroposto).

## 2. Decisão técnica tomada

Os dois projetos usam frameworks diferentes (Flask x Django), então
"juntar" não podia ser um simples merge de arquivos — rodar dois
servidores separados e trocar sessão entre eles seria complexo e frágil
para o que o time precisa.

**Decisão**: portar toda a lógica do site do carregador (rotas Flask +
templates + JS + CSS) para dentro do projeto Django, como a
implementação real do app `painel` — que já era exatamente o lugar para
onde o Django redireciona o usuário comum depois do login
(`contas/views.py → pos_login → painel:painel`).

Ou seja: **o projeto final é 100% Django.** O Flask não é mais
necessário e não faz parte da entrega final.

## 3. O que foi feito, em ordem

1. Lidos os dois projetos por completo (models, views, urls, templates,
   JS, CSS, READMEs e o `CONTEXT_LOG.md` do Flask) para entender o
   fluxo e as decisões já tomadas por vocês.
2. Criado o modelo `Carregador` em `painel/models.py`, com os mesmos
   campos e a mesma lógica de cálculo de energia/custo do protótipo
   Flask (`charger_publico()` virou o método `estado_atual()`), mas
   agora:
   - salvo de verdade no banco (SQLite), em vez de um dicionário Python
     em memória (`CHARGERS = {}`) que se perdia a cada reinício;
   - com uma `ForeignKey` para o usuário do Django (`request.user`), em
     vez do usuário simulado (`SIMULATED_USER`).
3. Portadas todas as rotas do `app.py` (Flask) para `painel/views.py` e
   `painel/urls.py` (Django) — páginas e API JSON, com `@login_required`
   e filtro por `usuario=request.user` em toda consulta/alteração, para
   que cada pessoa só veja e mexa nos próprios carregadores.
4. Portados os templates (`index.html`, `adicionar.html`,
   `carregador.html`, `pagamento.html`, `sucesso.html`) e o visual
   escuro "voltaico" original (CSS/fontes) para
   `painel/templates/painel/` e `painel/static/painel/`.
5. Adaptado o JavaScript (`main.js`, `adicionar.js`, `carregador.js`,
   `pagamento.js`) para funcionar com Django:
   - as URLs da API não ficam mais fixas no JS — vêm de atributos
     `data-*` no HTML, gerados pelo Django com `{% url %}`;
   - criada a função `apiFetch()` em `main.js`, que inclui
     automaticamente o cabeçalho `X-CSRFToken` exigido pelo Django em
     toda chamada `fetch()` que altera dados (POST). Sem isso, o Django
     bloqueia a requisição com erro 403.
6. Atualizado o painel do operador (`operador/views.py`) para mostrar
   dados **reais** agregados de todos os carregadores da plataforma
   (antes eram 3 linhas fixas de exemplo).
7. Gerada e aplicada a migração do banco (`painel/migrations/0001_initial.py`)
   para criar a tabela do modelo `Carregador`.
8. **Testado o fluxo de ponta a ponta** usando o test client do Django
   (sem precisar de navegador), simulando exatamente o que uma pessoa
   faria:
   - cadastro → login → redirecionamento automático pro painel;
   - adicionar carregador (token) → liberar → iniciar → acompanhar
     status → finalizar → ver cobrança → pagar → tela de sucesso;
   - **isolamento entre usuários**: criado um segundo usuário e
     confirmado que ele recebe "não encontrado" ao tentar acessar o
     carregador do primeiro usuário pela URL direta;
   - acesso sem login → redirecionado corretamente para a tela de
     login;
   - **proteção CSRF real** (com `enforce_csrf_checks=True`, simulando
     um navegador de verdade): confirmado que uma chamada à API sem o
     cabeçalho `X-CSRFToken` é bloqueada (403) e que, com o cabeçalho
     (do jeito que o `apiFetch()` do JS faz), a chamada funciona (200);
   - painel do operador: confirmado que um usuário comum é bloqueado
     (redirecionado) e que um administrador vê os carregadores reais
     de todos os usuários, incluindo o que estava em uso no teste.
   - Todos os testes passaram. Os scripts de teste foram removidos do
     projeto final (eram só para validação durante o desenvolvimento).

## 4. Fluxo final (o que você pediu)

1. A pessoa acessa o site e entra em **Login** (`/conta/login/`) ou
   **Cadastro** (`/conta/cadastro/`).
2. Depois do login/cadastro, o Django decide automaticamente para onde
   mandar:
   - usuário comum → **Meu Painel** (`/painel/`) = o site do carregador,
     já com o nome dela aparecendo no topo;
   - administrador → **Painel do Operador** (`/operador/`).
3. Tudo o que a pessoa faz no painel do carregador (adicionar, liberar,
   iniciar, finalizar, pagar) fica salvo no banco, vinculado à conta
   dela. Se ela sair e entrar de novo, os carregadores continuam lá.

## 5. Estrutura final do projeto

```
wecharge_unificado/
├── manage.py
├── requirements.txt
├── README.md
├── REGISTRO_INTEGRACAO.md      # este arquivo
├── core/                        # configurações gerais (settings, urls raiz)
├── contas/                      # cadastro, login, logout (já existia)
├── paginas/                     # site público institucional (já existia)
├── painel/                      # ÁREA DO USUÁRIO — agora com o fluxo
│   │                             # completo do carregador (o que era o
│   │                             # projeto Flask)
│   ├── models.py                 # modelo Carregador + cálculo de energia
│   ├── views.py                  # páginas + API JSON
│   ├── urls.py
│   ├── admin.py                  # carregadores visíveis em /admin/
│   ├── templates/painel/
│   │   ├── base_app.html          # layout "app" (tema escuro, do Flask)
│   │   ├── index.html             # lista de carregadores
│   │   ├── adicionar.html         # QR Code / token
│   │   ├── carregador.html        # liberar/iniciar/acompanhar/finalizar
│   │   ├── pagamento.html         # cobrança + escolha de pagamento
│   │   └── sucesso.html           # confirmação
│   └── static/painel/
│       ├── css/style.css          # identidade visual original do Flask
│       └── js/                    # main.js, adicionar.js, carregador.js,
│                                    # pagamento.js (adaptados para Django)
└── operador/                    # painel do administrador — agora com
                                    # dados reais agregados
```

## 6. Como rodar

```bash
cd wecharge_unificado
python -m venv venv
# Windows: venv\Scripts\activate      Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/` — a tela inicial é o site público
(`paginas`), com links de **Entrar** / **Cadastre-se** no menu.

(Opcional) Para ver todos os cadastros e carregadores pelo `/admin/`:
```bash
python manage.py createsuperuser
```

## 7. Pontos em aberto / próximos passos

- [ ] Integrar um gateway de pagamento real (Pix/cartão), se o time
      decidir ir além do protótipo de interface.
- [ ] Trocar `CHARGER_POWER_KW` em `painel/models.py` pelo valor real
      do hardware do GoodWe Challenge, quando disponível.
- [ ] Testar a leitura de QR Code num celular real — a lib
      `html5-qrcode` precisa de HTTPS (ou `localhost`) para acessar a
      câmera do aparelho.
- [ ] Se for para produção: trocar `DEBUG = True` e a `SECRET_KEY`
      fixa em `core/settings.py`, e configurar `ALLOWED_HOSTS`.
- [ ] Evoluir o painel do operador com histórico e gráficos, se o time
      quiser (por enquanto mostra só os carregadores ativos agora).

## 8. Histórico de decisões

- **24/08/2026** — Recebidos os dois projetos (`wecharge_site.zip` em
  Flask e `WeCharge_interface_modernizada.zip` em Django). Analisado o
  código de ambos, decidido portar o fluxo do carregador para dentro do
  app `painel` do Django (em vez de manter dois servidores separados).
  Criado o modelo `Carregador`, migrado o backend, o frontend (HTML/CSS/JS)
  e testado o fluxo completo ponta a ponta, incluindo isolamento entre
  usuários e proteção CSRF. Painel do operador atualizado para dados
  reais. Projeto final entregue como um único app Django unificado.
