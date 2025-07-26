import torch
import torch.nn as nn
import logging

def get_device():
    """
    Automatically detects and returns the best available device for PyTorch.
    """
    if torch.backends.mps.is_available():
        logging.info("Apple Silicon (MPS) GPU detected. Using MPS.")
        return torch.device("mps")
    elif torch.cuda.is_available():
        logging.info("NVIDIA CUDA GPU detected. Using CUDA.")
        return torch.device("cuda")
    else:
        logging.info("No GPU detected. Using CPU.")
        return torch.device("cpu")

class CNNLSTMModelPyTorch(nn.Module):
    """
    A PyTorch implementation of the CNN-LSTM model.
    """
    def __init__(self, n_features: int, hidden_size: int = 50, num_layers: int = 1, dropout: float = 0.2):
        super(CNNLSTMModelPyTorch, self).__init__()
        self.cnn = nn.Sequential(
            nn.Conv1d(in_channels=n_features, out_channels=64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2)
        )
        self.lstm = nn.LSTM(input_size=64, hidden_size=hidden_size, num_layers=num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_size, 1)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # x shape: [batch_size, seq_len, n_features]
        x = x.permute(0, 2, 1) # -> [batch_size, n_features, seq_len]
        x = self.cnn(x)
        
        # Reshape for LSTM
        x = x.permute(0, 2, 1) # -> [batch_size, seq_len/2, 64]
        
        _, (h_n, _) = self.lstm(x)
        
        # Get the last hidden state of the last layer
        x = h_n[-1, :, :]
        x = self.dropout(x)
        x = self.fc(x)
        return x