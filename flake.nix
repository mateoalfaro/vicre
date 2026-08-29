{
  description = "Vicre - screen-capture assistant that queries OpenCode using the course master workbook";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  inputs.llm-agents.url = "github:numtide/llm-agents.nix";

  outputs =
    { self, nixpkgs, llm-agents }:
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
        vicre = nixpkgs.legacyPackages.${system}.callPackage ./package.nix {
          opencode2 = llm-agents.packages.${system}.opencode2;
        };
        default = self.packages.${system}.vicre;
      });

      nixosModules = {
        vicre = import ./module.nix;
        default = import ./module.nix;
      };
    };
}
