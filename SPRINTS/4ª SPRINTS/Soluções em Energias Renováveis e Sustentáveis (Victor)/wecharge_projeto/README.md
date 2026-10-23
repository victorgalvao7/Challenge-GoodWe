# Meu Site (base Django)

Estrutura simples e organizada para você evoluir o site com facilidade.

## Estrutura

```
meu_site/
├── manage.py
├── requirements.txt
├── core/                      # configurações gerais do projeto (settings, urls raiz)
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── paginas/                   # app principal com as páginas do site
    ├── views.py                # lógica de cada página
    ├── urls.py                 # rotas do app
    ├── admin.py
    ├── templates/paginas/      # HTML (base.html + páginas)
    └── static/paginas/css/     # CSS
```

## Como rodar pela primeira vez

1. Crie um ambiente virtual (recomendado):
   ```
   python -m venv venv
   ```
   Ativar no Windows: `venv\Scripts\activate`
   Ativar no Mac/Linux: `source venv/bin/activate`

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

3. Rode as migrações (cria o banco de dados sqlite):
   ```
   python manage.py migrate
   ```

4. (Opcional) Crie um usuário admin para acessar /admin/:
   ```
   python manage.py createsuperuser
   ```

5. Suba o servidor:
   ```
   python manage.py runserver
   ```

6. Acesse no navegador: http://127.0.0.1:8000/

## Como adicionar uma nova página (dentro do app "paginas")

1. Crie uma função em `paginas/views.py`.
2. Crie o template em `paginas/templates/paginas/nome.html` (extends `base.html`).
3. Adicione a rota em `paginas/urls.py`.
4. Se quiser, adicione o link no menu em `paginas/templates/paginas/base.html`.

## Como adicionar um novo app (ex: blog, loja, portfólio)

1. `python manage.py startapp nome_do_app`
2. Adicione `'nome_do_app'` em `INSTALLED_APPS` (`core/settings.py`)
3. Crie `nome_do_app/urls.py` com suas rotas
4. Inclua no `core/urls.py`:
   ```python
   path('nome-do-app/', include('nome_do_app.urls')),
   ```

## Área de usuário e área de administrador

O site agora tem 3 apps novos:

- `contas` — cadastro, login e logout (`/conta/cadastro/`, `/conta/login/`, `/conta/logout/`)
- `painel` — painel do usuário comum / motorista (`/painel/`)
- `operador` — painel do administrador / operador do eletroposto (`/operador/`)

### Cadastro

Em `/conta/cadastro/` a pessoa preenche nome completo, e-mail, telefone (opcional),
cidade (opcional), usuário/login, senha e escolhe o **tipo de conta** (Usuário ou
Administrador). Ao enviar:

- Cria um usuário do Django (senha já vem criptografada automaticamente)
- Salva as informações extras (nome completo, telefone, cidade) no modelo `Perfil` (`contas/models.py`)
- Marca `is_staff = True` se escolheu "Administrador", ou `False` se escolheu "Usuário"
- Loga a pessoa automaticamente e já manda pro painel certo

O que decide se alguém é "usuário comum" ou "administrador" é o campo `is_staff` do usuário do Django:
- `is_staff = False` → só acessa `/painel/`
- `is_staff = True` → acessa `/operador/` (e também consegue acessar `/painel/` se quiser)

Quem tenta acessar `/operador/` sem ser administrador é automaticamente redirecionado de volta para `/painel/`.

Para ver todos os cadastros feitos, acesse `/admin/` (com um superusuário) e entre em "Perfis".

### Criando um superusuário (acesso total, inclusive /admin/)

```
python manage.py createsuperuser
```

### Painel do usuário (`/painel/`) — fluxo completo do carregador

Este projeto une o site de login/cadastro com o protótipo do site do
carregador (que antes era um app Flask separado, `wecharge_site`). O
fluxo completo agora vive dentro do app `painel`:

1. **Meus carregadores** (`/painel/`) — lista os carregadores do usuário logado
2. **Adicionar** (`/painel/adicionar/`) — via QR Code ou token de até 5 caracteres
3. **Liberar / Iniciar / Acompanhar** (`/painel/carregador/<id>/`) — acompanhamento
   em tempo real (kWh, % bateria, custo), com tempo excedente cobrado à parte
   se o veículo ficar conectado depois da bateria cheia
4. **Pagamento** (`/painel/pagamento/<id>/`) — Pix, crédito ou débito (só a
   interface; sem gateway real integrado)

Cada carregador fica salvo no banco (modelo `Carregador` em
`painel/models.py`), vinculado ao usuário que criou (`ForeignKey` para
`User`) — ou seja, cada pessoa só vê e mexe nos próprios carregadores.

### Painel do operador (`/operador/`) — gestão do dono

Contas do tipo **Administrador** agora gerenciam os próprios pontos físicos:

1. **Cadastrar carregador no próprio painel** — o formulário fica diretamente
   em `/operador/`; nele o dono informa nome, token/QR, endereço, preço por
   kWh e marca a posição clicando no mapa;
2. **Editar e ativar/desativar** — altera localização e preço ou impede novas
   sessões sem apagar o histórico;
3. **Acompanhar sessões** — vê quais dos seus carregadores estão em uso;
4. **Administrar renda** — acompanha energia vendida, receita e lucro estimado
   apenas dos carregadores pertencentes à sua conta.

O usuário comum só consegue iniciar uma recarga usando o token/QR de um ponto
ativo e cadastrado pelo dono. Um mesmo carregador não pode ficar ligado a duas
sessões abertas ao mesmo tempo. O preço é copiado para a sessão quando ela é
criada, então uma alteração posterior não muda uma cobrança já iniciada.

Os valores usados para os cálculos de energia (potência do carregador,
tarifa de energia, capacidade de bateria) estão centralizados no topo de
`painel/models.py` — troque ali se o time tiver dados reais de um
carregador/fornecedor específico depois.

Veja `REGISTRO_INTEGRACAO.md` na raiz do projeto para o histórico
completo de como os dois projetos originais foram unidos.

### Próximos passos sugeridos

- Ligar o painel do operador a mais métricas (histórico, gráficos)
- Integrar um gateway de pagamento real (ex. Mercado Pago, Stripe) se o
  time decidir ir além do protótipo de interface
- Testar a leitura de QR Code em um celular real (a lib `html5-qrcode`
  precisa de HTTPS ou `localhost` para acessar a câmera)
- Trocar `CHARGER_POWER_KW` em `painel/models.py` pelo valor real do
  hardware do GoodWe Challenge, quando disponível

## Banco de dados

Por padrão usa SQLite (arquivo `db.sqlite3`, criado automaticamente). Serve bem para desenvolvimento e sites pequenos. Se precisar de PostgreSQL/MySQL no futuro, é só trocar a configuração em `DATABASES` no `core/settings.py`.
