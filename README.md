# Vicre

Servicio de usuario para GNOME Wayland: capturas la pantalla con `ctrl+alt+i`, Vicre le pregunta a OpenCode usando el cuadernillo maestro del curso (`fuentes/Ejercicios_y_Respuestas.pdf`, extraído a Markdown navegable en tiempo de compilación), y luego escribe la respuesta directamente en la ventana enfocada.

## Atajos

| Atajo | Acción |
|---|---|
| `ctrl+alt+i` | Captura toda la pantalla → consulta a OpenCode → guarda las dos respuestas |
| `ctrl+alt+o` | Escribe la **Respuesta Tipo 1** (respuestas directas) donde esté escribiendo |
| `ctrl+alt+p` | Escribe la **Respuesta Tipo 2** (código Wolfram de verificación) |

La captura usa el portal de screenshots (funciona en GNOME y wlroots), la escritura usa portapapeles (`wl-copy`) + `ydotool`/uinput con un solo `ctrl+v` (ver `docs/adr/0002-clipboard-paste.md`). El éxito es silencioso; los errores llegan como notificación.

## Instalación (NixOS con flakes)

Vicre solo se distribuye como flake. En tu `flake.nix`:

```nix
{
  inputs.vicre.url = "github:mateoalfaro/vicre";

  outputs = { self, nixpkgs, vicre, ... }: {
    nixosConfigurations.mihost = nixpkgs.lib.nixosSystem {
      modules = [
        vicre.nixosModules.default
        # ...
      ];
    };
  };
}
```

Y en algún módulo de la configuración:

```nix
{
  programs.vicre = {
    enable = true;
    user = "jafed";
    # programs.vicre.systemd.enable = false;  # opt out of the autostart services
    # model = "opencode-go/glm-5.3-flash";   # vision model for the consulta (default)
    # variant = "max";                       # reasoning effort for that model (low|high|max)
  };
}
```

El modelo debe soportar imágenes; las credenciales del proveedor se leen
del archivo de auth de OpenCode (`opencode auth login`). Para probar otro
modelo sin tocar la configuración, usa `VICRE_MODEL` y `VICRE_VARIANT` en
el entorno del daemon.

Luego `sudo nixos-rebuild switch --flake .#mihost` y **vuelve a iniciar sesión** (necesario para el grupo `ydotool`). Los atajos se registran solos al iniciar la sesión gráfica.

## Layout en runtime

```
~/.vicre/
├── photos/               capturas PNG
├── fuentes/              symlink al cuadernillo extraído dentro del paquete de Nix
│   ├── INDICE.md         índice de navegación (partes, capítulos, categorías)
│   ├── ejercicios-capN.md / respuestas-capN.md / complementarios-capN.md / tipo-examen-capN.md
│   ├── apendice-{a,b,c}.md
│   └── funciones-vilcretas.txt   nombres protegidos del curso (validación)
├── opencode.json         agente "vicre" (sin bash/subagentes/task)
├── vicre-agent-prompt.md prompt del agente
└── state.json            última respuesta parseada
```

El PDF maestro (`fuentes/Ejercicios_y_Respuestas.pdf`, 461 páginas) se extrae
a chunks de texto deterministas durante la compilación de Nix
(`tools/extract_fuentes.py`, pypdf). El agente nunca lee el PDF: navega los
chunks con grep/read guiándose por `INDICE.md` (número de ejercicio
`cap.sección.ejer`, categorías tipo examen, capítulo). Las preguntas, claves
y rúbricas de evaluación viven en el cuadernillo del curso, no en este repo.

## CLI

```
vicre capture        # dispara el flujo completo (habla con el daemon)
vicre paste1         # escribe RESPUESTA_TIPO1
vicre paste2         # escribe RESPUESTA_TIPO2
vicre apply-keybinds # registra los atajos en GNOME (idempotente)
vicre daemon         # corre el daemon (lo maneja systemd)
```

## Notas

- La primera captura muestra un permiso de screenshots de GNOME; acéptalo una vez.
- El portal captura todos los monitores en una sola imagen.
- Una captura nueva cancela la consulta anterior en vuelo.
- Ver `docs/adr/0001-gnome-compat-io-strategy.md` para por qué no usamos grim/wtype.
