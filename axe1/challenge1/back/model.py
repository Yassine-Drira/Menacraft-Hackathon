import torch
import torch.nn as nn
from torchvision import models

class ThumbnailDeepfakeDetector(nn.Module):
    def __init__(self, pretrained=False, dropout=0.4):
        super().__init__()
        # Use EfficientNet-B0 as the backbone as per your notebook
        bb = models.efficientnet_b0(weights=None)
        self.features = bb.features
        self.avgpool = bb.avgpool
        in_feats = bb.classifier[1].in_features
        
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(in_feats, 256),
            nn.GELU(),
            nn.Dropout(dropout / 2),
            nn.Linear(256, 1),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        return self.classifier(x)