from dataclasses import dataclass


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
