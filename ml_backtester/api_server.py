import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from flask import Flask, request, jsonify
import numpy as np
import torch
import joblib
import logging

from ml_backtester.models.cnn_lstm_model import CNNLSTMModelPyTorch

app = Flask(__name__)

# --- Configuration ---
MODEL_PATH = Path('ml_backtester/models/trained_model_pytorch')
LOOK_BACK = 60 # This should match the model's training configuration
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- Load Model and Scaler ---
try:
    n_features = len(joblib.load(MODEL_PATH / 'scaler.gz').mean_)
    model = CNNLSTMModelPyTorch(n_features=n_features).to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH / 'model.pth'))
    scaler = joblib.load(MODEL_PATH / 'scaler.gz')
    model.eval()
    logging.info("API Server: Model and scaler loaded successfully.")
except Exception as e:
    model = None
    scaler = None
    logging.error(f"API Server: Could not load model or scaler. Error: {e}")

@app.route('/predict', methods=['POST'])
def predict():
    if not model or not scaler:
        return jsonify({"error": "Model not loaded"}), 500

    json_data = request.get_json()
    if 'features' not in json_data:
        return jsonify({"error": "Missing 'features' in request"}), 400

    # Expecting a list of lists/dicts representing the look_back window
    feature_data = json_data['features']
    if len(feature_data) != LOOK_BACK:
        return jsonify({"error": f"Expected {LOOK_BACK} timesteps, but got {len(feature_data)}"}), 400

    try:
        # Convert to numpy array and scale
        features_np = np.array(feature_data)
        scaled_features = scaler.transform(features_np)

        # Convert to tensor
        X = torch.from_numpy(scaled_features).float().unsqueeze(0).to(DEVICE) # Add batch dimension

        # Get prediction
        with torch.no_grad():
            output = model(X)
            prediction = torch.sigmoid(output.squeeze())
            signal = 1 if prediction.item() > 0.5 else -1

        return jsonify({"signal": signal})

    except Exception as e:
        logging.error(f"Prediction error: {e}")
        return jsonify({"error": "Failed to make a prediction."}), 500

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=5001, debug=False)