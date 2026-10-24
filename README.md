# K86 Display Studio 🦈🖥️

Painel de controle visual e daemon de sincronização em segundo plano para a tela LCD colorida panorâmica (240x128 pixels, ST7789 IPS) do teclado **Attack Shark K86**.

Monitora em tempo real as cotas de uso de inteligência artificial (Anthropic Claude, OpenAI Codex, Antigravity/Gemini, GitHub Copilot, Cursor, OpenCode, xAI Grok e Z.ai GLM), além de métricas locais do sistema (CPU/RAM).

## Estado do suporte multiplataforma

O Linux continua sendo a plataforma de instalação oficialmente suportada. A preparação para Windows e macOS começou com a separação da descoberta e comunicação HID: Linux mantém `hidraw`, enquanto Windows/macOS usam HIDAPI. No ambiente Python do macOS, instale a dependência com `python -m pip install hidapi`; no MSYS2/UCRT64, use o pacote `mingw-w64-ucrt-x86_64-python-hid`.

O código agora inclui caminhos de execução do daemon, inicialização no login e fontes de tela para Windows e macOS. Os instaladores nativos estão sendo preparados; o acesso HID ainda precisa ser validado com o teclado K86 conectado antes de considerar essas plataformas oficialmente suportadas.

O workflow [Build native installers](.github/workflows/native-installers.yml) prepara o instalador Windows x64 (`.exe`) e imagens macOS Intel/Apple Silicon (`.dmg`). Ele pode ser iniciado manualmente em **Actions** ou automaticamente ao publicar uma tag `v*`; nas tags, os três arquivos são anexados à release do GitHub. Os pacotes são experimentais até serem abertos em cada sistema e testados com o K86. Os builds não são assinados: no macOS o Gatekeeper pode exigir que o usuário autorize a abertura.

