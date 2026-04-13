{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    # Python with all needed packages
    (python3.withPackages (ps: with ps; [
      # avantgraph import
      click

      # clients
      duckdb
      neo4j
      kuzu
      psycopg2
      mysql-connector

      # visualization
      matplotlib
      pandas
      seaborn
      natsort
    ]))

    # build tools / dependencies
    cmake
    gcc
    openssl
    unixODBC
    wget
    unzip
    zstd

    # containers
    docker

    # convenience
    tmux
    vim
    htop
    nmon
    curl
    postgresql
    silver-searcher
  ];
}
