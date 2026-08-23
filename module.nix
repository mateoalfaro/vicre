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
    model = lib.mkOption {
      type = lib.types.str;
      default = "openai/gpt-5.6-sol";
      description = "Model (provider/model) that vicre uses for the consulta. Must support image input.";
    };
    variant = lib.mkOption {
      type = lib.types.str;
      default = "medium";
      description = "Reasoning variant passed to opencode run --variant.";
    };
    systemd = {
      enable = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = ''
          Set up vicre as systemd user services (autostarting daemon and
          GNOME keybind applier). They are user units because the screenshot
          portal and the session bus only exist inside the graphical session.
          When disabled, only the package, ydotool and group membership are
          configured; start `vicre daemon` yourself.
        '';
      };
    };
  };

  config = lib.mkMerge [
    (lib.mkIf cfg.enable (lib.mkMerge [
      {
        programs.ydotool.enable = true;
        environment.systemPackages = [ cfg.package ];
      }
      (lib.mkIf cfg.systemd.enable {
        systemd.user.services.vicre = {
          description = "Vicre daemon";
          wantedBy = [ "graphical-session.target" ];
          partOf = [ "graphical-session.target" ];
          after = [ "graphical-session.target" ];
          serviceConfig = {
            Type = "simple";
            ExecStart = "${cfg.package}/bin/vicre daemon";
            Restart = "on-failure";
            Environment = [
              "VICRE_MODEL=${cfg.model}"
              "VICRE_VARIANT=${cfg.variant}"
            ];
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
      })
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
