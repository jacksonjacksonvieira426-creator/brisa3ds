# Brisa3DS: guia de uso

Emulador de Nintendo 3DS para Android, baseado no Azahar e pensado para celulares fracos.

## Requisitos

- Android 10 ou mais novo.
- Celular de 64 bit (o APK `arm64-v8a`) é o recomendado. O APK de 32 bit (`armeabi-v7a`) é
  experimental e bem mais lento.
- Pelo menos 2 GB de RAM. Com menos de 3 GB, espere só os jogos mais leves.
- Você precisa dos seus próprios jogos, copiados de um 3DS que você tem.

## Instalar

1. Abra a aba **Releases** do repositório e baixe o APK da última versão.
2. Abra o arquivo e permita a instalação de apps de fontes desconhecidas, se o Android pedir.
3. O Brisa3DS instala ao lado do Azahar, sem apagar nada dele.

## Primeira abertura

O app escolhe sozinho um perfil de desempenho (mínimo, baixo, médio ou alto) conforme a RAM, os
núcleos e a GPU do celular. Você verá uma mensagem curta dizendo qual perfil foi aplicado.
Ele se aplica uma vez; depois você pode mudar tudo nas configurações.

Se o celular for muito fraco, o perfil usa resolução 1x e shaders assíncronos. GPUs antigas usam
OpenGL ES em vez de Vulkan.

## Modo de segurança

Se o app cair ou for fechado pelo Android por falta de memória 2 vezes seguidas durante um jogo,
na próxima abertura ele volta sozinho para as configurações mais leves e para o OpenGL ES.
Fechar o app deslizando nas recentes não conta.

## Dicas para celulares fracos

- Se o som chiar ou picotar, ative **Audio stretching** (já vem ligado nos perfis mais fracos). Se
  achar que o som atrasa em relação à imagem, desligue.
- Feche outros apps antes de jogar. Com 2 GB, cada aplicativo aberto conta.
- Se um jogo engasga muito, teste trocar Vulkan por OpenGL ES (ou o contrário) nas configurações.
- Se aparecer tela preta, tente trocar a API gráfica antes de qualquer outra coisa.

## Reportar um problema

1. No app, abra as **Configurações** da tela inicial e use **Compartilhar log**.
2. Abra uma issue no repositório e escolha **Problema** (se travou) ou **Relatório de desempenho**.
3. Anexe o log e preencha o modelo, o chip e a RAM do celular.

Enquanto um jogo roda, o app grava no log uma linha a cada 10 segundos, começando por
`[Brisa3DS perf]`. Ela mostra o FPS, a velocidade e para onde vai o tempo de cada quadro, em
milissegundos: `gpu` (comandos da GPU), `swap` (troca de quadro), `ipc` e `svc` (sistema do 3DS) e
`rest` (principalmente a CPU emulada), além da RAM livre. Ao reportar um problema de desempenho,
cole 3 ou 4 dessas linhas: elas dizem o que precisa ser melhorado.

Os relatórios de desempenho alimentam a tabela `compat/TABELA.md`, que ajuda a ajustar os perfis.
