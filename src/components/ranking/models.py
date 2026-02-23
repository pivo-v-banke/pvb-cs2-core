from pydantic import BaseModel


class RankDescription(BaseModel):
    rank: int
    translate_ru: str


RANK_DESCRIPTIONS = [
    RankDescription(
        rank=-2,
        translate_ru="Факин Боцман",
    ),
    RankDescription(
        rank=-1,
        translate_ru="Факин Боцман",
    ),
    RankDescription(
        rank=0,
        translate_ru="Факин Боцман",
    ),
    RankDescription(
        rank=1,
        translate_ru="Фотограф",
    ),
    RankDescription(
        rank=2,
        translate_ru="Актёр",
    ),
    RankDescription(
        rank=3,
        translate_ru="Игрок головой",
    ),
    RankDescription(
        rank=4,
        translate_ru="Голландский штурман",
    ),
    RankDescription(
        rank=5,
        translate_ru="Б Машина",
    ),
    RankDescription(
        rank=6,
        translate_ru="Раздатчик",
    ),
    RankDescription(
        rank=7,
        translate_ru="Бэнг Бэнг",
    ),
    RankDescription(
        rank=8,
        translate_ru="Опорник хайтаба",
    ),
    RankDescription(
        rank=9,
        translate_ru="Паровоз",
    ),
    RankDescription(
        rank=10,
        translate_ru="Паровоз",
    ),
    RankDescription(
        rank=11,
        translate_ru="Паровоз",
    ),
]