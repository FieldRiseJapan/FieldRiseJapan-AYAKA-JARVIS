from dataclasses import dataclass


# Layout contract for the 1080x1920 CENTER monitor: CORE dominates the middle,
# while compact metrics remain in a two-by-two region at the bottom.
CENTER_CORE_SIZE = (760, 820)
CARD_REGION = "bottom"
CARD_GRID_COLUMNS = 2
CARD_GRID_ROWS = 2


@dataclass(frozen=True)
class DashboardCard:
    key: str
    title: str
    metric: str
    value: str = "-- / DATA WAITING"


CENTER_CARDS = (
    DashboardCard("soundon", "SoundOn", "今月収益", "—"),
    DashboardCard("youtube", "YouTube", "直近28日再生", "—"),
    DashboardCard("tiktok", "TikTok", "直近7日再生"),
    DashboardCard("instagram", "Instagram", "直近30日リーチ"),
)
