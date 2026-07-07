"""
Batch job that computes a simple moving-average signal from a CSV of closing prices.

Usage:
    python run.py --input data.csv --config config.yaml --output metrics.json --log-file run.log
"""

import argparse
import json
import logging
import os
import sys
import time
import traceback

import numpy as np
import pandas as pd
import yaml


REQUIRED_CONFIG_KEYS = ("seed", "window", "version")


def setup_logger(log_file: str) -> logging.Logger:
    """Configure a logger that writes to both a file and stdout."""
    logger = logging.getLogger("batch_job")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def load_config(config_path: str) -> dict:
    """Load a YAML config file into a dict."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("Config file is empty or not a valid YAML mapping")

    return config


def validate_config(config: dict) -> None:
    """Check that all required keys are present in the config."""
    missing = [key for key in REQUIRED_CONFIG_KEYS if key not in config]
    if missing:
        raise ValueError(f"Missing required config keys: {missing}")


def load_dataset(input_path: str) -> pd.DataFrame:
    """Load and validate the input CSV file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    if df.empty:
        raise ValueError("Input CSV file is empty")

    df.columns = [c.strip().lower() for c in df.columns]

    if "close" not in df.columns:
        raise ValueError("Input CSV is missing required 'close' column")

    return df


def compute_signals(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """
    Compute the rolling mean of the close price and derive a binary signal.

    The first (window - 1) rows will have NaN for rolling_mean, since there
    aren't enough prior rows yet to average. For those rows the signal is
    set to 0, since close can't meaningfully be compared to a rolling mean
    that doesn't exist.
    """
    df = df.copy()
    df["rolling_mean"] = df["close"].rolling(window).mean()
    df["signal"] = (df["close"] > df["rolling_mean"]).fillna(False).astype(int)
    return df


def write_metrics(output_path: str, metrics: dict) -> None:
    """Write the metrics dict to the output JSON file."""
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)


def build_error_metrics(version: str, message: str) -> dict:
    """Build the metrics dict used on failure."""
    return {
        "version": version,
        "status": "error",
        "error_message": message,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Signal generation batch job")
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--output", required=True, help="Path to output metrics JSON file")
    parser.add_argument("--log-file", required=True, help="Path to log file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = setup_logger(args.log_file)
    logger.info("Job start")

    # Used for error output in case we fail before the config is fully loaded
    version = "unknown"

    try:
        config = load_config(args.config)
        version = config.get("version", "unknown")
        validate_config(config)
        logger.info("Config loaded")

        seed = config["seed"]
        window = config["window"]
        version = config["version"]

        np.random.seed(seed)
        logger.info("Validation passed")

        start_time = time.perf_counter()

        df = load_dataset(args.input)
        logger.info(f"Rows loaded: {len(df)}")

        df = compute_signals(df, window)
        logger.info("Rolling mean computed")
        logger.info("Signals generated")

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        rows_processed = len(df)
        signal_rate = round(float(df["signal"].mean()), 4)

        metrics = {
            "version": version,
            "rows_processed": rows_processed,
            "metric": "signal_rate",
            "value": signal_rate,
            "latency_ms": int(round(elapsed_ms)),
            "seed": seed,
            "status": "success",
        }

        write_metrics(args.output, metrics)
        logger.info("Metrics written")
        logger.info("Job completed")
        return 0

    except Exception as exc:
        logger.error(f"Job failed: {exc}")
        logger.error(traceback.format_exc())

        error_metrics = build_error_metrics(version, str(exc))
        write_metrics(args.output, error_metrics)
        return 1


if __name__ == "__main__":
    sys.exit(main())