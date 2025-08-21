{
  description = "Ulauncher-pop - Application launcher for Linux with pop-launcher integration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        python = pkgs.python313;
        pythonPackages = python.pkgs;
      in
      {
        packages.default = pythonPackages.buildPythonApplication {
          pname = "ulauncher-pop";
          version = "6.0.0-dev";

          src = ./.;

          pyproject = true;

          build-system = with pythonPackages; [
            pdm-backend
          ];

          nativeBuildInputs = with pkgs; [
            gobject-introspection
            wrapGAppsHook4
            desktop-file-utils
          ];

          buildInputs = with pkgs; [
            gtk4
            glib
            cairo
            pango
            gdk-pixbuf
            libappindicator-gtk3
            pop-launcher
          ];

          propagatedBuildInputs = with pythonPackages; [
            pygobject3
            pycairo
          ];
          pythonImportsCheck = [ "ulauncher" ];

          strictDeps = false; # broken with gobject-introspection setup hook https://github.com/NixOS/nixpkgs/issues/56943
          dontWrapGApps = true; # prevent double wrapping
          
          preFixup = ''
            makeWrapperArgs+=(--set ULAUNCHER_SYSTEM_PREFIX "$out")
            makeWrapperArgs+=(--prefix PATH : "${pkgs.pop-launcher}/bin")
            makeWrapperArgs+=(--prefix GI_TYPELIB_PATH : "$GI_TYPELIB_PATH")
            # Preserve GTK_PATH and GTK_THEME from environment
            makeWrapperArgs+=(--suffix GTK_PATH : "")
            makeWrapperArgs+=("''${gappsWrapperArgs[@]}")
          '';
          postInstall = ''
            patchShebangs bin/ulauncher-toggle

            # Install application icon (required for proper icon display)
            install -Dm644 data/share/ulauncher/icons/system/apps/ulauncher.svg $out/share/icons/hicolor/scalable/apps/ulauncher.svg
            # Install status icons (required for system tray)
            install -Dm644 data/share/ulauncher/icons/system/status/ulauncher-indicator-symbolic.svg $out/share/icons/hicolor/scalable/status/ulauncher-indicator-symbolic.svg
            install -Dm644 data/share/ulauncher/icons/system/status/ulauncher-indicator-symbolic-dark.svg $out/share/icons/hicolor/scalable/status/ulauncher-indicator-symbolic-dark.svg
          '';

          doCheck = false; # Skip tests for now

          meta = with pkgs.lib; {
            description = "Application launcher for Linux with pop-launcher integration";
            homepage = "https://github.com/Ulauncher/Ulauncher";
            license = licenses.gpl3Plus;
            platforms = platforms.linux;
            maintainers = [ ];
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python
            python.pkgs.pip
            pdm

            # Development tools
            python.pkgs.black
            python.pkgs.ruff
            python.pkgs.mypy
            python.pkgs.pytest
            python.pkgs.pytest-asyncio
            python.pkgs.pytest-mock
            python.pkgs.pygobject-stubs

            # Python dependencies
            python.pkgs.pygobject3
            python.pkgs.pycairo

            # GTK development
            gtk4
            gobject-introspection
            pkg-config

            # pygobject build dependencies
            ninja

            # Runtime dependencies
            pop-launcher
          ];

          shellHook = ''
            echo "Ulauncher-pop development environment"
            echo "Use 'pip install -e .' to install dependencies"
            echo "Use 'python -m ulauncher.main' to run the application"
          '';
        };
      }
    );
}
