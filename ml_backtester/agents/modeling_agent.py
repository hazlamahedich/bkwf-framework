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
from ..models.cnn_lightgbm_model import CNNLightGBMModel

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
        
        self.model_type = self.config.get('model_type', 'cnn_lstm') # 'cnn_lstm' or 'cnn_lightgbm'
        self.look_back = self.config.get('look_back', 60)
        self.epochs = self.config.get('epochs', 50)
        self.batch_size = self.config.get('batch_size', 32)
        self.early_stopping_patience = self.config.get('early_stopping_patience', 10)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logging.info(f"Using device: {self.device}")

    def _prepare_data(self, data: pd.DataFrame) -> Tuple[DataLoader, DataLoader]:
        """
        Prepares the data for the PyTorch CNN-LSTM model.
        """
        logging.info("Preparing data for the PyTorch model...")
        
        features = [col for col in data.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
        
        # --- Start of Robust Data Cleaning ---
        
        # 1. Handle non-finite values (inf) by replacing them with NaN
        data.replace([np.inf, -np.inf], np.nan, inplace=True)
        logging.info("Replaced Inf values with NaN.")

        # 2. Drop columns that are entirely NaN
        all_nan_cols = data.columns[data.isna().all()].tolist()
        if all_nan_cols:
            logging.warning(f"Dropping columns that are entirely NaN: {all_nan_cols}")
            data.dropna(axis=1, how='all', inplace=True)
            # Update features list to reflect any dropped columns
            features = [f for f in features if f in data.columns]
        
        # 3. Fill any remaining NaNs
        data.ffill(inplace=True)
        data.bfill(inplace=True)
        logging.info("Filled remaining NaNs using ffill and bfill.")

        # 4. Identify and handle columns with zero variance
        std_dev = data[features].std()
        zero_std_cols = std_dev[std_dev == 0].index.tolist()
        if zero_std_cols:
            logging.warning(f"Columns with zero standard deviation: {zero_std_cols}")
            # Remove zero-std columns from the list of features
            features = [col for col in features if col not in zero_std_cols]
            logging.info(f"Final features for model: {features}")

        # 5. Scale the data
        if not features:
            raise ValueError("No features left to scale after cleaning. Check feature engineering.")
            
        scaler = StandardScaler()
        data[features] = scaler.fit_transform(data[features])
        logging.info("Data scaling complete.")
        
        # --- End of Robust Data Cleaning ---
        
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

    def execute(self, data: pd.DataFrame, hyperparameters: Dict[str, Any] = None):
        """
        Trains the selected model and saves it.

        Args:
            data (pd.DataFrame): The training data.
            hyperparameters (Dict[str, Any], optional): Hyperparameters for this run.
                                                       If None, uses config defaults.
        """
        # If no dynamic hyperparameters are passed, use the defaults from the main config
        if hyperparameters is None:
            hyperparameters = {
                'learning_rate': self.config.get('learning_rate', 0.001),
                'hidden_size': self.config.get('hidden_size', 64),
                'num_layers': self.config.get('num_layers', 2),
                'dropout': self.config.get('dropout', 0.2)
            }

        train_loader, test_loader, n_features = self._prepare_data(data)

        if self.model_type == 'cnn_lstm':
            self._train_cnn_lstm(train_loader, test_loader, n_features, hyperparameters)
        elif self.model_type == 'cnn_lightgbm':
            self._train_cnn_lightgbm(train_loader, test_loader, n_features, hyperparameters)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def _train_cnn_lstm(self, train_loader, test_loader, n_features, hyperparameters: Dict[str, Any]):
        """
        Trains the standalone CNN-LSTM model.

        Args:
            train_loader: DataLoader for training data.
            test_loader: DataLoader for validation data.
            n_features (int): Number of input features.
            hyperparameters (Dict[str, Any]): Dictionary of hyperparameters for the model.
        """
        model = CNNLSTMModelPyTorch(
            n_features=n_features,
            hidden_size=hyperparameters.get('hidden_size', 64),
            num_layers=hyperparameters.get('num_layers', 2),
            dropout=hyperparameters.get('dropout', 0.2)
        ).to(self.device)
        
        criterion = nn.BCEWithLogitsLoss()
        optimizer = optim.Adam(model.parameters(), lr=hyperparameters.get('learning_rate', 0.001))

        logging.info(f"Starting PyTorch model training with params: {hyperparameters}")
        
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(self.epochs):
            model.train()
            for X_batch, y_batch in train_loader:
                X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)
                
                optimizer.zero_grad()
                outputs = model(X_batch)
                loss = criterion(outputs.squeeze(), y_batch)
                loss.backward()
                optimizer.step()
            
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
            
            avg_val_loss = val_loss / len(test_loader)
            accuracy = 100 * correct / total
            logging.info(f'Epoch {epoch+1}/{self.epochs}, Loss: {avg_val_loss:.4f}, Accuracy: {accuracy:.2f}%')

            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                torch.save(model.state_dict(), self.model_path / 'model.pth')
                logging.info(f"Validation loss improved. Model saved to '{self.model_path}'.")
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= self.early_stopping_patience:
                    logging.info(f"Early stopping triggered after {epoch + 1} epochs.")
                    break

        # Load the best model state before finishing
        model.load_state_dict(torch.load(self.model_path / 'model.pth'))
        logging.info(f"Finished training. Best model loaded from '{self.model_path}'.")

    def _train_cnn_lightgbm(self, train_loader, test_loader, n_features, hyperparameters: Dict[str, Any]):
        """
        Trains the hybrid CNN-LightGBM model.
        """
        logging.info("Starting Hybrid CNN-LightGBM model training...")
        
        # First, train the CNN-LSTM part to get good feature representations
        self._train_cnn_lstm(train_loader, test_loader, n_features, hyperparameters)

        # Now, train the LightGBM part on the extracted features
        model = CNNLightGBMModel(n_features=n_features, model_path=self.model_path)
        
        lgb_params = self.config.get('lgbm_params', {})
        model.train(train_loader, test_loader, lgb_params)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Makes predictions using the loaded model.
        """
        if self.model_type == 'cnn_lstm':
            # This would require loading the model and running prediction
            # For simplicity, we focus on the hybrid model's prediction path
            raise NotImplementedError("Prediction for standalone cnn_lstm is not implemented in this agent.")
        
        elif self.model_type == 'cnn_lightgbm':
            n_features = X.shape[2]
            model = CNNLightGBMModel(n_features=n_features, model_path=self.model_path)
            model.load_model() # Loads the lgbm_model.joblib
            
            # We also need to load the CNN-LSTM part for feature extraction
            cnn_lstm_path = self.model_path / 'model.pth'
            if cnn_lstm_path.exists():
                model.cnn_lstm_model.load_state_dict(torch.load(cnn_lstm_path, map_location=self.device))
            else:
                raise FileNotFoundError("CNN-LSTM model file not found for feature extraction.")

            return model.predict(X)