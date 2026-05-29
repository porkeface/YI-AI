"""用神选取模块

根据问题类型从卦中选取用神（六亲）和用神所在的爻。

用神规则：
- 问事业/工作/官司：取官鬼为用神
- 问财运/生意/婚姻(男)：取妻财为用神
- 问考试/文书：取父母为用神
- 问子女/生育/疾病：取子孙为用神
- 问兄弟/朋友：取兄弟为用神
- 问出行/旅游：取世爻为用神
- 问婚姻(女)：取官鬼为用神
- 默认：取世爻所在六亲为用神
"""

from __future__ import annotations

from foundation.types import Hexagram, Line, SixRelation


# 问题类型到用神六亲的映射
_QUESTION_TYPE_MAP: dict[str, SixRelation] = {
    "事业": SixRelation.OFFICIAL,
    "工作": SixRelation.OFFICIAL,
    "官司": SixRelation.OFFICIAL,
    "诉讼": SixRelation.OFFICIAL,
    "财运": SixRelation.WEALTH,
    "生意": SixRelation.WEALTH,
    "婚姻": SixRelation.WEALTH,  # 默认按男问婚姻取妻财
    "婚姻男": SixRelation.WEALTH,
    "婚姻女": SixRelation.OFFICIAL,
    "考试": SixRelation.PARENT,
    "文书": SixRelation.PARENT,
    "子女": SixRelation.CHILDREN,
    "生育": SixRelation.CHILDREN,
    "疾病": SixRelation.CHILDREN,
    "健康": SixRelation.CHILDREN,
    "兄弟": SixRelation.BROTHER,
    "朋友": SixRelation.BROTHER,
}


class YongShenEngine:
    """用神选取引擎

    根据问题类型从卦中选取用神六亲，并定位用神所在的爻。
    """

    @classmethod
    def find_yong_shen(
        cls, hexagram: Hexagram, question_type: str
    ) -> SixRelation:
        """根据问题类型选取用神

        对于出行/旅游类问题，返回世爻所在的六亲。
        对于未知问题类型，也返回世爻所在的六亲。

        Args:
            hexagram: 卦对象
            question_type: 问题类型（如"事业"、"财运"等）

        Returns:
            用神对应的六亲枚举值
        """
        # 出行/旅游类：直接取世爻所在六亲
        if question_type in ("出行", "旅游"):
            return cls._get_shi_relation(hexagram)

        # 查表
        relation = _QUESTION_TYPE_MAP.get(question_type)
        if relation is not None:
            return relation

        # 默认：取世爻所在六亲
        return cls._get_shi_relation(hexagram)

    @classmethod
    def find_yong_shen_line(
        cls, hexagram: Hexagram, yong_shen: SixRelation
    ) -> Line:
        """找到用神所在的爻

        如果卦中有多个爻匹配用神六亲，返回位置最低（最旺）的那个。

        Args:
            hexagram: 卦对象
            yong_shen: 用神六亲

        Returns:
            用神所在的爻

        Raises:
            ValueError: 如果卦中没有找到用神对应的爻
        """
        for line in hexagram.lines:
            if line.six_relation == yong_shen:
                return line
        raise ValueError(
            f"卦中未找到用神 {yong_shen.value} 对应的爻"
        )

    @classmethod
    def _get_shi_relation(cls, hexagram: Hexagram) -> SixRelation:
        """获取世爻所在的六亲关系

        Args:
            hexagram: 卦对象

        Returns:
            世爻的六亲关系

        Raises:
            ValueError: 如果卦中没有世爻
        """
        for line in hexagram.lines:
            if line.is_shi:
                return line.six_relation
        raise ValueError("卦中未找到世爻")
