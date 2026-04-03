{
  description = "A slangpy render backend for ImGui Bundle";

  inputs =
    {
      nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
      flake-utils.url = "github:numtide/flake-utils";
    };

  outputs = { self, nixpkgs, flake-utils }:
    with flake-utils.lib;
    eachSystem [
      system.x86_64-linux
      system.aarch64-darwin
    ]
      (system:
        let
          inherit (nixpkgs) lib;
          pkgs = import nixpkgs { inherit system; };
        in
        {
          devShells.default = pkgs.mkShell
            {
              buildInputs = with pkgs; [
                # Python environment.
                python3
                uv
              ];
              shellHook = ''
                # Unset XCode SDK to avoid build issues on macOS
                if [[ "$(uname)" == "Darwin" ]]; then
                  export PATH="/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
                  export DEVELOPER_DIR="/Applications/Xcode.app/Contents/Developer"
                  # Let xcrun pick the Xcode SDK; remove Nix’s SDK/toolchain overrides
                  unset SDKROOT CPATH LIBRARY_PATH NIX_CFLAGS_COMPILE NIX_LDFLAGS
                fi
                # Create the virtual environment if it doesn't exist
                if [ -d .venv ]; then
                  # Activate the virtual environment
                  source .venv/bin/activate
                  # Add .venv/bin to PATH
                  export PATH=$PWD/.venv/bin:$PATH
                else
                  echo "Environment not initialized."
                fi
              '';
            };
        }
      );
}
