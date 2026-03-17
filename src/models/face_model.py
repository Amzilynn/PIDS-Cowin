"""
src/models/face_model.py
─────────────────────────
EfficientNet-based facial emotion classifier.

Modes
-----
- classifier : full head → logits (num_classes,)
- encoder    : feature backbone → embedding (embed_dim,)

Usage
-----
    model = FaceEmotionModel(num_classes=7, embed_dim=512, mode='classifier')
    logits = model(images)              # (B, 7)

    encoder = FaceEmotionModel(num_classes=7, embed_dim=512, mode='encoder')
    feats   = encoder(images)           # (B, 512)
"""

import torch
import torch.nn as nn
import timm


class FaceEmotionModel(nn.Module):

    def __init__(
        self,
        backbone: str = "efficientnet_b2",
        num_classes: int = 7,
        embed_dim: int = 512,
        drop_rate: float = 0.3,
        pretrained: bool = True,
        mode: str = "classifier",   # 'classifier' | 'encoder'
    ) -> None:
        super().__init__()
        self.mode = mode
        self.embed_dim = embed_dim

        # ── Backbone ──────────────────────────────────────────────────────────
        self.backbone = timm.create_model(
            backbone,
            pretrained=pretrained,
            num_classes=0,          # remove original head
            drop_rate=drop_rate,
        )
        backbone_out_dim = self.backbone.num_features

        # ── Projection to embed_dim ───────────────────────────────────────────
        self.projector = nn.Sequential(
            nn.Linear(backbone_out_dim, embed_dim),
            nn.BatchNorm1d(embed_dim),
            nn.GELU(),
            nn.Dropout(drop_rate),
        )

        # ── Classification head ───────────────────────────────────────────────
        self.classifier = nn.Linear(embed_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x : (B, 3, H, W)"""
        feat = self.backbone(x)             # (B, backbone_out_dim)
        emb  = self.projector(feat)         # (B, embed_dim)
        if self.mode == "encoder":
            return emb
        return self.classifier(emb)         # (B, num_classes)

    def get_embedding(self, x: torch.Tensor) -> torch.Tensor:
        """Always returns embedding regardless of mode."""
        feat = self.backbone(x)
        return self.projector(feat)

    # ── Checkpoint helpers ────────────────────────────────────────────────────
    @classmethod
    def from_config(cls, cfg: dict, mode: str = "classifier") -> "FaceEmotionModel":
        m = cfg["model"]
        return cls(
            backbone=m["backbone"],
            num_classes=cfg["num_classes"],
            embed_dim=m["embed_dim"],
            drop_rate=m["drop_rate"],
            pretrained=m.get("pretrained", True),
            mode=mode,
        )

    @classmethod
    def load_checkpoint(
        cls,
        ckpt_path: str,
        cfg: dict,
        mode: str = "encoder",
        device: str = "cuda",
    ) -> "FaceEmotionModel":
        model = cls.from_config(cfg, mode=mode)
        state = torch.load(ckpt_path, map_location=device)
        # Support checkpoints that wrap weights under 'model_state_dict'
        sd = state.get("model_state_dict", state)
        model.load_state_dict(sd, strict=True)
        return model.to(device).eval()
