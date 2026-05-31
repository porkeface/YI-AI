"""易经知识库模块

存储易经原文（卦辞、爻辞），并提供基于关键词的检索功能。
MVP阶段使用静态数据 + 关键词匹配，后续可升级为向量数据库。

用法：
    kb = KnowledgeBase()
    context = kb.retrieve("乾", "事业")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KnowledgeEntry:
    """知识条目"""
    hexagram_name: str
    category: str        # "卦辞" | "爻辞" | "象辞"
    content: str
    keywords: tuple[str, ...]


# 六十四卦核心原文（精选关键卦，覆盖常见占卜场景）
_HEXAGRAM_KNOWLEDGE: list[KnowledgeEntry] = [
    # ---- 乾卦 ----
    KnowledgeEntry("乾", "卦辞", "乾：元亨利贞。", ("乾", "天", "创始", "刚健")),
    KnowledgeEntry("乾", "象辞", "天行健，君子以自强不息。", ("乾", "天", "自强", "刚健")),
    KnowledgeEntry("乾", "爻辞", "初九：潜龙勿用。", ("乾", "潜伏", "等待", "积蓄")),
    KnowledgeEntry("乾", "爻辞", "九二：见龙在田，利见大人。", ("乾", "显现", "贵人", "发展")),
    KnowledgeEntry("乾", "爻辞", "九五：飞龙在天，利见大人。", ("乾", "鼎盛", "成功", "高位")),
    KnowledgeEntry("乾", "爻辞", "上九：亢龙有悔。", ("乾", "过度", "衰退", "警示")),
    KnowledgeEntry("乾", "爻辞", "用九：见群龙无首，吉。", ("乾", "群龙", "无首", "吉利")),

    # ---- 坤卦 ----
    KnowledgeEntry("坤", "卦辞", "坤：元亨，利牝马之贞。君子有攸往，先迷后得主。", ("坤", "地", "柔顺", "包容")),
    KnowledgeEntry("坤", "象辞", "地势坤，君子以厚德载物。", ("坤", "地", "厚德", "包容", "承载")),
    KnowledgeEntry("坤", "爻辞", "初六：履霜，坚冰至。", ("坤", "征兆", "预见", "防备")),
    KnowledgeEntry("坤", "爻辞", "六二：直方大，不习无不利。", ("坤", "正直", "端方", "自然")),
    KnowledgeEntry("坤", "爻辞", "六五：黄裳，元吉。", ("坤", "中正", "谦逊", "大吉")),

    # ---- 屯卦 ----
    KnowledgeEntry("屯", "卦辞", "屯：元亨利贞，勿用有攸往，利建侯。", ("屯", "初生", "困难", "创业", "起步")),
    KnowledgeEntry("屯", "象辞", "云雷屯，君子以经纶。", ("屯", "开创", "经营", "布局")),

    # ---- 蒙卦 ----
    KnowledgeEntry("蒙", "卦辞", "蒙：亨。匪我求童蒙，童蒙求我。初筮告，再三渎，渎则不告。利贞。", ("蒙", "启蒙", "学习", "教育", "求知")),
    KnowledgeEntry("蒙", "象辞", "山下出泉，蒙。君子以果行育德。", ("蒙", "学习", "果断", "培育")),

    # ---- 需卦 ----
    KnowledgeEntry("需", "卦辞", "需：有孚，光亨，贞吉。利涉大川。", ("需", "等待", "耐心", "信心", "涉险")),
    KnowledgeEntry("需", "象辞", "云上于天，需。君子以饮食宴乐。", ("需", "等待", "享受", "从容")),

    # ---- 讼卦 ----
    KnowledgeEntry("讼", "卦辞", "讼：有孚窒惕，中吉，终凶。利见大人，不利涉大川。", ("讼", "争讼", "纠纷", "官司", "诉讼")),
    KnowledgeEntry("讼", "象辞", "天与水违行，讼。君子以作事谋始。", ("讼", "纠纷", "预防", "谋略")),

    # ---- 师卦 ----
    KnowledgeEntry("师", "卦辞", "师：贞，丈人吉，无咎。", ("师", "军队", "领导", "统帅", "团队")),
    KnowledgeEntry("师", "象辞", "地中有水，师。君子以容民畜众。", ("师", "领导", "容纳", "积累")),

    # ---- 比卦 ----
    KnowledgeEntry("比", "卦辞", "比：吉。原筮元永贞，无咎。不宁方来，后夫凶。", ("比", "亲附", "合作", "团结", "辅佐")),
    KnowledgeEntry("比", "象辞", "地上有水，比。先王以建万国，亲诸侯。", ("比", "合作", "联盟", "亲近")),

    # ---- 小畜卦 ----
    KnowledgeEntry("小畜", "卦辞", "小畜：亨。密云不雨，自我西郊。", ("小畜", "积蓄", "小成", "酝酿", "云")),
    KnowledgeEntry("小畜", "象辞", "风行天上，小畜。君子以懿文德。", ("小畜", "积蓄", "修养", "文德")),

    # ---- 履卦 ----
    KnowledgeEntry("履", "卦辞", "履：履虎尾，不咥人，亨。", ("履", "实践", "谨慎", "风险", "行走")),
    KnowledgeEntry("履", "象辞", "上天下泽，履。君子以辩上下，定民志。", ("履", "实践", "明辨", "秩序")),

    # ---- 泰卦 ----
    KnowledgeEntry("泰", "卦辞", "泰：小往大来，吉亨。", ("泰", "通泰", "顺利", "吉祥", "繁荣")),
    KnowledgeEntry("泰", "象辞", "天地交，泰。后以财成天地之道。", ("泰", "通达", "和谐", "调和")),
    KnowledgeEntry("泰", "爻辞", "九三：无平不陂，无往不复。艰贞无咎。", ("泰", "转化", "守正", "居安思危")),

    # ---- 否卦 ----
    KnowledgeEntry("否", "卦辞", "否之匪人，不利君子贞，大往小来。", ("否", "闭塞", "不利", "困顿", "阻碍")),
    KnowledgeEntry("否", "象辞", "天地不交，否。君子以俭德辟难。", ("否", "闭塞", "节俭", "避难")),
    KnowledgeEntry("否", "爻辞", "九五：休否，大人吉。其亡其亡，系于苞桑。", ("否", "转机", "警醒", "稳定")),

    # ---- 同人卦 ----
    KnowledgeEntry("同人", "卦辞", "同人于野，亨。利涉大川，利君子贞。", ("同人", "志同道合", "合作", "团队", "同行")),

    # ---- 大有卦 ----
    KnowledgeEntry("大有", "卦辞", "大有：元亨。", ("大有", "丰收", "富有", "大成", "丰盛")),
    KnowledgeEntry("大有", "象辞", "火在天上，大有。君子以遏恶扬善，顺天休命。", ("大有", "丰收", "扬善", "顺天")),

    # ---- 谦卦 ----
    KnowledgeEntry("谦", "卦辞", "谦：亨，君子有终。", ("谦", "谦虚", "谦逊", "低调", "美德")),
    KnowledgeEntry("谦", "象辞", "地中有山，谦。君子以裒多益寡，称物平施。", ("谦", "谦虚", "平衡", "公平")),
    KnowledgeEntry("谦", "爻辞", "六二：鸣谦，贞吉。", ("谦", "谦虚", "名声", "正吉")),

    # ---- 豫卦 ----
    KnowledgeEntry("豫", "卦辞", "豫：利建侯行师。", ("豫", "愉悦", "预备", "行动", "建功")),

    # ---- 随卦 ----
    KnowledgeEntry("随", "卦辞", "随：元亨利贞，无咎。", ("随", "随从", "适应", "灵活", "顺势")),

    # ---- 蛊卦 ----
    KnowledgeEntry("蛊", "卦辞", "蛊：元亨，利涉大川。先甲三日，后甲三日。", ("蛊", "整治", "革新", "腐败", "修复")),

    # ---- 临卦 ----
    KnowledgeEntry("临", "卦辞", "临：元亨利贞。至于八月有凶。", ("临", "临近", "亲临", "领导", "治理")),

    # ---- 观卦 ----
    KnowledgeEntry("观", "卦辞", "观：盥而不荐，有孚颙若。", ("观", "观察", "审视", "示范", "感悟")),

    # ---- 噬嗑卦 ----
    KnowledgeEntry("噬嗑", "卦辞", "噬嗑：亨。利用狱。", ("噬嗑", "决断", "刑罚", "障碍", "去除")),

    # ---- 贲卦 ----
    KnowledgeEntry("贲", "卦辞", "贲：亨。小利有攸往。", ("贲", "装饰", "文采", "外表", "修饰")),

    # ---- 剥卦 ----
    KnowledgeEntry("剥", "卦辞", "剥：不利有攸往。", ("剥", "剥落", "衰退", "不利", "消亡")),

    # ---- 复卦 ----
    KnowledgeEntry("复", "卦辞", "复：亨。出入无疾，朋来无咎。反复其道，七日来复。利有攸往。", ("复", "回复", "回归", "复兴", "转机")),
    KnowledgeEntry("复", "象辞", "雷在地中，复。先王以至日闭关。", ("复", "回归", "静养", "修整")),

    # ---- 无妄卦 ----
    KnowledgeEntry("无妄", "卦辞", "无妄：元亨利贞。其匪正有眚，不利有攸往。", ("无妄", "无妄", "真实", "正直", "意外")),

    # ---- 大畜卦 ----
    KnowledgeEntry("大畜", "卦辞", "大畜：利贞，不家食吉。利涉大川。", ("大畜", "大积蓄", "厚积", "外出", "涉险")),

    # ---- 颐卦 ----
    KnowledgeEntry("颐", "卦辞", "颐：贞吉。观颐，自求口实。", ("颐", "养生", "饮食", "修养", "自给")),

    # ---- 大过卦 ----
    KnowledgeEntry("大过", "卦辞", "大过：栋桡，利有攸往，亨。", ("大过", "非常", "过度", "栋梁", "突破")),

    # ---- 坎卦 ----
    KnowledgeEntry("坎", "卦辞", "习坎：有孚，维心亨，行有尚。", ("坎", "险难", "陷阱", "坎坷", "考验")),
    KnowledgeEntry("坎", "象辞", "水洊至，习坎。君子以常德行，习教事。", ("坎", "险难", "坚持", "学习")),

    # ---- 离卦 ----
    KnowledgeEntry("离", "卦辞", "离：利贞，亨。畜牝牛，吉。", ("离", "光明", "附丽", "文明", "依附")),
    KnowledgeEntry("离", "象辞", "明两作，离。大人以继明照于四方。", ("离", "光明", "照耀", "传承")),

    # ---- 咸卦 ----
    KnowledgeEntry("咸", "卦辞", "咸：亨，利贞，取女吉。", ("咸", "感应", "感情", "婚姻", "恋爱")),
    KnowledgeEntry("咸", "象辞", "山上有泽，咸。君子以虚受人。", ("咸", "感应", "虚心", "接受")),

    # ---- 恒卦 ----
    KnowledgeEntry("恒", "卦辞", "恒：亨，无咎，利贞。利有攸往。", ("恒", "恒久", "持久", "坚持", "常理")),
    KnowledgeEntry("恒", "象辞", "雷风恒。君子以立不易方。", ("恒", "恒久", "坚定", "不移")),

    # ---- 遁卦 ----
    KnowledgeEntry("遁", "卦辞", "遁：亨，小利贞。", ("遁", "退避", "隐遁", "撤离", "战略转进")),

    # ---- 大壮卦 ----
    KnowledgeEntry("大壮", "卦辞", "大壮：利贞。", ("大壮", "强壮", "壮大", "气势", "有力")),
    KnowledgeEntry("大壮", "象辞", "雷在天上，大壮。君子以非礼弗履。", ("大壮", "强壮", "守礼", "自律")),

    # ---- 晋卦 ----
    KnowledgeEntry("晋", "卦辞", "晋：康侯用锡马蕃庶，昼日三接。", ("晋", "晋升", "进步", "发展", "提拔")),

    # ---- 明夷卦 ----
    KnowledgeEntry("明夷", "卦辞", "明夷：利艰贞。", ("明夷", "韬晦", "隐忍", "光明受损", "暗淡")),

    # ---- 家人卦 ----
    KnowledgeEntry("家人", "卦辞", "家人：利女贞。", ("家人", "家庭", "家人", "和睦", "治家")),

    # ---- 睽卦 ----
    KnowledgeEntry("睽", "卦辞", "睽：小事吉。", ("睽", "乖离", "分歧", "对立", "小成")),

    # ---- 蹇卦 ----
    KnowledgeEntry("蹇", "卦辞", "蹇：利西南，不利东北。利见大人，贞吉。", ("蹇", "艰难", "险阻", "困难", "退守")),

    # ---- 解卦 ----
    KnowledgeEntry("解", "卦辞", "解：利西南，无所往，其来复吉。有攸往，夙吉。", ("解", "解除", "化解", "宽松", "转机")),

    # ---- 损卦 ----
    KnowledgeEntry("损", "卦辞", "损：有孚，元吉，无咎可贞，利有攸往。", ("损", "减损", "付出", "节制", "奉献")),

    # ---- 益卦 ----
    KnowledgeEntry("益", "卦辞", "益：利有攸往，利涉大川。", ("益", "增益", "有利", "发展", "进取")),

    # ---- 夬卦 ----
    KnowledgeEntry("夬", "卦辞", "夬：扬于王庭，孚号有厉。告自邑，不利即戎。利有攸往。", ("夬", "决断", "果断", "清除", "刚毅")),

    # ---- 姤卦 ----
    KnowledgeEntry("姤", "卦辞", "姤：女壮，勿用取女。", ("姤", "相遇", "邂逅", "诱惑", "警惕")),

    # ---- 萃卦 ----
    KnowledgeEntry("萃", "卦辞", "萃：亨。王假有庙，利见大人，亨，利贞。用大牲吉，利有攸往。", ("萃", "聚集", "汇萃", "团结", "祭祀")),

    # ---- 升卦 ----
    KnowledgeEntry("升", "卦辞", "升：元亨，用见大人，勿恤，南征吉。", ("升", "上升", "晋升", "发展", "进步")),

    # ---- 困卦 ----
    KnowledgeEntry("困", "卦辞", "困：亨，贞，大人吉，无咎。有言不信。", ("困", "困境", "穷困", "坚守", "信用")),
    KnowledgeEntry("困", "象辞", "泽无水，困。君子以致命遂志。", ("困", "困境", "坚持", "志向")),

    # ---- 井卦 ----
    KnowledgeEntry("井", "卦辞", "井：改邑不改井，无丧无得。往来井井，汔至亦未繘井，羸其瓶，凶。", ("井", "井养", "不变", "滋养", "根本")),

    # ---- 革卦 ----
    KnowledgeEntry("革", "卦辞", "革：巳日乃孚，元亨利贞，悔亡。", ("革", "变革", "革新", "除旧", "更新")),
    KnowledgeEntry("革", "象辞", "泽中有火，革。君子以治历明时。", ("革", "变革", "时机", "明辨")),

    # ---- 鼎卦 ----
    KnowledgeEntry("鼎", "卦辞", "鼎：元吉，亨。", ("鼎", "鼎新", "更新", "烹饪", "养贤")),

    # ---- 震卦 ----
    KnowledgeEntry("震", "卦辞", "震：亨。震来虩虩，笑言哑哑。震惊百里，不丧匕鬯。", ("震", "震动", "惊雷", "奋起", "警醒")),
    KnowledgeEntry("震", "象辞", "洊雷，震。君子以恐惧修省。", ("震", "震动", "警醒", "反省")),

    # ---- 艮卦 ----
    KnowledgeEntry("艮", "卦辞", "艮其背，不获其身，行其庭，不见其人，无咎。", ("艮", "止住", "停止", "静止", "知止")),
    KnowledgeEntry("艮", "象辞", "兼山，艮。君子以思不出其位。", ("艮", "止住", "本分", "守位")),

    # ---- 渐卦 ----
    KnowledgeEntry("渐", "卦辞", "渐：女归吉，利贞。", ("渐", "渐进", "循序", "稳步", "发展")),
    KnowledgeEntry("渐", "象辞", "山上有木，渐。君子以居贤德善俗。", ("渐", "渐进", "积累", "善俗")),

    # ---- 归妹卦 ----
    KnowledgeEntry("归妹", "卦辞", "归妹：征凶，无攸利。", ("归妹", "婚嫁", "归宿", "冒进", "不利")),

    # ---- 丰卦 ----
    KnowledgeEntry("丰", "卦辞", "丰：亨。王假之，勿忧，宜日中。", ("丰", "丰盛", "盛大", "光明", "鼎盛")),

    # ---- 旅卦 ----
    KnowledgeEntry("旅", "卦辞", "旅：小亨，旅贞吉。", ("旅", "旅行", "旅途", "客居", "出行")),

    # ---- 巽卦 ----
    KnowledgeEntry("巽", "卦辞", "巽：小亨，利有攸往，利见大人。", ("巽", "顺从", "谦逊", "柔顺", "渗透")),

    # ---- 兑卦 ----
    KnowledgeEntry("兑", "卦辞", "兑：亨，利贞。", ("兑", "喜悦", "和悦", "沟通", "快乐")),
    KnowledgeEntry("兑", "象辞", "丽泽，兑。君子以朋友讲习。", ("兑", "喜悦", "交流", "学习")),

    # ---- 涣卦 ----
    KnowledgeEntry("涣", "卦辞", "涣：亨。王假有庙，利涉大川，利贞。", ("涣", "涣散", "离散", "挽救", "聚合")),

    # ---- 节卦 ----
    KnowledgeEntry("节", "卦辞", "节：亨。苦节不可贞。", ("节", "节制", "节约", "限度", "适中")),
    KnowledgeEntry("节", "象辞", "泽上有水，节。君子以制数度，议德行。", ("节", "节制", "制度", "规范")),

    # ---- 中孚卦 ----
    KnowledgeEntry("中孚", "卦辞", "中孚：豚鱼吉，利涉大川，利贞。", ("中孚", "诚信", "内心", "信任", "真诚")),

    # ---- 小过卦 ----
    KnowledgeEntry("小过", "卦辞", "小过：亨，利贞。可小事，不可大事。飞鸟遗之音，不宜上宜下，大吉。", ("小过", "小过", "适度", "谦卑", "小事")),

    # ---- 既济卦 ----
    KnowledgeEntry("既济", "卦辞", "既济：亨小，利贞。初吉终乱。", ("既济", "完成", "成功", "守成", "警惕")),
    KnowledgeEntry("既济", "象辞", "水在火上，既济。君子以思患而豫防之。", ("既济", "完成", "预防", "思患")),

    # ---- 未济卦 ----
    KnowledgeEntry("未济", "卦辞", "未济：亨。小狐汔济，濡其尾，无攸利。", ("未济", "未完成", "过渡", "谨慎", "继续")),
    KnowledgeEntry("未济", "象辞", "火在水上，未济。君子以慎辨物居方。", ("未济", "未完成", "谨慎", "辨别")),
]

# 问题关键词到主题映射
_QUESTION_TOPIC_MAP: dict[str, tuple[str, ...]] = {
    "事业": ("晋升", "发展", "领导", "创业", "积蓄"),
    "工作": ("发展", "坚持", "进取", "团队"),
    "财运": ("丰盛", "富有", "积蓄", "增益"),
    "婚姻": ("感情", "婚姻", "感应", "和谐", "家庭"),
    "感情": ("感情", "恋爱", "感应", "和谐"),
    "健康": ("养生", "修养", "坚持", "恢复"),
    "考试": ("学习", "进步", "积累", "渐进"),
    "出行": ("旅行", "出行", "涉险", "谨慎"),
    "官司": ("纠纷", "诉讼", "决断", "公正"),
}

# 卦序号 -> 卦名（文王六十四卦序）
_HEXAGRAM_ID_TO_NAME: dict[int, str] = {
    1: "乾", 2: "坤", 3: "屯", 4: "蒙", 5: "需", 6: "讼", 7: "师", 8: "比",
    9: "小畜", 10: "履", 11: "泰", 12: "否", 13: "同人", 14: "大有", 15: "谦", 16: "豫",
    17: "随", 18: "蛊", 19: "临", 20: "观", 21: "噬嗑", 22: "贲", 23: "剥", 24: "复",
    25: "无妄", 26: "大畜", 27: "颐", 28: "大过", 29: "坎", 30: "离", 31: "咸", 32: "恒",
    33: "遁", 34: "大壮", 35: "晋", 36: "明夷", 37: "家人", 38: "睽", 39: "蹇", 40: "解",
    41: "损", 42: "益", 43: "夬", 44: "姤", 45: "萃", 46: "升", 47: "困", 48: "井",
    49: "革", 50: "鼎", 51: "震", 52: "艮", 53: "渐", 54: "归妹", 55: "丰", 56: "旅",
    57: "巽", 58: "兑", 59: "涣", 60: "节", 61: "中孚", 62: "小过", 63: "既济", 64: "未济",
}

# 卦名 -> 卦序号（反向映射，运行时构建）
_NAME_TO_HEXAGRAM_ID: dict[str, int] = {v: k for k, v in _HEXAGRAM_ID_TO_NAME.items()}


def _load_line_texts_from_json() -> dict[str, dict[int, dict[str, str]]]:
    """从 line_texts.json 加载全部384爻辞数据到内存缓存

    JSON 使用的键名:
        - hexagram_id: 卦序号 (int, 1-64)
        - position: 爻位置 (int, 1-6)
        - yao_name: 爻名 (str, 如"初九")
        - text: 爻辞 (str)
        - image_text: 小象辞 (str)

    Returns:
        {卦名: {爻位置: {"text": 爻辞, "image_text": 小象辞}}}
    """
    json_path = Path(__file__).resolve().parent.parent / "foundation" / "data" / "line_texts.json"
    if not json_path.exists():
        logger.warning("line_texts.json 不存在: %s", json_path)
        return {}

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error("加载 line_texts.json 失败: %s", e)
        return {}

    result: dict[str, dict[int, dict[str, str]]] = {}
    for d in data:
        hex_id = d.get("hexagram_id", 0)
        position = d.get("position", 0)
        hex_name = _HEXAGRAM_ID_TO_NAME.get(hex_id, "")

        if hex_name and 1 <= position <= 6:
            if hex_name not in result:
                result[hex_name] = {}
            result[hex_name][position] = {
                "text": d.get("text", ""),
                "image_text": d.get("image_text", ""),
            }

    total = sum(len(v) for v in result.values())
    logger.info("从 line_texts.json 加载了 %d 卦共 %d 条爻辞", len(result), total)
    return result


# 模块级缓存：加载全部384爻辞
_LINE_TEXTS: dict[str, dict[int, dict[str, str]]] = _load_line_texts_from_json()


class KnowledgeBase:
    """易经知识库

    提供基于关键词的易经原文检索。
    支持可选的向量语义检索：传入 vector_backend 和 embedding_service 即可启用，
    否则自动降级到关键词匹配（向后兼容）。
    """

    def __init__(
        self,
        vector_backend: Any | None = None,
        embedding_service: Any | None = None,
    ) -> None:
        self._entries = _HEXAGRAM_KNOWLEDGE
        self._vector_backend = vector_backend
        self._embedding_service = embedding_service

    def retrieve(
        self,
        hexagram_name: str,
        question_type: str = "通用",
        max_entries: int = 5,
    ) -> list[str]:
        """检索与卦名和问题类型相关的知识条目

        优先尝试向量语义检索，失败时降级到关键词匹配。

        Args:
            hexagram_name: 卦名（如"乾"、"坤"）
            question_type: 问题类型（如"事业"、"财运"）
            max_entries: 最大返回条目数

        Returns:
            相关知识条目文本列表
        """
        # 如果有向量后端，用语义检索
        if self._vector_backend and self._embedding_service:
            try:
                return self._vector_retrieve(hexagram_name, question_type, max_entries)
            except Exception as e:
                logger.warning("Vector search failed, falling back to keyword: %s", e)

        # 降级到关键词匹配
        return self._keyword_retrieve(hexagram_name, question_type, max_entries)

    def _vector_retrieve(
        self,
        hexagram_name: str,
        question_type: str,
        max_entries: int,
    ) -> list[str]:
        """向量语义检索"""
        query = f"{hexagram_name} {question_type}"
        vector = self._embedding_service.embed(query)
        results = self._vector_backend.search(vector, top_k=max_entries)
        return [r.get("content", "") for r in results if r.get("content")]

    def _keyword_retrieve(
        self,
        hexagram_name: str,
        question_type: str,
        max_entries: int,
    ) -> list[str]:
        """关键词匹配检索（原有逻辑）"""
        results: list[str] = []

        # 1. 当前卦的原文（优先级最高）
        hex_entries = [
            e for e in self._entries if e.hexagram_name == hexagram_name
        ]
        for entry in hex_entries[:3]:
            results.append(f"[{entry.hexagram_name}·{entry.category}] {entry.content}")

        if len(results) >= max_entries:
            return results[:max_entries]

        # 2. 根据问题类型补充相关主题的条目
        topic_keywords = _QUESTION_TOPIC_MAP.get(question_type, ())
        if topic_keywords:
            related = [
                e for e in self._entries
                if e.hexagram_name != hexagram_name
                and any(kw in e.keywords for kw in topic_keywords)
            ]
            for entry in related[: max_entries - len(results)]:
                results.append(
                    f"[{entry.hexagram_name}·{entry.category}] {entry.content}"
                )

        return results[:max_entries]

    def get_hexagram_text(self, hexagram_name: str) -> str:
        """获取卦的完整原文（卦辞+象辞+主要爻辞）

        Args:
            hexagram_name: 卦名

        Returns:
            格式化的原文文本
        """
        entries = [
            e for e in self._entries if e.hexagram_name == hexagram_name
        ]
        if not entries:
            return ""

        parts: list[str] = []
        for entry in entries:
            parts.append(f"{entry.category}：{entry.content}")
        return "\n".join(parts)

    def get_line_text(
        self,
        hexagram_name: str,
        line_position: int,
    ) -> dict[str, str] | None:
        """获取指定卦、指定爻位的爻辞数据

        优先从内存缓存 _LINE_TEXTS 读取（已预加载全部384爻）。
        如果缓存为空（JSON 文件缺失），返回 None。

        Args:
            hexagram_name: 卦名（如 "乾"、"坤"、"小畜"）
            line_position: 爻位置 (1-6)

        Returns:
            {"text": "初九：潜龙勿用。", "image_text": "潜龙勿用，阳在下也。"}
            未找到时返回 None
        """
        if not (1 <= line_position <= 6):
            return None
        hex_lines = _LINE_TEXTS.get(hexagram_name)
        if hex_lines is None:
            return None
        return hex_lines.get(line_position)

    @property
    def total_entries(self) -> int:
        """知识库条目总数"""
        return len(self._entries)
