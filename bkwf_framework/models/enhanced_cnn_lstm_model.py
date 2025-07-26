import torch
import torch.nn as nn
import torch.nn.functional as F
import logging

from .cnn_lstm_model import get_device

class Attention(nn.Module):
    """
    A custom Attention module for the LSTM layer.
    """
    def __init__(self, hidden_size: int):
        super(Attention, self).__init__()
        self.hidden_size = hidden_size
        self.attention_weights = nn.Linear(hidden_size, 1)

    def forward(self, lstm_outputs: torch.Tensor) -> torch.Tensor:
        # lstm_outputs shape: [batch_size, seq_len, hidden_size]
        
        # Calculate attention scores
        # scores shape: [batch_size, seq_len, 1]
        scores = self.attention_weights(lstm_outputs)
        
        # Apply softmax to get attention weights
        # weights shape: [batch_size, seq_len, 1]
        weights = F.softmax(scores, dim=1)
        
        # Calculate context vector
        # context shape: [batch_size, hidden_size]
        context = torch.sum(weights * lstm_outputs, dim=1)
        
        return context

class EnhancedCNNLSTMModel(nn.Module):
    """
    An enhanced CNN-BiLSTM model with an Attention mechanism.
    """
    def __init__(self, n_features: int, hidden_size: int = 50, num_layers: int = 1):
        super(EnhancedCNNLSTMModel, self).__init__()
        self.cnn = nn.Sequential(
            nn.Conv1d(in_channels=n_features, out_channels=64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2)
        )
        self.lstm = nn.LSTM(input_size=64, hidden_size=hidden_size, 
                            num_layers=num_layers, batch_first=True, bidirectional=True)
        self.attention = Attention(hidden_size * 2)  # *2 for bidirectional
        self.fc = nn.Linear(hidden_size * 2, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: [batch_size, seq_len, n_features]
        x = x.permute(0, 2, 1)  # -> [batch_size, n_features, seq_len]
        x = self.cnn(x)
        
        # Reshape for LSTM
        x = x.permute(0, 2, 1)  # -> [batch_size, seq_len/2, 64]
        
        # LSTM layer
        lstm_out, _ = self.lstm(x)
        
        # Attention layer
        context_vector = self.attention(lstm_out)
        
        # Fully connected layer
        x = self.fc(context_vector)
        return x