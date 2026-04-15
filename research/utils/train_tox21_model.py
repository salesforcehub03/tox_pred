import os
import sys

# Suppress warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import logging
logging.getLogger("deepchem").setLevel(logging.ERROR)

import deepchem as dc
from deepchem.models import MultitaskClassifier
import numpy as np

def main():
    print("==================================================")
    print("[*] DeepChem Tox21 Offline Model Trainer")
    print("==================================================")
    print("[1] Building Datasets (Will download if not cached)...")
    
    # Use the 'ECFP' string to tell DeepChem to download the pre-featurized dataset
    # This completely bypasses the local RDKit string-parsing crash on the 8,000 molecules!
    tasks, datasets, transformers = dc.molnet.load_tox21(featurizer='ECFP', split='random')
    train_dataset, valid_dataset, test_dataset = datasets

    print(f"[*] Tasks loaded: {len(tasks)} target endpoints.")
    print(f"[*] Training compounds: {len(train_dataset)}")
    
    # Save directory
    model_dir = os.path.join(os.path.dirname(__file__), "models", "tox21_multitask")
    os.makedirs(model_dir, exist_ok=True)
    
    print(f"[2] Initializing MultitaskClassifier Neural Network...")
    print(f"[*] Output directory: {model_dir}")
    
    # Create the model. 
    # n_tasks = 12, n_features = 1024, layer_sizes = [1000]
    model = MultitaskClassifier(
        n_tasks=len(tasks),
        n_features=1024,
        layer_sizes=[1000],
        dropouts=[0.25],
        learning_rate=0.001,
        model_dir=model_dir
    )
    
    print("[3] Training Model (This will take a minute on a CPU)...")
    model.fit(train_dataset, nb_epoch=10)
    
    print("[4] Evaluating against Validation Set...")
    metric = dc.metrics.Metric(dc.metrics.roc_auc_score, np.mean)
    train_score = model.evaluate(train_dataset, [metric], transformers)
    valid_score = model.evaluate(valid_dataset, [metric], transformers)
    
    print(f"[*] Train ROC-AUC: {train_score['mean-roc_auc_score']:.3f}")
    print(f"[*] Valid ROC-AUC: {valid_score['mean-roc_auc_score']:.3f}")
    
    print("==================================================")
    print("[*] Training Complete! The model weights are saved.")
    print("[*] Your toxicity_predictor.py will now use TRUE predictions!")
    print("==================================================")

if __name__ == "__main__":
    main()
