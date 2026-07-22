"""Locked SRRES-VP-1.0.0 constants for Act 5. No protocol values are tunable at runtime."""

from __future__ import annotations

PROTOCOL_ID = "SRRES-VP-1.0.0"
SELECTION_TOLERANCE = 0.002000

DATASET_PRIMARY = {
    "relative_path": "data/raw/masses_exclusions.csv",
    "sha256": "c8c8063c84a10143b6369f444a037ef5695ff13f5eef6f9bf00dc86880c3937a",
    "bytes": 360552,
    "rows": 12280,
    "columns": ["mchi1", "mchipm1", "Final_CLs", "exclusion"],
    "features_raw": ["mchi1", "mchipm1"],
    "feature_names": ["x1", "x2"],
}

DATASET_SECONDARY = {
    "relative_path": "data/raw/masses_exclusions2.csv",
    "sha256": "7c725fb1ada5d19fa4177274660eebc5141e5535275ed78b58a974fe2a023b68",
    "bytes": 494290,
    "rows": 12280,
    "columns": ["mhiggs", "mchi1", "mchipm1", "Final_CLs", "exclusion"],
    "features_raw": ["mchi1", "mchipm1", "mhiggs"],
    "feature_names": ["x1", "x2", "x3"],
}

CLASS_COUNTS = {"0": 2263, "1": 10017}
SCALE = 1000.0
POSITIVE_CLASS = 1
TARGET = "exclusion"
PROHIBITED_FEATURE = "Final_CLs"

OUTER_SEEDS = [
    1052946466,
    2954944466,
    253326485,
    3092109938,
    2214114891,
    360250991,
    79207584,
    3435737801,
    3826220486,
    1585298731,
]

BUNDLE_MASTERS = [
    [2596228945, 1539645898, 4178097650],
    [2121174993, 1880000882, 4094919132],
    [2144778368, 656599826, 2108423874],
    [1187826276, 3618860218, 350984310],
    [1463233600, 1239700443, 726122521],
    [3574990427, 4084193958, 3810626280],
    [3984356223, 3293072627, 1310764055],
    [644294708, 3747685511, 1254902362],
    [2222464828, 1247498419, 180046264],
    [829889456, 335872028, 2696894631],
]

BOOTSTRAP_PRIMARY_SEED = 3710008170
BOOTSTRAP_DELTA_SEED = 381478060
BOOTSTRAP_REPLICATES = 100_000

CANDIDATE_CONFIGS = [
    {"id": "C01", "maxsize": 20, "parsimony": 0.0001},
    {"id": "C02", "maxsize": 30, "parsimony": 0.0001},
    {"id": "C03", "maxsize": 40, "parsimony": 0.0001},
    {"id": "C04", "maxsize": 20, "parsimony": 0.0010},
    {"id": "C05", "maxsize": 30, "parsimony": 0.0010},
    {"id": "C06", "maxsize": 40, "parsimony": 0.0010},
]

STAGE_A = {
    "niterations": 30,
    "populations": 12,
    "population_size": 27,
    "ncycles_per_iteration": 200,
    "timeout_seconds": 60 * 60,
}

STAGE_B = {
    "niterations": 200,
    "populations": 20,
    "population_size": 27,
    "ncycles_per_iteration": 380,
    "timeout_seconds": 6 * 60 * 60,
}

BINARY_OPERATORS = ["+", "-", "*", "/"]
UNARY_OPERATORS = ["square", "abs", "log1p"]
ELEMENTWISE_LOSS = "loss(prediction, target, weight) = weight * (prediction - target)^2"

FIXED_PYSR = {
    "parallelism": "serial",
    "precision": 64,
    "deterministic": True,
    "warm_start": False,
    "batching": False,
    "early_stopping": False,
    "model_selection": "accuracy",
    "temp_equation_file": True,
    "delete_tempfiles": False,
    "verbosity": 0,
    "progress": False,
}

LOCKED_VERSIONS = {
    "Python": "3.12.13",
    "pysr": "1.5.10",
    "Julia": "1.10.3",
    "SymbolicRegression": "1.11.3",
    "juliacall": "0.9.26",
    "juliapkg": "0.1.24",
    "numpy": "2.5.1",
    "pandas": "3.0.3",
    "scikit-learn": "1.9.0",
    "scipy": "1.18.0",
    "sympy": "1.14.0",
    "PyYAML": "6.0.3",
    "matplotlib": "3.11.0",
}

ACT4_ARCHIVE_SHA256 = "f5c8cccaff25f7c5fb1ff08b83f34666120345edc72e3c1f341315ed9dbd9fbb"
REPO_COMMIT = "2539dfebb07d587a66aa61ec5381aa1f332b822e"
SPLIT_MANIFEST_SHA256 = "399dfe0e1747f58417d9015d1f1b82b740c889262b49f9ba13b75b73d9aff5e0"
REQUIREMENTS_LOCK_SHA256 = "ccf433d1c55bf2d583d6a8888fb37ae62e563a07990256b4c2b329c9084014f2"
JULIA_PROJECT_SHA256 = "a6220dc01248971f8f524c49f6a659d78a5859a0fe8aae04a4f6e8a90f070ef9"
JULIA_MANIFEST_SHA256 = "0e1ee9d8b36189383709e94df62846a8c2032be51592f9b8b2cff105a6613876"

ARMS = ("PRIMARY", "SECONDARY")
OUTER_IDS = [f"OS-{i:02d}" for i in range(1, 11)]
BUNDLE_IDS = ("B01", "B02", "B03")
CONFIG_IDS = [c["id"] for c in CANDIDATE_CONFIGS]

# Safe concurrency on Apple M2 / 8 logical CPUs / 8 GiB RAM.
# Each search is single-threaded; leave headroom for OS + scheduler.
DEFAULT_MAX_CONCURRENT_SEARCHES = 2
