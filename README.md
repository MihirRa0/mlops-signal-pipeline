# Signal Generation Batch Job

A small batch job that reads closing prices from a CSV file, computes a
rolling-mean crossover signal, and writes summary metrics to a JSON file.

## Overview

For each row, the job computes a rolling mean of the `close` column over a
configurable window and generates a binary signal:

- `signal = 1` if `close > rolling_mean`
- `signal = 0` otherwise (including rows where the rolling mean isn't
  defined yet, i.e. the first `window - 1` rows)

The job is deterministic (seeded via `numpy.random.seed`), logs its
progress, and always writes a metrics file — whether it succeeds or fails.

## Requirements

- Python 3.9+
- pandas
- numpy
- PyYAML

## Installation

```bash
pip install -r requirements.txt
```

## Local Execution

```bash
python run.py --input data.csv --config config.yaml --output metrics.json --log-file run.log
```

All four arguments are required; there are no hardcoded paths.

## Docker Execution

Build and run the image:

```bash
docker build -t mlops-task .
docker run --rm mlops-task
```

This runs the job against the bundled `config.yaml` and `data.csv`,
writes `metrics.json` and `run.log` inside the container, and prints
the contents of `metrics.json` to stdout. Exit code is `0` on success.

## Expected Output

On success, `metrics.json` looks like:

```json
{
  "version": "v1",
  "rows_processed": 10000,
  "metric": "signal_rate",
  "value": 0.4989,
  "latency_ms": 49,
  "seed": 42,
  "status": "success"
}
```

On failure, `metrics.json` instead looks like:

```json
{
  "version": "v1",
  "status": "error",
  "error_message": "Input CSV is missing required 'close' column"
}
```

