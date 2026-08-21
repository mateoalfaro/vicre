{
  lib,
  config,
  pkgs,
  ...
}:

let
  cfg = config.programs.vicre;
in
{
  options.programs.vicre = {
    enable = lib.mkEnableOption "vicre";
    package = lib.mkOption {
      type = lib.types.package;
      default = pkgs.callPackage ./package.nix { };
      description = "The vicre package to use.";
    };
    user = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = "User to add to the ydotool group.";
    };
  };

  config = lib.mkMerge [
    (lib.mkIf cfg.enable (lib.mkMerge [
      {
        programs.ydotool.enable = true;

        systemd.user.services.vicre = {
          description = "Vicre daemon";
          wantedBy = [ "graphical-session.target" ];
          partOf = [ "graphical-session.target" ];
          after = [ "graphical-session.target" ];
          serviceConfig = {
            Type = "simple";
            ExecStart = "${cfg.package}/bin/vicre daemon";
            Restart = "on-failure";
          };
        };

        systemd.user.services.vicre-keybinds = {
          description = "Vicre apply-keybinds";
          wantedBy = [ "graphical-session.target" ];
          after = [ "graphical-session.target" ];
          serviceConfig = {
            Type = "oneshot";
            ExecStart = "${cfg.package}/bin/vicre apply-keybinds";
          };
        };
      }
      (lib.mkIf (cfg.user != null) {
        users.users.${cfg.user}.extraGroups = [ "ydotool" ];
      })
    ]))
    {
      assertions = [
        {
          assertion = !cfg.enable || cfg.user != null;
          message = "programs.vicre.user must be set when programs.vicre.enable is true.";
        }
      ];
    }
  ];
}
