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
    def __init__(self, n_features: int):
        super(CNNLSTMModelPyTorch, self).__init__()
        self.cnn = nn.Sequential(
            nn.Conv1d(in_channels=n_features, out_channels=64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2)
        )
        self.lstm = nn.LSTM(input_size=64, hidden_size=50, batch_first=True)
        self.fc = nn.Linear(50, 1)

    def forward(self, x):
        # x shape: [batch_size, seq_len, n_features]
        x = x.permute(0, 2, 1) # -> [batch_size, n_features, seq_len]
        x = self.cnn(x)
        
        # Reshape for LSTM
        x = x.permute(0, 2, 1) # -> [batch_size, seq_len/2, 64]
        
        _, (h_n, _) = self.lstm(x)
        
        # Get the last hidden state
        x = h_n.squeeze(0)
        x = self.fc(x)
        return x