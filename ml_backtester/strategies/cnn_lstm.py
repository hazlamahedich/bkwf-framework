import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from pathlib import Path
import joblib
import torch

from .base_strategy import BaseStrategy
from ..models.cnn_lstm_model import CNNLSTMModelPyTorch
from ..models.cnn_lightgbm_model import CNNLightGBMModel
from ..models.enhanced_cnn_lstm_model import EnhancedCNNLSTMModel

class CnnLstmStrategy(BaseStrategy):
    """
    A strategy that uses a trained PyTorch CNN-LSTM model to generate trading signals.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the CNNLSTMStrategy.
        """
        super().__init__(config)
        self.model_config = config.get('modeling', {})
        self.model_path = Path(self.model_config.get('model_save_path', 'ml_backtester/models/trained_model_pytorch'))
        self.look_back = self.model_config.get('look_back', 60)
        self.model_type = self.model_config.get('model_type', 'cnn_lstm')
        self.use_enhanced_model = self.model_config.get('use_enhanced_model', False)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.model = None
        self.scaler = None
        self._load_model_and_scaler()

    def _load_model_and_scaler(self):
        """Loads the appropriate model and scaler based on the config."""
        try:
            self.scaler = joblib.load(self.model_path / 'scaler.gz')
            n_features = len(self.scaler.mean_)

            if self.model_type == 'cnn_lightgbm':
                self.model = CNNLightGBMModel(
                    n_features=n_features,
                    model_path=self.model_path,
                    use_enhanced_model=self.use_enhanced_model
                )
                self.model.load_model() # Loads lgbm_model.joblib
                # Also load the CNN-LSTM part for feature extraction
                cnn_lstm_path = self.model_path / 'model.pth'
                if cnn_lstm_path.exists():
                    self.model.cnn_lstm_model.load_state_dict(torch.load(cnn_lstm_path, map_location=self.device))
                    logging.info("Hybrid CNN-LightGBM model loaded successfully.")
                else:
                    raise FileNotFoundError("CNN-LSTM model file not found for feature extraction.")
            else: # Default to cnn_lstm or enhanced_cnn_lstm
                if self.use_enhanced_model:
                    # Pass hyperparameters to the model constructor
                    self.model = EnhancedCNNLSTMModel(
                        n_features=n_features,
                        hidden_size=self.model_config.get('hidden_size', 50),
                        num_layers=self.model_config.get('num_layers', 2),
                        dropout=self.model_config.get('dropout', 0.2)
                    ).to(self.device)
                    logging.info("PyTorch Enhanced CNN-LSTM model loaded successfully.")
                else:
                    # Pass hyperparameters to the model constructor
                    self.model = CNNLSTMModelPyTorch(
                        n_features=n_features,
                        hidden_size=self.model_config.get('hidden_size', 50),
                        num_layers=self.model_config.get('num_layers', 2),
                        dropout=self.model_config.get('dropout', 0.2)
                    ).to(self.device)
                    logging.info("PyTorch CNN-LSTM model loaded successfully.")
                
                self.model.load_state_dict(torch.load(self.model_path / 'model.pth'))
                self.model.eval()

        except Exception as e:
            logging.error(f"Could not load the model or scaler for model_type '{self.model_type}'. Error: {e}")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generates signals using the trained PyTorch CNN-LSTM model.
        """
        if self.model is None or self.scaler is None:
            data['signal'] = 0
            return data

        logging.info("Generating signals with PyTorch CNN-LSTM model...")
        
        features = [col for col in data.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
        data_scaled = self.scaler.transform(data[features])
        
        X = []
        for i in range(len(data) - self.look_back):
            X.append(data_scaled[i:(i + self.look_back)])
        
        X = np.array(X)
        
        if self.model_type == 'cnn_lightgbm':
            predictions = self.model.predict(X)
            # The output of LGBM is already 0 or 1, convert to -1 or 1
            predictions_binary = np.where(predictions > 0.5, 1, -1)
        else:
            X_tensor = torch.from_numpy(X).float().to(self.device)
            with torch.no_grad():
                outputs = self.model(X_tensor)
                predictions = torch.sigmoid(outputs.squeeze())
                predictions_binary = np.where(predictions.cpu().numpy() > 0.5, 1, -1)

        # Pad the predictions to align with the original dataframe
        full_length_preds = np.zeros(len(data))
        full_length_preds[self.look_back:] = predictions_binary

        # Generate signals only on a change of state
        signals = np.zeros(len(data))
        for i in range(1, len(full_length_preds)):
            if full_length_preds[i] == 1 and full_length_preds[i-1] == -1:
                signals[i] = 1  # Buy signal
            elif full_length_preds[i] == -1 and full_length_preds[i-1] == 1:
                signals[i] = -1 # Sell signal
        
        data['signal'] = signals
        return data