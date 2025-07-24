import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from pathlib import Path
import joblib
import torch

from .base_strategy import BaseStrategy
from ..models.cnn_lstm_model import CNNLSTMModelPyTorch

class CnnLstmStrategyStrategy(BaseStrategy):
    """
    A strategy that uses a trained PyTorch CNN-LSTM model to generate trading signals.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the CNNLSTMStrategy.
        """
        super().__init__(config)
        self.model_path = Path(config.get('modeling', {}).get('model_save_path', 'ml_backtester/models/trained_model_pytorch'))
        self.look_back = config.get('modeling', {}).get('look_back', 60)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        try:
            # The model's n_features will be determined at runtime during training
            # Here, we initialize it with a placeholder and load the state dict.
            n_features = len(joblib.load(self.model_path / 'scaler.gz').mean_)
            self.model = CNNLSTMModelPyTorch(n_features=n_features).to(self.device)
            self.model.load_state_dict(torch.load(self.model_path / 'model.pth'))
            self.scaler = joblib.load(self.model_path / 'scaler.gz')
            self.model.eval() # Set model to evaluation mode
            logging.info("PyTorch CNN-LSTM model and scaler loaded successfully.")
        except Exception as e:
            logging.error(f"Could not load the PyTorch model or scaler. Ensure the model is trained first. Error: {e}")
            self.model = None
            self.scaler = None

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
        
        X = torch.from_numpy(np.array(X)).float().to(self.device)
        
        with torch.no_grad():
            outputs = self.model(X)
            predictions = torch.sigmoid(outputs.squeeze())
            predicted_signals = np.where(predictions.cpu().numpy() > 0.5, 1, -1)
        
        signals = np.zeros(len(data))
        signals[self.look_back:] = predicted_signals
        
        data['signal'] = signals
        return data