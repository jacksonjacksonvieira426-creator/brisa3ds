# Brisa3DS

Emulador de Nintendo 3DS para Android pensado para celulares fracos. É um fork do
[Azahar](https://github.com/azahar-emu/azahar), que por sua vez é um fork do Citra. Todo o
mérito do emulador em si é do Azahar e do Citra; este projeto só adiciona ajustes de desempenho.

Este repositório **não contém o código inteiro do Azahar**, só as mudanças (`overlay/`,
`patches/` e `tools/`). O GitHub Actions baixa o Azahar original com todas as dependências,
aplica as mudanças e compila o APK.

## O que muda em relação ao Azahar

- **Perfil automático por aparelho** (`DeviceProfile.kt`): na primeira abertura o app lê a RAM, os
  núcleos de CPU e a GPU e escolhe um perfil (mínimo, baixo, médio ou alto).
  - Resolução interna 1x, shaders assíncronos, cache de shaders em disco, sem filtro de textura.
  - Perfil mínimo (menos de 2,5 GB de RAM): também usa o modo Old 3DS (layout de memória menor). Alguns jogos exigem New 3DS e não abrem assim.
  - GPUs antigas (Mali-T, Adreno 3xx/4xx, PowerVR): usa OpenGL ES em vez de Vulkan.
  - Perfil alto (6 GB ou mais): não mexe em nada.
- **Modo de segurança**: se o app morrer 2 vezes seguidas durante um jogo (normalmente falta de
  memória), ele volta sozinho para o perfil mais leve e para o OpenGL ES na próxima abertura.
- **Modo de desempenho sustentado** (perfis mínimo, baixo e médio): pede ao Android para manter
  o clock estável durante o jogo, em vez de acelerar e depois reduzir por calor. Aparelhos sem
  suporte ignoram o pedido.
- **Memória sob demanda** (`src/core/memory.cpp`): o Azahar reservava e zerava 256 MB de RAM do 3DS
  na abertura, mesmo para jogos que usam bem menos. Agora essa RAM só ocupa memória real quando o
  jogo a usa. Em um teste isolado a reserva caiu de 256 MB para 0 MB, mas o ganho dentro do
  emulador depende de cada jogo e ainda não foi medido num aparelho.
- **APK experimental de 32 bit** (`armeabi-v7a`): o código do Azahar já sabe rodar sem o JIT
  (usa o interpretador), então o workflow também compila uma versão 32 bit com o interpretador.
  Ela será **bem mais lenta**, serve só para jogos leves, e pode falhar na compilação porque
  nunca foi compilada. Se falhar, o APK de 64 bit sai normalmente.
- **Só arm64-v8a no build principal** (sem x86_64): APK menor.
- **Nome e ID próprios** (`app.brisa3ds.emu`): instala ao lado do Azahar normal.

## Como compilar o APK

1. Crie um repositório novo no GitHub e envie o conteúdo desta pasta (arraste os arquivos pelo
   site, mantendo as pastas `.github`, `overlay`, `patches` e `tools`).
2. Abra a aba **Actions**, escolha **build-apk** e clique em **Run workflow**.
3. Quando terminar (leva de 30 a 60 minutos na primeira vez), os APKs aparecem na aba
   **Releases** do repositório, onde dá para baixar direto pelo celular. Ele também fica como
   arquivo **brisa3ds-apk** na página da execução.

O SDK do Android, o NDK e o CMake **não precisam estar no zip**: o workflow instala tudo sozinho
no servidor do GitHub (e baixa o código do Azahar com todas as dependências).

Os APKs saem assinados com chave de debug, o que basta para instalar direto no celular.

## Se o build falhar

- **"no longer applies"** ou erro do `rename.py` no passo *Apply Brisa3DS changes*: o Azahar
  mudou os arquivos que o projeto altera. Rode o workflow com `upstream_ref` apontando para uma
  versão mais antiga, ou envie o log do erro para atualizar o patch.
- Erro de compilação do Kotlin ou do CMake: copie o final do log do passo *Build APK*.

## Importante

- O Azahar é licenciado em GPLv2 ou posterior, e este projeto segue a mesma licença. Se você
  distribuir o APK, precisa também disponibilizar o código-fonte com as mudanças (este
  repositório faz esse papel) e manter os créditos ao Azahar e ao Citra.
- O ícone do app ainda é o do Azahar. Troque por um próprio antes de divulgar.
- Não envie estas mudanças ao projeto Azahar original: a política de IA deles proíbe
  contribuições com código escrito por IA (veja `AI-POLICY.md` no repositório deles).
- O APK nunca foi testado em um aparelho: os perfis são estimativas e podem precisar de ajuste.
