from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class AvatarProfile:
    avatar_id: str
    name: str
    tone: str
    audience_focus: str


AVATARS: Dict[str, AvatarProfile] = {
    "ava_med": AvatarProfile(
        avatar_id="ava_med",
        name="Ava Med",
        tone="clinical, evidence-first, concise",
        audience_focus="physicians",
    ),
    "leo_pharma": AvatarProfile(
        avatar_id="leo_pharma",
        name="Leo Pharma",
        tone="practical, dispensing-focused, patient-safe",
        audience_focus="pharmacists",
    ),
}


def list_avatars() -> List[AvatarProfile]:
    return list(AVATARS.values())


def get_avatar(avatar_id: str) -> AvatarProfile:
    avatar = AVATARS.get(avatar_id)
    if avatar is None:
        valid = ", ".join(sorted(AVATARS.keys()))
        raise ValueError(f"Unknown avatar_id '{avatar_id}'. Valid values: {valid}")
    return avatar
