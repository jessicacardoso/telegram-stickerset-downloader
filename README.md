# Telegram StickerSet Downloader

Aplicação em python responsável por baixar todos os stickers contidos em uma lista de canais.

## Pré-requisitos

Para utilizar essa ferramenta, é necessária a criação de uma *API KEY* do *Telegram* e autorizar o uso do aplicativo através do número de telefone informado, além de um banco de dados postgresql. Via docker pode ser criado com o seguinte comando:

```sh
docker run -d \
    --name some-postgres \
    -e POSTGRES_PASSWORD=mysecretpassword \
    -e PGDATA=/var/lib/postgresql/data/pgdata \
    -v /var/tmp/postgresql:/var/lib/postgresql/data \
    -p 5432:5432 \
    postgres
```

### Telegram API KEY
Ter uma **TELEGRAM API KEY** (*api_id* e *api_hash* pair) válido, para isso:

1. Visite https://my.telegram.org/apps e faça login em sua conta do Telegram.

2. Preencha o formulário com seu número completo, incluindo código do país e DDD, em seguida registre uma nova aplicação do *Telegram*.

3. Pronto. A API key é composta de duas partes: api_id e api_hash. Guarde-as e não as deixe visível no projeto.

### Autorizar aplicativo

Copie o arquivo `config.yaml` para o caminho ` ~/.config/StickerApp/config.yaml`, substitua os campos *api_id* e *api_hash* com as informações obtidas na seção anterior. Em seguida, instale as dependências contidas no `requirements.txt`, execute o código python `user_auth.py`e informe seu número de telefone e o código de confirmação enviado via Telegram. Abaixo, mostramos a mensagem que apareceu em nosso terminal.

```bash
Welcome to Pyrogram (version 2.0.30)
Pyrogram is free software and comes with ABSOLUTELY NO WARRANTY. Licensed
under the terms of the GNU Lesser General Public License v3.0 (LGPL-3.0).

Enter phone number or bot token: +55-98-7654-3210
Is "+55-98-7654-3210" correct? (y/N): y
The confirmation code has been sent via Telegram app
Enter confirmation code: 12345
^C% 
```

Depois da autorização ser realizada com sucesso, podemos encerrar o processo anterior, o arquivo `my_account.session` na raiz do projeto nos permite interagir com nosso usuário do Telegram.


## Rodando a aplicação
Execute o arquivo `db.py` para criar as tabelas do banco de dados, em seguida rode o *script* `scraper.py`, selecione os canais de interesse e aguarde o download.

