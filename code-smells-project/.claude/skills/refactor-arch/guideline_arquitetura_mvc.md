# 🏛️ Guidelines da Arquitetura MVC Alvo

Este documento define o contrato de responsabilidades e a estrutura física de diretórios para a refatoração MVC.

## 📂 Estrutura Alvo de Diretórios

```text
src/
├── config/             # Configurações de ambiente, variáveis e conexão com banco
│   ├── database.js / database.py
│   └── config.js / config.py
├── models/             # Entidades, esquemas do banco e métodos de acesso aos dados (DAO/Repository)
├── controllers/        # Regras de negócio, validações de entrada e orquestração
├── routes/             # Definição das rotas HTTP e vinculação com os Controllers
├── middlewares/        # Middlewares de tratamento de erros, CORS e autenticação
└── app.js / app.py     # Entrypoint da aplicação (inicialização limpa do servidor)