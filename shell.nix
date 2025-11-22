{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    evdev
    pyudev
    pyyaml
    xlib
    psutil
    dbus-python
    pygobject3
    typing-extensions
    pydbus
    
    # Dev dependencies
    pytest
    pytest-mock
    pytest-cov
    ruff
  ]);
in
pkgs.mkShell {
  nativeBuildInputs = [
    pkgs.gobject-introspection
    pkgs.wrapGAppsHook3
  ];

  buildInputs = [
    pythonEnv
    pkgs.gtk3
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
  '';
}
