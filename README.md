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
  - GPUs antigas (Mali-T, Adreno 3xx/4xx, PowerVR): usa OpenGL ES em vez de Vulkan.
  - Perfil alto (6 GB ou mais): não mexe em nada.
- **Modo de segurança**: se o app cair ou for morto por falta de memória 2 vezes seguidas durante
  um jogo, ele volta sozinho para o perfil mais leve e para o OpenGL ES na próxima abertura.
  Fechar o app deslizando nas recentes não conta (Android 11 ou mais novo).
- **Modo de desempenho sustentado** (perfis mínimo e baixo): pede ao Android para manter
  o clock estável durante o jogo, em vez de acelerar e depois reduzir por calor. Aparelhos sem
  suporte ignoram o pedido.
- **Áudio contínuo em celulares lentos** (perfis mínimo e baixo): liga o "Audio stretching".
  Lendo o código do áudio, sem ele a saída repete a última amostra sempre que o jogo roda abaixo
  da velocidade real, o que soa como chiado. Com ele o som fica contínuo e com o tom certo, ao
  custo de um pouco de CPU e cerca de 100 ms de atraso. Dá para desligar nas configurações.
  Quando o perfil muda numa atualização ele é aplicado de novo uma vez.
- **Menus**: a tela inicial ganhou **Perfil de desempenho** (mostra o perfil escolhido, a RAM e os
  núcleos, e permite aplicar o perfil automático de novo). O botão do Discord, na tela "Sobre",
  abria o servidor do Azahar; agora abre a página de problemas do seu repositório, com um ícone de
  ajuda no lugar da logo do Discord.
- **Registro de desempenho** (`PerfLogger.kt`): a cada 10 segundos de jogo grava no log uma linha
  `[Brisa3DS perf]` com FPS, velocidade, tempo de GPU, troca de quadro, IPC, SVC, o resto
  (principalmente a CPU emulada) e a RAM livre. É a base para decidir qual núcleo otimizar.
- **Memória sob demanda** (`src/core/memory.cpp`): o Azahar reservava e zerava 256 MB de RAM do 3DS
  na abertura, mesmo para jogos que usam bem menos. Agora essa RAM só ocupa memória real quando o
  jogo a usa. Em um teste isolado a reserva caiu de 256 MB para 0 MB, mas o ganho dentro do
  emulador depende de cada jogo e ainda não foi medido num aparelho.
- **Menos memória de GPU em celulares fracos** (`0002-low-ram-memory.patch`): o renderizador
  Vulkan reservava um buffer de upload de 512 MB e um de 64 MB para vértices, em qualquer
  aparelho. Agora o tamanho depende da RAM total: até 3 GB usa 96 MB e 32 MB, até 6 GB usa
  256 MB e 64 MB, acima disso fica como era. Quanto disso é RAM física de verdade depende do
  driver da GPU, então o ganho exato não foi medido.
- **Limpeza do cache de texturas com pouca RAM**: o cache do Azahar só descarta texturas
  invalidadas pelo jogo e nunca por falta de memória. Agora, a cada 2 segundos, o app lê
  `/proc/meminfo`. Se sobrar menos de 10% da RAM e menos de 300 MB, ele descarta as texturas
  em cache (elas são refeitas quando preciso), o que causa um engasgo em vez de o Android
  matar o app. Depois da limpeza espera 10 segundos antes de tentar de novo. A mensagem
  "Host memory is low" aparece no log quando isso acontece.
- **APK experimental de 32 bit** (`armeabi-v7a`): o código do Azahar já sabe rodar sem o JIT
  (usa o interpretador), então o workflow também compila uma versão 32 bit com o interpretador.
  Ela será **bem mais lenta**, serve só para jogos leves, e pode falhar na compilação porque
  nunca foi compilada. Se falhar, o APK de 64 bit sai normalmente.
