# K86 Display Studio 🦈🖥️

Painel de controle visual e daemon de sincronização em segundo plano para a tela LCD colorida panorâmica (240x128 pixels, ST7789 IPS) do teclado **Attack Shark K86** no Linux.

Monitora em tempo real as cotas de uso de inteligência artificial (Anthropic Claude, OpenAI Codex, Antigravity/Gemini, GitHub Copilot, Cursor, OpenCode, xAI Grok e Z.ai GLM), além de métricas locais do sistema (CPU/RAM).

---

## 📁 Estrutura do Projeto

```text
k86-display-studio/
├── k86_display_studio.py     # Aplicativo desktop GTK 4 + Libadwaita
├── k86_renderer.py           # Motor de renderização e composição 240x128
├── k86_config.py             # Schema, validação e persistência atômica
├── k86_trio_daemon.py        # Daemon com hot-reload automático
├── k86_trio_monitor.py       # Driver de baixo nível HID (ioctl/USB)
├── k86_screen_token.py       # Utilitário de telemetria de tokens
├── k86_calibrate_width.py    # Régua e calibrador de largura física
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

Clone o repositório e execute o script de instalação para configurar os atalhos, ícones e serviço de usuário:

```bash
git clone https://github.com/AndersonGuerreiro/k86-display-studio.git
cd k86-display-studio
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
