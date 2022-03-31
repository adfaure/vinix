{
  description = "Python application managed with poetry2nix";

  inputs = {
    nixpkgs = { url = "github:nixos/nixpkgs/nixpkgs-unstable"; };
    flake-utils = { url = "github:numtide/flake-utils"; };
  };

   nixConfig = {
    substituters = [ "https://vinix.cachix.org" ];
    trusted-public-keys = [
      "vinix.cachix.org-1:d0T0FsoxO6us47YfoHU0SKizukCUjEIR30DZhDuIBC8="
    ];
  };


  outputs = { self, nixpkgs, flake-utils, ... }:

    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        # Poetry information
        python = pkgs.python39;
        projectDir = ./.;
        overrides = pkgs.poetry2nix.overrides.withDefaults (final: prev:
          {
            # Python dependency overrides go here
          });

        packageName = "vinix";

        # R package
        plot_tree = pkgs.stdenv.mkDerivation {
          name = "vinix";
          src = pkgs.lib.sourceByRegex ./. [ "vinix" "vinix/print_treemap.R" ];
          buildInputs = [
            (pkgs.rWrapper.override {
              packages = with pkgs.rPackages; [ readr treemap ];
            })
          ];
          installPhase = ''
            mkdir -p $out/bin
            cp vinix/print_treemap.R $out/bin/print_treemap.R
          '';
        };

      in {

        packages = {
          ${packageName} = pkgs.poetry2nix.mkPoetryApplication {
            inherit python projectDir overrides;
            # Non-Python runtime dependencies go here
            propogatedBuildInputs = [ plot_tree pkgs.graphviz ];
            preBuild = ''
              # Replace tree_map
              sed -i 's#print_treemap\.R#${plot_tree}/bin/print_treemap\.R#g' vinix/__main__.py

              # Replace dot
              sed -i 's#dot#${pkgs.graphviz}/bin/dot#g' vinix/__main__.py

              # Replace nix
            '';
          };
          plot_tree = plot_tree;
        };

        defaultPackage = self.packages.${system}.${packageName};

        devShell = pkgs.mkShell {
          buildInputs = [
            plot_tree
            (pkgs.poetry2nix.mkPoetryEnv {
              inherit python projectDir overrides;
            })
            pkgs.python39Packages.poetry
          ];
        };

      });
}
