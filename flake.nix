{
  description = "Solaar development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          evdev
          pyudev
          pyyaml
          xlib
          psutil
          dbus-python
          pygobject3
          typing-extensions
          
          # Dev dependencies
          pytest
          pytest-mock
          pytest-cov
          ruff
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          nativeBuildInputs = [
            pkgs.gobject-introspection
            pkgs.wrapGAppsHook3
          ];

          buildInputs = [
            pythonEnv
            pkgs.gtk3
            pkgs.gtk4
            pkgs.libnotify
            pkgs.udev
            pkgs.gdk-pixbuf
            pkgs.glib
            pkgs.gsettings-desktop-schemas
          ];

          shellHook = ''
            export PYTHONPATH=$PYTHONPATH:$(pwd)/lib
            echo "Solaar development environment loaded."
            echo "You can run solaar with: bin/solaar"
            echo "If you need root permissions (e.g. for device access without udev rules), use: sudo -E bin/solaar"
          '';
        };
      }
    );
}
