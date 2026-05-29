"""64卦静态数据模块

包含所有64卦的完整数据：卦序号、卦名、上卦、下卦、二进制、卦辞、象辞、五行属性。
"""

from __future__ import annotations

from foundation.types import Element, TrigramName


# 卦数据结构：(id, name, upper, lower, binary, element, judgment, image)
HexagramData = tuple[
    int, str, TrigramName, TrigramName, str, Element, str, str
]

# 64卦数据表
# binary: 6位二进制，从下到上（第1爻到第6爻）
HEXAGRAM_DATA: list[HexagramData] = [
    # 1. 乾为天
    (1, "乾为天", TrigramName.QIAN, TrigramName.QIAN, "111111",
     Element.METAL, "元亨利贞", "天行健，君子以自强不息"),
    # 2. 坤为地
    (2, "坤为地", TrigramName.KUN, TrigramName.KUN, "000000",
     Element.EARTH, "元亨，利牝马之贞", "地势坤，君子以厚德载物"),
    # 3. 水雷屯
    (3, "水雷屯", TrigramName.KAN, TrigramName.ZHEN, "100010",
     Element.WATER, "元亨利贞，勿用有攸往，利建侯", "云雷屯，君子以经纶"),
    # 4. 山水蒙
    (4, "山水蒙", TrigramName.GEN, TrigramName.KAN, "010001",
     Element.EARTH, "亨，匪我求童蒙，童蒙求我", "山下出泉，蒙，君子以果行育德"),
    # 5. 水天需
    (5, "水天需", TrigramName.KAN, TrigramName.QIAN, "111010",
     Element.WATER, "有孚，光亨，贞吉，利涉大川", "云上于天，需，君子以饮食宴乐"),
    # 6. 天水讼
    (6, "天水讼", TrigramName.QIAN, TrigramName.KAN, "010111",
     Element.METAL, "有孚窒惕，中吉，终凶，利见大人", "天与水违行，讼，君子以作事谋始"),
    # 7. 地水师
    (7, "地水师", TrigramName.KUN, TrigramName.KAN, "010000",
     Element.EARTH, "贞，丈人吉，无咎", "地中有水，师，君子以容民畜众"),
    # 8. 水地比
    (8, "水地比", TrigramName.KAN, TrigramName.KUN, "000010",
     Element.WATER, "吉，原筮元永贞，无咎", "地上有水，比，先王以建万国，亲诸侯"),
    # 9. 风天小畜
    (9, "风天小畜", TrigramName.XUN, TrigramName.QIAN, "111011",
     Element.WOOD, "亨，密云不雨，自我西郊", "风行天上，小畜，君子以懿文德"),
    # 10. 天泽履
    (10, "天泽履", TrigramName.QIAN, TrigramName.DUI, "110111",
     Element.METAL, "履虎尾，不咥人，亨", "上天下泽，履，君子以辨上下，定民志"),
    # 11. 地天泰
    (11, "地天泰", TrigramName.KUN, TrigramName.QIAN, "111000",
     Element.EARTH, "小往大来，吉亨", "天地交，泰，后以财成天地之道"),
    # 12. 天地否
    (12, "天地否", TrigramName.QIAN, TrigramName.KUN, "000111",
     Element.METAL, "否之匪人，不利君子贞，大往小来", "天地不交，否，君子以俭德辟难"),
    # 13. 天火同人
    (13, "天火同人", TrigramName.QIAN, TrigramName.LI, "101111",
     Element.METAL, "同人于野，亨，利涉大川，利君子贞", "天与火，同人，君子以类族辨物"),
    # 14. 火天大有
    (14, "火天大有", TrigramName.LI, TrigramName.QIAN, "111101",
     Element.FIRE, "元亨", "火在天上，大有，君子以遏恶扬善，顺天休命"),
    # 15. 地山谦
    (15, "地山谦", TrigramName.KUN, TrigramName.GEN, "001000",
     Element.EARTH, "亨，君子有终", "地中有山，谦，君子以裒多益寡，称物平施"),
    # 16. 雷地豫
    (16, "雷地豫", TrigramName.ZHEN, TrigramName.KUN, "000100",
     Element.WOOD, "利建侯行师", "雷出地奋，豫，先王以作乐崇德"),
    # 17. 泽雷随
    (17, "泽雷随", TrigramName.DUI, TrigramName.ZHEN, "100110",
     Element.METAL, "元亨利贞，无咎", "泽中有雷，随，君子以向晦入宴息"),
    # 18. 山风蛊
    (18, "山风蛊", TrigramName.GEN, TrigramName.XUN, "011001",
     Element.EARTH, "元亨，利涉大川，先甲三日，后甲三日", "山下有风，蛊，君子以振民育德"),
    # 19. 地泽临
    (19, "地泽临", TrigramName.KUN, TrigramName.DUI, "110000",
     Element.EARTH, "元亨利贞，至于八月有凶", "泽上有地，临，君子以教思无穷，容保民无疆"),
    # 20. 风地观
    (20, "风地观", TrigramName.XUN, TrigramName.KUN, "000011",
     Element.WOOD, "盥而不荐，有孚颙若", "风行地上，观，先王以省方观民设教"),
    # 21. 火雷噬嗑
    (21, "火雷噬嗑", TrigramName.LI, TrigramName.ZHEN, "100101",
     Element.FIRE, "亨，利用狱", "雷电噬嗑，先王以明罚敕法"),
    # 22. 山火贲
    (22, "山火贲", TrigramName.GEN, TrigramName.LI, "101001",
     Element.EARTH, "亨，小利有攸往", "山下有火，贲，君子以明庶政，无敢折狱"),
    # 23. 山地剥
    (23, "山地剥", TrigramName.GEN, TrigramName.KUN, "000001",
     Element.EARTH, "不利有攸往", "山附于地，剥，上以厚下安宅"),
    # 24. 地雷复
    (24, "地雷复", TrigramName.KUN, TrigramName.ZHEN, "100000",
     Element.EARTH, "亨，出入无疾，朋来无咎，反复其道", "雷在地中，复，先王以至日闭关"),
    # 25. 天雷无妄
    (25, "天雷无妄", TrigramName.QIAN, TrigramName.ZHEN, "100111",
     Element.METAL, "元亨利贞，其匪正有眚，不利有攸往", "天下雷行，物与无妄，先王以茂对时育万物"),
    # 26. 山天大畜
    (26, "山天大畜", TrigramName.GEN, TrigramName.QIAN, "111001",
     Element.EARTH, "利贞，不家食吉，利涉大川", "天在山中，大畜，君子以多识前言往行，以畜其德"),
    # 27. 山雷颐
    (27, "山雷颐", TrigramName.GEN, TrigramName.ZHEN, "100001",
     Element.EARTH, "贞吉，观颐，自求口实", "山下有雷，颐，君子以慎言语，节饮食"),
    # 28. 泽风大过
    (28, "泽风大过", TrigramName.DUI, TrigramName.XUN, "011110",
     Element.METAL, "栋桡，利有攸往，亨", "泽灭木，大过，君子以独立不惧，遁世无闷"),
    # 29. 坎为水
    (29, "坎为水", TrigramName.KAN, TrigramName.KAN, "010010",
     Element.WATER, "习坎，有孚，维心亨，行有尚", "水洊至，习坎，君子以常德行，习教事"),
    # 30. 离为火
    (30, "离为火", TrigramName.LI, TrigramName.LI, "101101",
     Element.FIRE, "利贞，亨，畜牝牛吉", "明两作，离，大人以继明照于四方"),
    # 31. 泽山咸
    (31, "泽山咸", TrigramName.DUI, TrigramName.GEN, "001110",
     Element.METAL, "亨利贞，取女吉", "山上有泽，咸，君子以虚受人"),
    # 32. 雷风恒
    (32, "雷风恒", TrigramName.ZHEN, TrigramName.XUN, "011100",
     Element.WOOD, "亨，无咎，利贞，利有攸往", "雷风恒，君子以立不易方"),
    # 33. 天山遁
    (33, "天山遁", TrigramName.QIAN, TrigramName.GEN, "001111",
     Element.METAL, "亨，小利贞", "天下有山，遁，君子以远小人，不恶而严"),
    # 34. 雷天大壮
    (34, "雷天大壮", TrigramName.ZHEN, TrigramName.QIAN, "111100",
     Element.WOOD, "利贞", "雷在天上，大壮，君子以非礼弗履"),
    # 35. 火地晋
    (35, "火地晋", TrigramName.LI, TrigramName.KUN, "000101",
     Element.FIRE, "康侯用锡马蕃庶，昼日三接", "明出地上，晋，君子以自昭明德"),
    # 36. 地火明夷
    (36, "地火明夷", TrigramName.KUN, TrigramName.LI, "101000",
     Element.EARTH, "利艰贞", "明入地中，明夷，君子以莅众，用晦而明"),
    # 37. 风火家人
    (37, "风火家人", TrigramName.XUN, TrigramName.LI, "101011",
     Element.WOOD, "利女贞", "风自火出，家人，君子以言有物而行有恒"),
    # 38. 火泽睽
    (38, "火泽睽", TrigramName.LI, TrigramName.DUI, "110101",
     Element.FIRE, "小事吉", "上火下泽，睽，君子以同而异"),
    # 39. 水山蹇
    (39, "水山蹇", TrigramName.KAN, TrigramName.GEN, "001010",
     Element.WATER, "利西南，不利东北，利见大人，贞吉", "山上有水，蹇，君子以反身修德"),
    # 40. 雷水解
    (40, "雷水解", TrigramName.ZHEN, TrigramName.KAN, "010100",
     Element.WOOD, "利西南，无所往，其来复吉", "雷雨作，解，君子以赦过宥罪"),
    # 41. 山泽损
    (41, "山泽损", TrigramName.GEN, TrigramName.DUI, "110001",
     Element.EARTH, "有孚，元吉，无咎可贞，利有攸往", "山下有泽，损，君子以惩忿窒欲"),
    # 42. 风雷益
    (42, "风雷益", TrigramName.XUN, TrigramName.ZHEN, "100011",
     Element.WOOD, "利有攸往，利涉大川", "风雷益，君子以见善则迁，有过则改"),
    # 43. 泽天夬
    (43, "泽天夬", TrigramName.DUI, TrigramName.QIAN, "111110",
     Element.METAL, "扬于王庭，孚号有厉，告自邑", "泽上于天，夬，君子以施禄及下，居德则忌"),
    # 44. 天风姤
    (44, "天风姤", TrigramName.QIAN, TrigramName.XUN, "011111",
     Element.METAL, "女壮，勿用取女", "天下有风，姤，后以施命诰四方"),
    # 45. 泽地萃
    (45, "泽地萃", TrigramName.DUI, TrigramName.KUN, "000110",
     Element.METAL, "亨，王假有庙，利见大人，亨利贞", "泽上于地，萃，君子以除戎器，戒不虞"),
    # 46. 地风升
    (46, "地风升", TrigramName.KUN, TrigramName.XUN, "011000",
     Element.EARTH, "元亨，用见大人，勿恤，南征吉", "地中生木，升，君子以顺德，积小以高大"),
    # 47. 泽水困
    (47, "泽水困", TrigramName.DUI, TrigramName.KAN, "010110",
     Element.METAL, "亨，贞大人吉，无咎，有言不信", "泽无水，困，君子以致命遂志"),
    # 48. 水风井
    (48, "水风井", TrigramName.KAN, TrigramName.XUN, "011010",
     Element.WATER, "改邑不改井，无丧无得，往来井井", "木上有水，井，君子以劳民劝相"),
    # 49. 泽火革
    (49, "泽火革", TrigramName.DUI, TrigramName.LI, "101110",
     Element.METAL, "己日乃孚，元亨利贞，悔亡", "泽中有火，革，君子以治历明时"),
    # 50. 火风鼎
    (50, "火风鼎", TrigramName.LI, TrigramName.XUN, "011101",
     Element.FIRE, "元吉，亨", "木上有火，鼎，君子以正位凝命"),
    # 51. 震为雷
    (51, "震为雷", TrigramName.ZHEN, TrigramName.ZHEN, "100100",
     Element.WOOD, "亨，震来虩虩，笑言哑哑", "洊雷震，君子以恐惧修省"),
    # 52. 艮为山
    (52, "艮为山", TrigramName.GEN, TrigramName.GEN, "001001",
     Element.EARTH, "艮其背，不获其身，行其庭，不见其人", "兼山艮，君子以思不出其位"),
    # 53. 风山渐
    (53, "风山渐", TrigramName.XUN, TrigramName.GEN, "001011",
     Element.WOOD, "女归吉，利贞", "山上有木，渐，君子以居贤德善俗"),
    # 54. 雷泽归妹
    (54, "雷泽归妹", TrigramName.ZHEN, TrigramName.DUI, "110100",
     Element.WOOD, "征凶，无攸利", "泽上有雷，归妹，君子以永终知敝"),
    # 55. 雷火丰
    (55, "雷火丰", TrigramName.ZHEN, TrigramName.LI, "101100",
     Element.WOOD, "亨，王假之，勿忧，宜日中", "雷电皆至，丰，君子以折狱致刑"),
    # 56. 火山旅
    (56, "火山旅", TrigramName.LI, TrigramName.GEN, "001101",
     Element.FIRE, "小亨，旅贞吉", "山上有火，旅，君子以明慎用刑而不留狱"),
    # 57. 巽为风
    (57, "巽为风", TrigramName.XUN, TrigramName.XUN, "011011",
     Element.WOOD, "小亨，利有攸往，利见大人", "随风巽，君子以申命行事"),
    # 58. 兑为泽
    (58, "兑为泽", TrigramName.DUI, TrigramName.DUI, "110110",
     Element.METAL, "亨利贞", "丽泽兑，君子以朋友讲习"),
    # 59. 风水涣
    (59, "风水涣", TrigramName.XUN, TrigramName.KAN, "010011",
     Element.WOOD, "亨，王假有庙，利涉大川，利贞", "风行水上，涣，先王以享于帝立庙"),
    # 60. 水泽节
    (60, "水泽节", TrigramName.KAN, TrigramName.DUI, "110010",
     Element.WATER, "亨，苦节不可贞", "泽上有水，节，君子以制数度，议德行"),
    # 61. 风泽中孚
    (61, "风泽中孚", TrigramName.XUN, TrigramName.DUI, "110011",
     Element.WOOD, "豚鱼吉，利涉大川，利贞", "泽上有风，中孚，君子以议狱缓死"),
    # 62. 雷山小过
    (62, "雷山小过", TrigramName.ZHEN, TrigramName.GEN, "001100",
     Element.WOOD, "亨利贞，可小事，不可大事", "山上有雷，小过，君子以行过乎恭，丧过乎哀，用过乎俭"),
    # 63. 水火既济
    (63, "水火既济", TrigramName.KAN, TrigramName.LI, "101010",
     Element.WATER, "亨小利贞，初吉终乱", "水在火上，既济，君子以思患而豫防之"),
    # 64. 火水未济
    (64, "火水未济", TrigramName.LI, TrigramName.KAN, "010101",
     Element.FIRE, "亨，小狐汔济，濡其尾，无攸利", "火在水上，未济，君子以慎辨物居方"),
]