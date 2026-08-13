import os
import yaml
import subprocess


def run(cmd: list[str]) -> int:
    print(f"[RUN] {' '.join(cmd)}")
    return subprocess.call(cmd)


def main():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    download_dir = config["data"]["download_dir"]

    # 1) Convert NetCDF → Parquet
    run(["python", os.path.join("scripts", "nc_to_parquet.py")])

    # 2) Insert metadata into PostgreSQL
    run(["python", os.path.join("scripts", "insert_metadata_postgres.py")])

    # 3) Build FAISS index
    run(["python", os.path.join("scripts", "build_faiss_index.py")])

    print("[DONE] Pipeline finished.")


if __name__ == "__main__":
    main()


