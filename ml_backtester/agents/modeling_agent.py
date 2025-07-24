import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
import logging
from pathlib import Path
import joblib
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

from ..models.cnn_lstm_model import CNNLSTMModelPyTorch

class ModelingAgent:
    """
    Agent for training, evaluating, and managing the PyTorch model.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the ModelingAgent.
        """
        self.config = config.get('modeling', {})
        self.model_path = Path(self.config.get('model_save_path', 'ml_backtester/models/trained_model_pytorch'))
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        self.look_back = self.config.get('look_back', 60)
        self.epochs = self.config.get('epochs', 50)
        self.batch_size = self.config.get('batch_size', 32)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logging.info(f"Using device: {self.device}")

    def _prepare_data(self, data: pd.DataFrame) -> Tuple[DataLoader, DataLoader]:
        """
        Prepares the data for the PyTorch CNN-LSTM model.
        """
        logging.info("Preparing data for the PyTorch model...")
        
        features = [col for col in data.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
        scaler = StandardScaler()
        data[features] = scaler.fit_transform(data[features])
        
        joblib.dump(scaler, self.model_path / 'scaler.gz')

        X, y = [], []
        for i in range(len(data) - self.look_back):
            X.append(data.iloc[i:(i + self.look_back)][features].values)
            y.append(data.iloc[i + self.look_back]['close'] > data.iloc[i + self.look_back - 1]['close'])
        
        X, y = np.array(X), np.array(y).astype(np.float32)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

        train_dataset = TensorDataset(torch.from_numpy(X_train).float(), torch.from_numpy(y_train).float())
        test_dataset = TensorDataset(torch.from_numpy(X_test).float(), torch.from_numpy(y_test).float())

        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=self.batch_size, shuffle=False)

        return train_loader, test_loader, X_train.shape[2]

    def execute(self, data: pd.DataFrame):
        """
        Trains the PyTorch model and saves it.
        """
        train_loader, test_loader, n_features = self._prepare_data(data)
        
        model = CNNLSTMModelPyTorch(n_features=n_features).to(self.device)
        criterion = nn.BCEWithLogitsLoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001)

        logging.info("Starting PyTorch model training...")
        for epoch in range(self.epochs):
            model.train()
            for X_batch, y_batch in train_loader:
                X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)
                
                optimizer.zero_grad()
                outputs = model(X_batch)
                loss = criterion(outputs.squeeze(), y_batch)
                loss.backward()
                optimizer.step()
            
            # Validation
            model.eval()
            val_loss, correct, total = 0, 0, 0
            with torch.no_grad():
                for X_batch, y_batch in test_loader:
                    X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)
                    outputs = model(X_batch)
                    val_loss += criterion(outputs.squeeze(), y_batch).item()
                    predicted = torch.round(torch.sigmoid(outputs.squeeze()))
                    total += y_batch.size(0)
                    correct += (predicted == y_batch).sum().item()
            
            accuracy = 100 * correct / total
            logging.info(f'Epoch {epoch+1}/{self.epochs}, Loss: {val_loss/len(test_loader):.4f}, Accuracy: {accuracy:.2f}%')

        torch.save(model.state_dict(), self.model_path / 'model.pth')
        logging.info(f"PyTorch model saved to '{self.model_path}'.")