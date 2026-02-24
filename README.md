# Ping Monitor

Aplicativo desktop em Python/Tkinter para monitorar hosts por ICMP (ping), com arquitetura modular.

## Estrutura (boas praticas)

- `main.py`: entrypoint simples.
- `src/ping_monitor/app.py`: bootstrap da aplicacao.
- `src/ping_monitor/ui/main_window.py`: camada de interface.
- `src/ping_monitor/services/pinger.py`: regra de ping (com fallback para comando do sistema).
- `src/ping_monitor/services/emailer.py`: envio de alerta por e-mail.
- `src/ping_monitor/models.py`: entidades da aplicacao.
- `src/ping_monitor/config.py`: configuracoes por variavel de ambiente.

## Como executar

1. Python 3.10+ instalado.
2. Instalar dependencias:
   - `python -m pip install -r requirements.txt`
3. Rodar o app:
   - `python main.py`

## Alerta por e-mail (opcional)

Configure as variaveis no sistema:

- `PM_SMTP_SERVER`
- `PM_SMTP_PORT` (default: `587`)
- `PM_SENDER_EMAIL`
- `PM_SENDER_PASSWORD`
- `PM_RECIPIENT_EMAIL`

Teste de e-mail:

- `python mail_test.py`

## Notas tecnicas

- UI atualizada de forma thread-safe usando fila + `after`.
- Alertas enviados somente na transicao para offline.
- Se `ping3` nao estiver disponivel, o app usa `ping` do sistema operacional.
