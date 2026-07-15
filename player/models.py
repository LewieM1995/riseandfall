from dataclasses import dataclass


@dataclass
class Player:
    id: int
    username: str
    user_id: int
    level: int
    experience: int


@dataclass
class PlayerExperience:
    level: int
    experience: int
    xp_for_next_level: int