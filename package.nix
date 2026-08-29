{
  lib,
  python3Packages,
  makeWrapper,
  # The opencode2 CLI used for consultas. The flake pins it from the
  # llm-agents input; the NixOS module default falls back to the system
  # profile, which provides opencode2 itself.
  opencode2 ? null,
  tesseract,
  ydotool,
  libnotify,
  glib,
  wl-clipboard,
}:

let
  python = python3Packages.python;
  pythonPath = lib.makeSearchPath "lib/${python.libPrefix}/site-packages" [
    python
    python3Packages.dbus-next
  ];
  sourceFiles = lib.fileset.toSource {
    root = ./.;
    fileset = lib.fileset.unions [
      ./flake.lock
      ./flake.nix
      ./module.nix
      ./package.nix
      ./tests
      ./tools
      ./vicre
      ./fuentes
    ];
  };
  extractionPython = python3Packages.python.withPackages (ps: [ ps.pypdf ]);
  tesseractCourse = tesseract.override {
    enableLanguages = [
      "eng"
      "spa"
    ];
  };
  binPaths =
    lib.optionals (opencode2 != null) [ opencode2 ]
    ++ [
      tesseractCourse
      ydotool
      libnotify
      glib
      wl-clipboard
    ];
in
python3Packages.buildPythonApplication {
  pname = "vicre";
  version = "0.1.0";
  format = "other";

  src = sourceFiles;

  propagatedBuildInputs = [ python3Packages.dbus-next ];

  nativeBuildInputs = [ makeWrapper ];

  doCheck = true;
  checkPhase = ''
    runHook preCheck
    ${python.interpreter} -m unittest discover -s tests -v
    runHook postCheck
  '';

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
      --prefix PATH : "${lib.makeBinPath binPaths}" \
      --add-flags "-m vicre.__main__"

    mkdir -p "$out/share/vicre"
    mkdir -p "$out/share/vicre/fuentes"
    ${extractionPython.interpreter} tools/extract_fuentes.py \
      fuentes/Ejercicios_y_Respuestas.pdf "$out/share/vicre/fuentes"
  '';

  meta = {
    description = "Screen-capture assistant that queries OpenCode using compact runtime procedure cards";
    mainProgram = "vicre";
    platforms = lib.platforms.linux;
  };
}
