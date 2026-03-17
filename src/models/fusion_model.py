"""
src/models/fusion_model.py
───────────────────────────
Late-fusion model that combines frozen face + pose embeddings.

Fusion strategies
─────────────────
  concat_mlp : [face_feat | pose_feat] → MLP → logits        (default)
  attention  : cross-attention between modalities → MLP → logits
  gated      : learnable sigmoid gate per dimension → MLP → logits
"""

from typing import List, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from src.models.face_model import FaceEmotionModel
from src.models.pose_model import PoseModel


# ── Gated fusion ─────────────────────────────────────────────────────────────

class GatedFusion(nn.Module):
    def __init__(self, face_dim: int, pose_dim: int, out_dim: int) -> None:
        super().__init__()
        total = face_dim + pose_dim
        self.gate = nn.Sequential(
            nn.Linear(total, total),
            nn.Sigmoid(),
        )
        self.proj = nn.Linear(total, out_dim)

    def forward(self, face: torch.Tensor, pose: torch.Tensor) -> torch.Tensor:
        cat  = torch.cat([face, pose], dim=-1)
        gated = cat * self.gate(cat)
        return self.proj(gated)


# ── Cross-attention fusion ────────────────────────────────────────────────────

class CrossAttentionFusion(nn.Module):
    def __init__(self, face_dim: int, pose_dim: int, out_dim: int,
                 num_heads: int = 4) -> None:
        super().__init__()
        # Project both to same dim
        common = max(face_dim, pose_dim)
        self.face_proj = nn.Linear(face_dim, common)
        self.pose_proj = nn.Linear(pose_dim, common)
        self.attn = nn.MultiheadAttention(common, num_heads, batch_first=True)
        self.proj = nn.Linear(common, out_dim)

    def forward(self, face: torch.Tensor, pose: torch.Tensor) -> torch.Tensor:
        f = self.face_proj(face).unsqueeze(1)   # (B, 1, C)
        p = self.pose_proj(pose).unsqueeze(1)   # (B, 1, C)
        x = torch.cat([f, p], dim=1)            # (B, 2, C)
        attn_out, _ = self.attn(x, x, x)
        pooled = attn_out.mean(dim=1)            # (B, C)
        return self.proj(pooled)


# ── MLP head ──────────────────────────────────────────────────────────────────

def build_mlp(in_dim: int, hidden_dims: List[int], out_dim: int,
              dropout: float) -> nn.Sequential:
    layers: List[nn.Module] = []
    prev = in_dim
    for h in hidden_dims:
        layers += [nn.Linear(prev, h), nn.BatchNorm1d(h), nn.GELU(),
                   nn.Dropout(dropout)]
        prev = h
    layers.append(nn.Linear(prev, out_dim))
    return nn.Sequential(*layers)


# ── Main fusion model ─────────────────────────────────────────────────────────

class FusionModel(nn.Module):

    def __init__(
        self,
        face_model: FaceEmotionModel,
        pose_model: PoseModel,
        num_classes: int = 7,
        fusion_type: str = "concat_mlp",
        hidden_dims: List[int] = None,
        dropout: float = 0.4,
        freeze_branches: bool = True,
    ) -> None:
        super().__init__()
        self.face_model = face_model
        self.pose_model = pose_model

        face_dim = face_model.embed_dim
        pose_dim = pose_model.embed_dim
        hidden_dims = hidden_dims or [384, 128]

        if freeze_branches:
            for p in self.face_model.parameters():
                p.requires_grad = False
            for p in self.pose_model.parameters():
                p.requires_grad = False

        # ── Fusion layer ──────────────────────────────────────────────────────
        self.fusion_type = fusion_type
        if fusion_type == "concat_mlp":
            self.fusion_head = build_mlp(face_dim + pose_dim, hidden_dims,
                                         num_classes, dropout)
        elif fusion_type == "attention":
            attn_out = max(face_dim, pose_dim)
            self.fusion_layer = CrossAttentionFusion(face_dim, pose_dim, attn_out)
            self.fusion_head  = build_mlp(attn_out, hidden_dims, num_classes, dropout)
        elif fusion_type == "gated":
            gated_out = max(face_dim, pose_dim)
            self.fusion_layer = GatedFusion(face_dim, pose_dim, gated_out)
            self.fusion_head  = build_mlp(gated_out, hidden_dims, num_classes, dropout)
        else:
            raise ValueError(f"Unknown fusion_type: {fusion_type}")

    def forward(
        self,
        face_img: torch.Tensor,
        pose_seq: torch.Tensor,
    ) -> torch.Tensor:
        """
        face_img : (B, 3, H, W)
        pose_seq : (B, T, 132)
        returns  : logits (B, num_classes)
        """
        face_feat = self.face_model.get_embedding(face_img)   # (B, face_dim)
        pose_feat = self.pose_model.get_embedding(pose_seq)   # (B, pose_dim)

        if self.fusion_type == "concat_mlp":
            fused = torch.cat([face_feat, pose_feat], dim=-1)
        else:
            fused = self.fusion_layer(face_feat, pose_feat)

        return self.fusion_head(fused)

    # ── Checkpoint helpers ────────────────────────────────────────────────────
    @classmethod
    def from_config(
        cls,
        cfg: dict,
        face_cfg: dict,
        pose_cfg: dict,
        device: str = "cuda",
    ) -> "FusionModel":
        face_model = FaceEmotionModel.load_checkpoint(
            cfg["face_ckpt"], face_cfg, mode="encoder", device=device)
        pose_model = PoseModel.load_checkpoint(
            cfg["pose_ckpt"], pose_cfg, mode="encoder", device=device)

        m = cfg["model"]
        return cls(
            face_model=face_model,
            pose_model=pose_model,
            num_classes=cfg["num_classes"],
            fusion_type=m["fusion_type"],
            hidden_dims=m["hidden_dims"],
            dropout=m["dropout"],
            freeze_branches=cfg.get("freeze_branches", True),
        )

    @classmethod
    def load_checkpoint(
        cls,
        ckpt_path: str,
        cfg: dict,
        face_cfg: dict,
        pose_cfg: dict,
        device: str = "cuda",
    ) -> "FusionModel":
        model = cls.from_config(cfg, face_cfg, pose_cfg, device=device)
        state = torch.load(ckpt_path, map_location=device)
        sd = state.get("model_state_dict", state)
        model.load_state_dict(sd, strict=False)
        return model.to(device).eval()
