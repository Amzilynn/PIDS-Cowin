"""
src/models/pose_model.py
─────────────────────────
Bidirectional LSTM with self-attention for pose-sequence classification.

Input : (B, T, input_size)   — T frames, input_size = 33*4 = 132
Output: logits (B, num_classes)  or embedding (B, embed_dim)

Architecture
────────────
    BiLSTM  →  Temporal Self-Attention  →  Pooling  →  MLP head
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


# ── Temporal Self-Attention ───────────────────────────────────────────────────

class TemporalAttention(nn.Module):
    """Additive (Bahdanau) attention over the time axis."""

    def __init__(self, hidden_size: int) -> None:
        super().__init__()
        self.query = nn.Linear(hidden_size, hidden_size, bias=False)
        self.key   = nn.Linear(hidden_size, hidden_size, bias=False)
        self.value = nn.Linear(hidden_size, hidden_size, bias=False)
        self.scale = math.sqrt(hidden_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x : (B, T, H)
        returns: (B, H) weighted pooled representation
        """
        q = self.query(x)                            # (B, T, H)
        k = self.key(x)
        v = self.value(x)
        scores = torch.bmm(q, k.transpose(1, 2)) / self.scale  # (B, T, T)
        attn   = F.softmax(scores, dim=-1)
        out    = torch.bmm(attn, v)                  # (B, T, H)
        return out.mean(dim=1)                        # (B, H)


# ── Pose Model ────────────────────────────────────────────────────────────────

class PoseModel(nn.Module):

    def __init__(
        self,
        input_size: int = 132,
        hidden_size: int = 256,
        num_layers: int = 2,
        num_classes: int = 7,
        embed_dim: int = 256,
        dropout: float = 0.3,
        bidirectional: bool = True,
        mode: str = "classifier",   # 'classifier' | 'encoder'
    ) -> None:
        super().__init__()
        self.mode = mode
        self.embed_dim = embed_dim
        self.hidden_size = hidden_size
        self.bidirectional = bidirectional
        self.num_directions = 2 if bidirectional else 1
        lstm_out = hidden_size * self.num_directions

        # ── Input projection (normalises landmark scale) ───────────────────────
        self.input_proj = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
        )

        # ── Bi-LSTM ───────────────────────────────────────────────────────────
        self.lstm = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=bidirectional,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # ── Temporal attention ────────────────────────────────────────────────
        self.attn = TemporalAttention(lstm_out)

        # ── Projection to embed_dim ───────────────────────────────────────────
        self.projector = nn.Sequential(
            nn.Linear(lstm_out, embed_dim),
            nn.LayerNorm(embed_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )

        # ── Head ──────────────────────────────────────────────────────────────
        self.classifier = nn.Linear(embed_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x : (B, T, input_size)"""
        x = self.input_proj(x)              # (B, T, H)
        out, _ = self.lstm(x)               # (B, T, H*dirs)
        pooled = self.attn(out)             # (B, H*dirs)
        emb    = self.projector(pooled)     # (B, embed_dim)
        if self.mode == "encoder":
            return emb
        return self.classifier(emb)         # (B, num_classes)

    def get_embedding(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_proj(x)
        out, _ = self.lstm(x)
        pooled = self.attn(out)
        return self.projector(pooled)

    # ── Checkpoint helpers ────────────────────────────────────────────────────
    @classmethod
    def from_config(cls, cfg: dict, mode: str = "classifier") -> "PoseModel":
        m = cfg["model"]
        p = cfg["pose"]
        return cls(
            input_size=p["input_size"],
            hidden_size=m["hidden_size"],
            num_layers=m["num_layers"],
            num_classes=cfg["num_classes"],
            embed_dim=m["embed_dim"],
            dropout=m["dropout"],
            bidirectional=m.get("bidirectional", True),
            mode=mode,
        )

    @classmethod
    def load_checkpoint(
        cls,
        ckpt_path: str,
        cfg: dict,
        mode: str = "encoder",
        device: str = "cuda",
    ) -> "PoseModel":
        model = cls.from_config(cfg, mode=mode)
        state = torch.load(ckpt_path, map_location=device)
        sd = state.get("model_state_dict", state)
        model.load_state_dict(sd, strict=True)
        return model.to(device).eval()