- **Só arm64-v8a no build principal** (sem x86_64): APK menor.
- **Logo própria** (`assets/logo.png`): ícone do app, ícone temático (Android 13), logo das telas
  internas e ícone de notificação. Para trocar a logo, substitua o PNG e rode
  `python3 tools/make_icons.py` (precisa do Pillow).
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

- O código do Azahar é licenciado em GPLv3 ou posterior (alguns trechos herdados do Citra e do
  yuzu são GPLv2 ou posterior, como indicam os cabeçalhos de cada arquivo), e este projeto segue a
  mesma licença. Se você
  distribuir o APK, precisa também disponibilizar o código-fonte com as mudanças (este
  repositório faz esse papel) e manter os créditos ao Azahar e ao Citra.
- Não envie estas mudanças ao projeto Azahar original: a política de IA deles proíbe
  contribuições com código escrito por IA (veja `AI-POLICY.md` no repositório deles).
- O APK nunca foi testado em um aparelho: os perfis são estimativas e podem precisar de ajuste.

## Correções de travamento incluídas

- **Fecha ao escolher a pasta** (`Missing declaration for key 'battery_state_source'` no
  `azahar_log.txt`): o arquivo de configuração padrão do Android do Azahar não declarava 3
  chaves de bateria, e o app aborta na verificação logo após a escolha da pasta. O script
  `tools/fix_default_ini.py` adiciona as chaves que faltam. Se o Azahar já tiver corrigido,
  ele não faz nada.

## Log de erro do build

Se um build falhar, baixe o arquivo **build-log-arm64-v8a** ou **build-log-armeabi-v7a** na
página da execução (aba Actions). Ele tem as últimas 700 linhas do build, que é o que eu preciso
para corrigir o erro.

## Análise do build de 32 bit (armeabi-v7a)

Feita lendo o código, sem compilar. Problemas encontrados e corrigidos só no build de 32 bit
(`tools/fix_32bit.py`):

1. `common/atomic_ops.h` usa `unsigned __int128`, que não existe em 32 bit. Agora, sem suporte a
   128 bit, usa uma versão com trava. Só guests de 64 bit usam isso, e o 3DS não usa. Testado
   isoladamente nos dois ramos.
2. O vulkan-hpp desliga a conversão automática entre `vk::Image` e `VkImage` em 32 bit, mas o
   renderizador (e as chamadas do VMA) dependem dela. O script liga
   `VULKAN_HPP_TYPESAFE_CONVERSION` para o `video_core` nesse caso.
3. `#ifdef CITRA_ARCH_arm64` no `native.cpp` é sempre verdadeiro, então o 32 bit ofereceria
   drivers de GPU personalizados que não carregam. Trocado por `#if CITRA_ARCH(arm64)`.

Verificado e sem problema: detecção de arquitetura no CMake (cai em GENERIC), Dynarmic/xbyak/
oaknut/adrenotools (só 64 bit, já protegidos), JIT de shader (cai no interpretador), NEON em
`vector_math.h`, `math_util.cpp` e `texture_codec.h`, FFmpeg (desligado no Android).

O que não dá para saber sem compilar: erros de tipo do tipo `std::min(size_t, u64)` e
dependências externas (cryptopp, etc.) em ARM de 32 bit. Se o build ainda falhar, o log
**build-log-armeabi-v7a** mostra o próximo erro.

## Ajustes do JIT que foram avaliados e descartados

Com o código do Dynarmic em mãos, conferi cada opção de ajuste antes de mexer:

- `DYNARMIC_IGNORE_ASSERTS`: sem efeito, porque o build de release já define `NDEBUG`, que
  desliga as asserções.
- `code_cache_size` menor: não economiza RAM. O cache de código é uma reserva de endereços e só
  ocupa memória real conforme o código é gerado.
- `always_little_endian`: o ganho é desprezível (só afeta a escrita do CPSR).
- Otimizações "unsafe" de ponto flutuante: aceleram, mas mudam o tratamento de NaN e podem
  quebrar jogos. Ficam desligadas.