As dependências Python compartilhadas estão em [`requirements.txt`](requirements.txt). GTK 4 e PyGObject precisam ser fornecidos pelo sistema; o [guia oficial PyGObject](https://pygobject.gnome.org/getting_started.html) documenta a instalação por plataforma. No Windows, a instalação indicada usa MSYS2/UCRT64; no macOS, Homebrew. A interface também depende de Libadwaita, disponível como pacote MSYS2 e Homebrew.

Para preparar um ambiente de desenvolvimento:

```bash
# macOS (Homebrew)
brew install pygobject3 gtk4 libadwaita hidapi
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 k86_display_studio.py
```

No Windows, use o terminal UCRT64 do MSYS2 e instale com `pacman` `mingw-w64-ucrt-x86_64-python`, `mingw-w64-ucrt-x86_64-python-gobject`, `mingw-w64-ucrt-x86_64-gtk4`, `mingw-w64-ucrt-x86_64-libadwaita`, `mingw-w64-ucrt-x86_64-python-pillow`, `mingw-w64-ucrt-x86_64-python-psutil` e `mingw-w64-ucrt-x86_64-python-hid`. Depois rode `python k86_display_studio.py` nesse terminal. O PyGObject pode exigir configurar `PYGI_DLL_PATH` para localizar as DLLs do MSYS2; siga o [guia de instalação Windows](https://pygobject.gnome.org/getting_started.html#windows).

O serviço `systemd` continua disponível apenas no Linux. Em Windows/macOS, a interface inicia e reinicia o daemon como processo de usuário separado. A opção “Iniciar daemon ao entrar no sistema” registra sua inicialização no login do usuário: via Task Scheduler no Windows e LaunchAgent no macOS. O log fica em `k86-screen-daemon.log` dentro do diretório de configuração do usuário.

As pastas de dados e configurações podem ser direcionadas com `K86_DATA_DIR` e `K86_CONFIG_DIR`, respectivamente. Isso permite apontar o monitor para os arquivos de cotas usados por outra instalação ou aplicativo.

---

## 📁 Estrutura do Projeto

```text
k86-display-studio/
├── k86_display_studio.py     # Aplicativo desktop GTK 4 + Libadwaita
├── k86_renderer.py           # Motor de renderização e composição 240x128
├── k86_config.py             # Schema, validação e persistência atômica
├── k86_trio_daemon.py        # Daemon com hot-reload automático
├── k86_service.py            # Controle do daemon por plataforma
├── k86_trio_monitor.py       # Transporte USB HID por plataforma
├── requirements.txt          # Dependências Python compartilhadas
├── k86_screen_token.py       # Utilitário de telemetria de tokens
├── k86_calibrate_width.py    # Régua e calibrador de largura física
├── packaging/                # Build PyInstaller e instalador Windows/macOS
├── install.sh                # Script de instalação automatizada
├── uninstall.sh              # Script de desinstalação
├── udev/                     # Regras udev de permissão USB
│   └── 99-k86.rules
├── systemd/                  # Definição do serviço de usuário systemd
│   └── k86-screen.service
├── tests/                    # Suíte completa de testes automatizados
│   ├── test_k86_config.py
│   ├── test_k86_daemon.py
│   ├── test_k86_display_studio.py
│   ├── test_k86_install.py
│   └── test_k86_renderer.py
└── assets/                   # Imagens e pré-visualizações geradas
```

---

## 📦 Instalação

### Opção 1: Baixar o Pacote Pronto (.deb / .tar.gz) 🚀
Você pode baixar os instaladores prontos diretamente na [página de Releases](https://github.com/aguerreiropereira/k86monitor-IA/releases/latest):

* **Ubuntu / Debian / Pop!_OS / Linux Mint:** Baixe o arquivo `k86monitor-ia_1.0.0_all.deb` e instale com dois cliques ou:
  ```bash
  sudo apt install ./k86monitor-ia_1.0.0_all.deb
  ```
  *(O pacote `.deb` já configura automaticamente as dependências, regras udev e o serviço de segundo plano).*

* **Universal (Fedora, Arch, etc.):** Baixe `k86monitor-ia-1.0.0.tar.gz`, extraia e execute `./install.sh`.

### Opção 2: Instalação via Código Fonte (Git)
Clone o repositório e execute o script de instalação para configurar os atalhos, ícones e serviço de usuário:

```bash
git clone https://github.com/aguerreiropereira/k86monitor-IA.git
cd k86monitor-IA
./install.sh
```

### Permissões USB (Udev)
Para permitir que seu usuário comunique diretamente com o visor sem necessidade de `sudo`:

```bash
sudo cp udev/99-k86.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

---

## 🚀 Como Usar

### 1. Interface Gráfica (K86 Display Studio)
Abra pelo menu de aplicativos do GNOME procurando por **K86 Display Studio** ou via terminal:
```bash
k86-display-studio
```

Na interface você pode:
- **Modo Foco (1 Modelo)**: Ao deixar apenas 1 provedor ativado, a tela de 240x128 expande automaticamente para layout imersivo com logo grande de 48x48 px, porcentagens destacadas em 14pt e barras largas de alta visibilidade.
- **Modo Multi-provedores**: Ao ativar 2 ou mais provedores, o visor se divide dinamicamente em slots adaptativos.
- Ativar/desativar provedores individualmente (Claude, Codex, Antigravity, Copilot, Cursor, OpenCode, Grok, GLM).
- Alternar barras de limites (5 Horas e Semanal).
- Ativar medição de consumo local de CPU e RAM.
- Visualizar o preview com fidelidade de pixels (escala 2x: 480x256).
- Salvar e aplicar diretamente no teclado com 1 clique.

---

## ⚙️ Gerenciamento do Serviço (Systemd)

O daemon opera de forma contínua em segundo plano via serviço de usuário:

```bash
# Verificar status
systemctl --user status k86-screen.service

# Reiniciar serviço
systemctl --user restart k86-screen.service

# Visualizar logs em tempo real
journalctl --user -u k86-screen.service -f
```

---

## 🔒 Permissões USB (Udev)

O dispositivo `0x3151:0x4015` requer acesso de leitura/escrita no nó `hidraw`. Uma regra udev está instalada em `/etc/udev/rules.d/99-k86.rules`:

```udev
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="3151", ATTRS{idProduct}=="4015", MODE="0666", GROUP="plugdev", TAG+="uaccess"
```

---

## 🧪 Testes Automatizados

Para rodar todos os testes unitários:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

---

## 📄 Licença

Distribuído sob a licença MIT. Consulte [`LICENSE`](LICENSE) para mais informações.
