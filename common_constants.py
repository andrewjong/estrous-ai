EXPERIMENTS_ROOT = "experiments"
META_FNAME = "meta.json"
MODEL_PARAMS_FNAME = "model.pth"
TRAIN_RESULTS_FNAME = "train.csv"
PREDICT_RESULTS_FNAME = "predictions.csv"

PHASE_ORDER = {'p': 1, 'e': 2, 'm': 3, 'd': 4}  # ordering of estrous cycle

MODEL_TO_IMAGE_SIZE = {
    "inception": 299,
    "nasnetalarge": 331
}
DEFAULT_IMAGE_SIZE = 224