- Um backend ARM32 novo: o backend ARM64 do Dynarmic tem cerca de 13 mil linhas e usa o
  assembler `oaknut`, que só existe para ARM64. Para 32 bit seria preciso escrever um assembler
  e um backend do zero, sem poder compilar aqui. Por isso o 32 bit usa o interpretador.

## Revisão dos módulos (`externals`)

Só entram no Android os módulos que o CMake liga com as opções do app (Qt, SDL e GDB stub
desligados). Resultado da revisão:

**Lidos com atenção:** dynarmic, cryptopp, libressl, sirit, spirv-tools, soundtouch, teakra, cubeb.
- **sirit** é sempre compilado com `-Werror`, `-pedantic-errors`, `-Wconversion` e
  `-Wsign-conversion`. Em 32 bit isso gera muito mais avisos, e cada um viraria erro. O
  `fix_32bit.py` tira só o caráter de erro, mantendo os avisos.
- **spirv-tools** usa `-Werror` por padrão (`SPIRV_WERROR=ON`). No 32 bit passamos
  `-DSPIRV_WERROR=OFF`.
- **libressl** monta código assembly ARMv4 em ARM de 32 bit. No 32 bit passamos
  `-DENABLE_ASM=OFF`, já que só o serviço web usa isso.
- **cryptopp, soundtouch, teakra, cubeb, xxHash**: já tratam ARM de 32 bit (NEON, uso de
  `__int128` protegido). Nada a mudar.

**Só varridos por busca (sem leitura completa):** faad2, libyuv, enet, inih, lodepng, zstd,
microtar, nihstro, dds-ktx, glad, boost, libusb, openal-soft, vma, vulkan-headers, glslang, fmt.
Nenhum apareceu com `__int128` sem proteção nem com suposição de 64 bit.

**Não entram no Android:** xbyak (só x86_64), libadrenotools (só arm64), sdl2, catch2 (só em
testes), discord-rpc, gamemode, libretro-common.

OpenAL continua ligado de propósito: ele aparece como opção de saída de áudio no app.

## Estrutura do projeto

| Pasta ou arquivo | Para que serve |
|---|---|
| `overlay/` | Código novo copiado para dentro do Azahar (`DeviceProfile.kt`, ícones). |
| `patches/` | Mudanças em arquivos que já existem no Azahar. |
| `tools/apply.sh` | Aplica tudo sobre uma cópia do Azahar (o workflow usa este). |
| `tools/rename.py`, `fix_default_ini.py`, `fix_32bit.py` | Troca de nome, correção do travamento de configuração e ajustes só do 32 bit. |
| `tools/verify_default_ini.py` | Confere se a configuração padrão do Android está completa (a mesma checagem que derrubava o app). |
| `tools/make_icons.py` | Gera o ícone e os logos a partir de `assets/logo.png`. |
| `tools/compat_table.py` | Gera `compat/TABELA.md` a partir de `compat/resultados.csv`. |
| `.github/workflows/build-apk.yml` | Compila os APKs e publica em Releases. |
| `.github/workflows/upstream-check.yml` | Toda segunda-feira confere, em poucos minutos, se o Azahar mais novo ainda aceita as mudanças. |
| `.github/ISSUE_TEMPLATE/` | Formulários de problema e de relatório de desempenho. |
| `docs/USO.md` | Guia para quem vai instalar e usar. |
| `NOTICE.md`, `LICENSE` | Créditos e licença (GPLv3 ou posterior), que precisam acompanhar o projeto. |
| `tools/rebrand_links.py` | Aponta os links do app e o verificador de atualização para o seu repositório. |
| `tools/add_home_entry.py` | Acrescenta a opção Perfil de desempenho ao menu da tela inicial. |

O workflow `upstream-check` não compila o app. Se ele falhar, o Azahar mudou algo que as
mudanças do Brisa3DS precisam acompanhar. Você recebe o aviso do GitHub antes de gastar um build.
