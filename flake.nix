{
  description = "Vicre - screen-capture assistant that queries OpenCode using the course master workbook";

  # Prebuilt closures for the llm-agents inputs (opencode2 and friends).
  # Nix asks for one-time confirmation unless this flake is already trusted.
  nixConfig = {
    extra-substituters = [ "https://cache.numtide.com" ];
    extra-trusted-public-keys = [
      "niks3.numtide.com-1:DTx8wZduET09hRmMtKdQDxNNthLQETkc/yaX7M4qK0g="
    ];
  };

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
