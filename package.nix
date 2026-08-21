{
  lib,
  python3Packages,
  makeWrapper,
  opencode,
  ydotool,
  libnotify,
  glib,
}:

let
  python = python3Packages.python;
  pythonPath = lib.makeSearchPath "lib/${python.libPrefix}/site-packages" [
    python
    python3Packages.dbus-next
  ];
in
python3Packages.buildPythonApplication {
  pname = "vicre";
  version = "0.1.0";
  format = "other";

  src = ./.;

  propagatedBuildInputs = [ python3Packages.dbus-next ];

  nativeBuildInputs = [ makeWrapper ];

  dontWrapPythonPrograms = true;

  postInstall = ''
    site="$out/lib/${python.libPrefix}/site-packages"
    mkdir -p "$site"
    cp -r vicre "$site/"

    mkdir -p "$out/bin"
    makeWrapper "${python.interpreter}" "$out/bin/vicre" \
      --prefix PYTHONPATH : "${pythonPath}" \
      --prefix PYTHONPATH : "$site" \
      --set VICRE_FUENTES_DIR "$out/share/vicre/fuentes" \
      --set VICRE_BIN "$out/bin/vicre" \
      --prefix PATH : "${lib.makeBinPath [ opencode ydotool libnotify glib ]}" \
      --add-flags "-m vicre.__main__"

    mkdir -p "$out/share/vicre"
    cp -r fuentes "$out/share/vicre/fuentes"
  '';

  meta = {
    description = "Screen-capture assistant that queries OpenCode using bundled course PDFs";
    mainProgram = "vicre";
    platforms = lib.platforms.linux;
  };
}
