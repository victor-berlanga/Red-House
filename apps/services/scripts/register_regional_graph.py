"""Register a reviewed graph file through the owner API. No database access."""

import argparse
import json
import os

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument(
        "--key", required=True, help="Stable idempotency key for this version"
    )
    args = parser.parse_args()
    token = os.environ["REDHOUSE_ACCESS_TOKEN"]
    with open(args.file) as source:
        data = json.load(source)
    response = requests.post(
        args.url.rstrip("/") + "/api/v1/regional-graphs",
        json=data,
        headers={"Authorization": "Bearer " + token, "Idempotency-Key": args.key},
        timeout=(3, 30),
    )
    response.raise_for_status()
    print(
        json.dumps(
            {
                "id": response.json()["data"]["id"],
                "version": response.json()["data"]["version"],
            }
        )
    )


if __name__ == "__main__":
    main()
