import torch
import torch.nn as nn
import lightgbm as lgb
import numpy as np
from pathlib import Path
import joblib

from .cnn_lstm_model import CNNLSTMModelPyTorch, get_device
from .enhanced_cnn_lstm_model import EnhancedCNNLSTMModel

class CNNLightGBMModel:
    """
    A hybrid model that uses a CNN-LSTM for feature extraction and LightGBM for prediction.
    """
    def __init__(self, n_features: int, model_path: str, use_enhanced_model: bool = False):
        self.device = get_device()
        self.use_enhanced_model = use_enhanced_model
        if use_enhanced_model:
            self.cnn_lstm_model = EnhancedCNNLSTMModel(n_features=n_features).to(self.device)
        else:
            self.cnn_lstm_model = CNNLSTMModelPyTorch(n_features=n_features).to(self.device)
        self.lgb_model = None
        self.model_path = Path(model_path)

    def extract_features(self, data_loader: torch.utils.data.DataLoader) -> tuple[np.ndarray, np.ndarray]:
        """
        Extracts features from the CNN-LSTM model.
        """
        self.cnn_lstm_model.eval()
        features = []
        labels = []
        with torch.no_grad():
            for X_batch, y_batch in data_loader:
                X_batch = X_batch.to(self.device)
                
                # Get the feature representation from the model
                if self.use_enhanced_model:
                    # The enhanced model returns the context vector from the attention layer
                    context_vector = self.cnn_lstm_model(X_batch)
                    features.append(context_vector.cpu().numpy())
                else:
                    # Original model returns the last hidden state
                    x = X_batch.permute(0, 2, 1)
                    x = self.cnn_lstm_model.cnn(x)
                    x = x.permute(0, 2, 1)
                    _, (h_n, _) = self.cnn_lstm_model.lstm(x)
                    features.append(h_n.squeeze(0).cpu().numpy())
                labels.append(y_batch.cpu().numpy())
        
        return np.concatenate(features), np.concatenate(labels)

    def train(self, train_loader: torch.utils.data.DataLoader, val_loader: torch.utils.data.DataLoader, lgb_params: dict):
        """
        Trains the LightGBM model on features extracted from the CNN-LSTM.
        """
        # First, ensure the CNN-LSTM is loaded if it exists
        cnn_lstm_path = self.model_path / 'model.pth'
        if cnn_lstm_path.exists():
            self.cnn_lstm_model.load_state_dict(torch.load(cnn_lstm_path, map_location=self.device))
            print("Loaded pre-trained CNN-LSTM model.")

        print("Extracting features for LightGBM training...")
        X_train_features, y_train = self.extract_features(train_loader)
        X_val_features, y_val = self.extract_features(val_loader)

        print("Training LightGBM model...")
        self.lgb_model = lgb.LGBMClassifier(**lgb_params)
        self.lgb_model.fit(X_train_features, y_train,
                           eval_set=[(X_val_features, y_val)],
                           eval_metric='logloss',
                           callbacks=[lgb.early_stopping(10, verbose=True)])
        
        self.save_model()

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Makes predictions using the hybrid model.
        """
        self.cnn_lstm_model.eval()
        
        # Prepare data for feature extraction
        X_tensor = torch.from_numpy(X).float().to(self.device)
        dataset = torch.utils.data.TensorDataset(X_tensor, torch.zeros(X_tensor.size(0))) # Dummy labels
        data_loader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=False)

        features = []
        with torch.no_grad():
            for X_batch, _ in data_loader:
                X_batch = X_batch.to(self.device)
                if self.use_enhanced_model:
                    context_vector = self.cnn_lstm_model(X_batch)
                    features.append(context_vector.cpu().numpy())
                else:
                    x = X_batch.permute(0, 2, 1)
                    x = self.cnn_lstm_model.cnn(x)
                    x = x.permute(0, 2, 1)
                    _, (h_n, _) = self.cnn_lstm_model.lstm(x)
                    features.append(h_n.squeeze(0).cpu().numpy())
        
        extracted_features = np.concatenate(features)
        return self.lgb_model.predict(extracted_features)

    def save_model(self):
        """
        Saves the LightGBM model.
        """
        joblib.dump(self.lgb_model, self.model_path / 'lgbm_model.joblib')
        print(f"LightGBM model saved to '{self.model_path}'.")

    def load_model(self):
        """
        Loads the LightGBM model.
        """
        self.lgb_model = joblib.load(self.model_path / 'lgbm_model.joblib')
        print(f"LightGBM model loaded from '{self.model_path}'.")
