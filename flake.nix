{
  description = "Vicre - screen-capture assistant that queries OpenCode using bundled course PDFs";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = f: builtins.listToAttrs (map (system: {
        name = system;
        value = f system;
      }) systems);
    in
    {
      packages = forAllSystems (system: {
        vicre = nixpkgs.legacyPackages.${system}.callPackage ./package.nix { };
        default = self.packages.${system}.vicre;
      });

      nixosModules = {
        vicre = import ./module.nix;
        default = import ./module.nix;
      };
    };
}
