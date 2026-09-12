{
  description = "Vicre - screen-capture assistant that queries the Gemini CLI (antigravity) using the course master workbook";

  # Prebuilt closures for the llm-agents inputs (antigravity-cli and
  # friends). Nix asks for one-time confirmation unless this flake is already
  # trusted.
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
      # Note: antigravity-cli (agy) comes from llm-agents (numtide cache), not
      # from nixpkgs, so no unfree-allowance is needed to build vicre.
      packages = forAllSystems (system: {
        vicre = nixpkgs.legacyPackages.${system}.callPackage ./package.nix {
          antigravity-cli = llm-agents.packages.${system}.antigravity-cli;
        };
        default = self.packages.${system}.vicre;
      });

      checks = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          expectedPackage = self.packages.${system}.vicre;
          modulePackage = (nixpkgs.lib.nixosSystem {
            inherit system;
            modules = [
              self.nixosModules.default
              {
                programs.vicre = {
                  enable = true;
                  user = "vicre";
                };
                system.stateVersion = "25.11";
              }
            ];
          }).config.programs.vicre.package;
        in
        {
          module-package =
            assert modulePackage.outPath == expectedPackage.outPath;
            pkgs.runCommand "vicre-module-package-${system}" { } ''
              touch "$out"
            '';
        }
      );

      nixosModules =
        let
          module =
            { lib, pkgs, ... }:
            {
              imports = [ ./module.nix ];
              config.programs.vicre.package =
                lib.mkDefault self.packages.${pkgs.stdenv.hostPlatform.system}.vicre;
            };
        in
        {
          vicre = module;
          default = module;
        };
    };
}