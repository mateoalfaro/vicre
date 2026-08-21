# Vicre

Servicio de usuario para GNOME Wayland: capturas la pantalla con `ctrl+i`, Vicre le pregunta a OpenCode usando los PDFs del curso (`fuentes/`), y luego escribe la respuesta directamente en la ventana enfocada.

## Atajos

| Atajo | Acción |
|---|---|
| `ctrl+i` | Captura toda la pantalla → consulta a OpenCode → guarda las dos respuestas |
| `ctrl+o` | Escribe la **Respuesta Tipo 1** (respuestas directas) donde esté escribiendo |
| `ctrl+p` | Escribe la **Respuesta Tipo 2** (código Wolfram de verificación) |

La captura usa el portal de screenshots (funciona en GNOME y wlroots), la escritura usa `ydotool`/uinput. El éxito es silencioso; los errores llegan como notificación.

## Instalación (NixOS)

En `/etc/nixos/configuration.nix`:

```nix
{
  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  imports = [
    (builtins.getFlake "path:/home/jafed/devwork/vicre").nixosModules.default
  ];

  programs.vicre = {
    enable = true;
    user = "jafed";
  };
}
```

Luego `sudo nixos-rebuild switch` y **vuelve a iniciar sesión** (necesario para el grupo `ydotool`). Los atajos se registran solos al iniciar la sesión gráfica.

## Layout en runtime

```
~/.vicre/
├── photos/    capturas PNG
├── fuentes/   symlink a los PDFs dentro del paquete de Nix
└── state.json última respuesta parseada
```

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
