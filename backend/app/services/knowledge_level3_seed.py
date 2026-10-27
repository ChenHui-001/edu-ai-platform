"""知识点 level3 种子：把现有 level2 章节拆到「可命题粒度」。

## 为什么需要这一层

需求要求「年级-学期-单元-章节-知识点」五级树，但实测生产库只有
level 1（单元，236 个）与 level 2（章节，1354 个），**level 3 恒为 0 条**。
后果不是"树不好看"，而是三处功能失效：

1. **AI 出题的候选知识点只能取 level<=2**。`question_agent` 里必须绕开
   `level==3` 过滤（否则候选恒空、模型只能凭空编造不存在的 id，落库触发外键
   约束失败，整批题目全军覆没）。这是 P0 事故的直接诱因。
2. **组卷的知识点范围粒度太粗**：选「一元二次方程」等于整章，无法只考
   「判别式」或「根与系数关系」。
3. **掌握度地图停在章节层**，看不出学生具体在哪个考点上失分。

## 播种策略（重要）

**只为本文件显式列出的 level2 章节补 level3**，不做「给 1354 个节点一律套
模板」的批量生成。理由：生产库 1354 个 level2 里只有 6 个挂了真实题目，
批量造出 4000+ 空节点会让知识点选择器彻底不可用，教师反而找不到东西。
本文件覆盖的是 `KNOWLEDGE_POINTS` 里有真实教研内容的 80 个章节，
每个补 2~4 个真实考点，合计约 250 个 level3。

幂等：以 `(grade_id, subject_id, parent_id, name)` 为准，已存在即跳过；
`code` 由 `G{年级}-L3-{父code后缀}-{序号}` 拼出，与现有命名保持一致。
"""
from typing import Dict, List, Tuple

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Grade, KnowledgePoint, Subject

# 结构：{年级: {学科: {level2 章节名: [(level3 考点名, 难度), ...]}}}
LEVEL3_POINTS: Dict[int, Dict[str, Dict[str, List[Tuple[str, str]]]]] = {
    1: {"数学": {
        "20以内加减法": [
            ("10以内加减法", "easy"), ("凑十法与破十法", "easy"), ("20以内进位加法", "medium"),
        ],
        "100以内加减法": [
            ("整十数加减法", "easy"), ("两位数加一位数进位", "medium"), ("连加连减", "medium"),
        ],
        "认识立体图形": [
            ("长方体与正方体特征", "easy"), ("圆柱与球特征", "easy"), ("图形分类与计数", "easy"),
        ],
        "认识钟表": [
            ("整时与半时", "easy"), ("时针分针位置", "easy"), ("经过时间计算", "medium"),
        ],
        "简单统计": [
            ("分类与整理", "easy"), ("象形统计图读取", "easy"), ("一格表示一个", "medium"),
        ],
    }},
    3: {
        "数学": {
            "万以内加减法": [
                ("三位数加减法", "medium"), ("连续进位与退位", "hard"), ("估算与验算", "medium"),
            ],
            "多位数乘一位数": [
                ("口算乘法", "easy"), ("笔算不进位乘法", "medium"), ("因数中间或末尾有0", "hard"),
            ],
            "分数初步认识": [
                ("认识几分之一", "easy"), ("认识几分之几", "medium"), ("同分母分数比较大小", "medium"),
            ],
            "长方形正方形面积": [
                ("面积单位认识", "easy"), ("长方形面积公式", "medium"), ("周长与面积区别", "hard"),
            ],
        },
        "语文": {
            "生字书写": [
                ("笔画笔顺规则", "easy"), ("形近字辨析", "medium"), ("偏旁部首归类", "easy"),
            ],
            "句子练习": [
                ("把字句与被字句互改", "medium"), ("扩句与缩句", "medium"), ("修改病句", "hard"),
            ],
            "阅读短文": [
                ("提取关键信息", "medium"), ("概括段落大意", "hard"), ("联系上下文理解词义", "medium"),
            ],
            "看图写话": [
                ("按顺序观察图画", "easy"), ("用完整句子表达", "medium"), ("写清时间地点人物", "medium"),
            ],
        },
    },
    5: {
        "数学": {
            "小数乘除法": [
                ("小数乘整数", "medium"), ("小数除以整数", "medium"), ("积与商的近似数", "hard"),
            ],
            "简易方程": [
                ("用字母表示数", "medium"), ("等式性质解方程", "medium"), ("列方程解应用题", "hard"),
            ],
            "多边形面积": [
                ("平行四边形面积", "medium"), ("三角形面积", "medium"), ("梯形面积", "hard"),
            ],
            "分数加减法": [
                ("同分母分数加减", "easy"), ("异分母分数加减", "hard"), ("分数加减混合运算", "hard"),
            ],
        },
        "语文": {
            "说明文阅读": [
                ("说明方法辨识", "medium"), ("说明顺序梳理", "hard"), ("提取说明对象特征", "medium"),
            ],
            "习作：写事": [
                ("事情经过写具体", "medium"), ("详略安排", "hard"), ("开头结尾呼应", "medium"),
            ],
            "文言文两则": [
                ("文言实词理解", "hard"), ("句子翻译", "hard"), ("寓意概括", "medium"),
            ],
        },
    },
    7: {
        "数学": {
            "有理数": [
                ("正负数与数轴", "easy"), ("相反数与绝对值", "easy"), ("有理数四则运算", "medium"),
            ],
            "整式的加减": [
                ("单项式与多项式", "easy"), ("同类项合并", "medium"), ("去括号法则", "medium"),
            ],
            "一元一次方程": [
                ("等式性质与移项", "medium"), ("去分母解方程", "hard"), ("列方程解应用题", "hard"),
            ],
            "平行线的性质": [
                ("同位角内错角同旁内角", "medium"), ("平行线判定", "medium"), ("平行线性质应用", "hard"),
            ],
            "三角形": [
                ("三边关系", "medium"), ("内角和与外角", "medium"), ("多边形内角和", "hard"),
            ],
            "二元一次方程组": [
                ("代入消元法", "medium"), ("加减消元法", "hard"), ("方程组实际应用", "hard"),
            ],
        },
        "语文": {
            "记叙文阅读": [
                ("记叙六要素", "easy"), ("人物形象分析", "hard"), ("景物描写作用", "medium"),
            ],
            "说明文阅读": [
                ("说明对象与特征", "medium"), ("常见说明方法", "medium"), ("说明语言准确性", "hard"),
            ],
            "文言文阅读": [
                ("通假字与古今异义", "hard"), ("句子翻译", "hard"), ("内容理解与启示", "medium"),
            ],
            "写作：记叙文": [
                ("选材与立意", "medium"), ("细节描写", "hard"), ("结构安排", "medium"),
            ],
        },
        "英语": {
            "一般现在时": [
                ("第三人称单数变化", "medium"), ("否定句与疑问句", "medium"), ("频度副词用法", "easy"),
            ],
            "一般过去时": [
                ("规则动词过去式", "medium"), ("不规则动词过去式", "hard"), ("过去时时间状语", "easy"),
            ],
            "there be 句型": [
                ("单复数be动词选择", "easy"), ("some与any用法", "medium"), ("就近原则", "hard"),
            ],
            "阅读理解": [
                ("细节理解题", "easy"), ("主旨大意题", "medium"), ("词义猜测题", "hard"),
            ],
        },
        # 七年级不开设物理（国家课程方案：物理自八年级起）。
        # `init_db.KNOWLEDGE_POINTS[7]["物理"]` 是历史遗留的错误数据，
        # 因 `sub_map.get((g.id, "物理"))` 取不到学科而从未真正落库
        # （实测 7 年级学科只有语文/数学/英语/生物/政治/历史/地理）。
        # 这里不为其补 level3，否则 just 制造一批父级不存在的孤儿配置。
    },
    8: {
        "数学": {
            "全等三角形": [
                ("全等判定SSS/SAS", "medium"), ("全等判定ASA/AAS", "medium"), ("HL判定", "hard"),
            ],
            "轴对称": [
                ("轴对称图形识别", "easy"), ("垂直平分线性质", "medium"), ("等腰三角形性质", "hard"),
            ],
            "一次函数": [
                ("函数图像与性质", "medium"), ("待定系数法求解析式", "medium"), ("一次函数与方程不等式", "hard"),
            ],
            "二次根式": [
                ("二次根式化简", "medium"), ("同类二次根式合并", "medium"), ("分母有理化", "hard"),
            ],
            "勾股定理": [
                ("勾股定理计算", "medium"), ("勾股定理逆定理", "medium"), ("实际问题建模", "hard"),
            ],
            "数据的分析": [
                ("平均数中位数众数", "easy"), ("方差与波动", "medium"), ("频数分布", "medium"),
            ],
        },
        "语文": {
            "文言文词类活用": [
                ("名词作动词", "hard"), ("使动与意动", "hard"), ("形容词作名词", "hard"),
            ],
            "现代文阅读理解": [
                ("句段作用分析", "medium"), ("表达方式辨析", "medium"), ("主题探究", "hard"),
            ],
            "议论文阅读": [
                ("论点与论据", "medium"), ("论证方法辨识", "medium"), ("论证结构梳理", "hard"),
            ],
            "写作：说明文": [
                ("说明顺序安排", "medium"), ("恰当使用说明方法", "hard"), ("语言准确简明", "medium"),
            ],
        },
        "英语": {
            "现在完成时": [
                ("have/has done构成", "medium"), ("already/yet/since/for", "hard"), ("与一般过去时区别", "hard"),
            ],
            "过去完成时": [
                ("had done构成", "medium"), ("过去的过去", "hard"), ("时间状语从句搭配", "hard"),
            ],
            "宾语从句": [
                ("连接词选择", "medium"), ("陈述语序", "hard"), ("时态呼应", "hard"),
            ],
            "完形填空": [
                ("上下文逻辑", "medium"), ("词义辨析", "hard"), ("固定搭配", "medium"),
            ],
        },
        "物理": {
            "机械能": [
                ("动能与势能", "medium"), ("机械能转化", "medium"), ("机械能守恒", "hard"),
            ],
            "电与电路": [
                ("电路连接与串并联", "medium"), ("电流表电压表使用", "medium"), ("短路断路判断", "hard"),
            ],
            "欧姆定律": [
                ("I=U/R计算", "medium"), ("伏安法测电阻", "hard"), ("动态电路分析", "hard"),
            ],
            "电功率": [
                ("电功率计算", "medium"), ("额定功率与实际功率", "hard"), ("焦耳定律", "hard"),
            ],
        },
    },
    9: {
        "数学": {
            "一元二次方程": [
                ("配方法与公式法", "medium"), ("因式分解法", "medium"), ("判别式与根的情况", "hard"),
                ("根与系数关系", "hard"),
            ],
            "二次函数": [
                ("图像与开口方向", "medium"), ("顶点式与对称轴", "medium"), ("最值与实际应用", "hard"),
            ],
            "旋转": [
                ("旋转性质", "medium"), ("中心对称图形", "medium"), ("坐标中的旋转", "hard"),
            ],
            "圆": [
                ("垂径定理", "medium"), ("圆周角定理", "hard"), ("切线的判定与性质", "hard"),
            ],
            "相似三角形": [
                ("相似判定定理", "medium"), ("相似比与面积比", "hard"), ("位似图形", "medium"),
            ],
            "锐角三角函数": [
                ("正弦余弦正切定义", "medium"), ("特殊角三角函数值", "medium"), ("解直角三角形应用", "hard"),
            ],
        },
        "语文": {
            "古诗文默写": [
                ("直接默写", "easy"), ("理解性默写", "hard"), ("易错字辨析", "medium"),
            ],
            "说明文阅读方法": [
                ("筛选整合信息", "medium"), ("说明方法及作用", "medium"), ("开放性探究", "hard"),
            ],
            "小说阅读": [
                ("情节梳理", "medium"), ("人物形象", "hard"), ("环境描写作用", "medium"),
            ],
            "写作：议论文": [
                ("论点提炼", "medium"), ("论据选择与论证", "hard"), ("结构安排", "medium"),
            ],
        },
        "英语": {
            "被动语态": [
                ("一般现在时被动", "medium"), ("一般过去时被动", "medium"), ("含情态动词被动", "hard"),
            ],
            "定语从句": [
                ("关系代词who/which/that", "medium"), ("关系副词when/where", "hard"), ("只能用that的情况", "hard"),
            ],
            "状语从句": [
                ("时间状语从句", "medium"), ("条件状语从句", "medium"), ("让步状语从句", "hard"),
            ],
            "书面表达": [
                ("要点齐全", "medium"), ("连接词使用", "medium"), ("句式多样与准确性", "hard"),
            ],
        },
        "物理": {
            "压强": [
                ("固体压强计算", "medium"), ("液体压强", "hard"), ("大气压强", "medium"),
            ],
            "浮力": [
                ("阿基米德原理", "hard"), ("浮沉条件", "hard"), ("浮力综合计算", "hard"),
            ],
            "功与机械能": [
                ("功的计算", "medium"), ("功率计算", "medium"), ("机械效率", "hard"),
            ],
            "电磁感应": [
                ("感应电流产生条件", "medium"), ("影响感应电流方向因素", "hard"), ("发电机原理", "medium"),
            ],
        },
        "化学": {
            "走进化学实验室": [
                ("常用仪器识别", "easy"), ("基本操作规范", "medium"), ("药品取用与加热", "medium"),
            ],
            "我们周围的空气": [
                ("空气成分及测定", "medium"), ("氧气性质", "medium"), ("空气污染与防治", "easy"),
            ],
            "物质构成的奥秘": [
                ("分子原子离子", "medium"), ("元素与元素符号", "medium"), ("化学式与化合价", "hard"),
            ],
            "化学方程式": [
                ("质量守恒定律", "medium"), ("方程式配平", "hard"), ("根据方程式计算", "hard"),
            ],
            "溶液": [
                ("溶解度与溶解度曲线", "hard"), ("溶质质量分数计算", "hard"), ("配制一定浓度溶液", "medium"),
            ],
        },
    },
}


def _parent_code_suffix(parent: KnowledgePoint) -> str:
    """子级编码片段。

    **不能用父 code 的末段**：level2 的 code 形如 `G1-S2-U2-K1`，末段是
    `K1`，不同单元下会重复（实测 U1-K1 与 U2-K1 在同一学科内撞码，
    触发 `uq_kp_subject_code` 唯一约束，整批插入失败）。
    改用父节点自增 id：全局唯一、稳定、重建库后仍可复现。
    """
    return f"P{parent.id}"


def seed_knowledge_level3(db: Session, *, dry_run: bool = False) -> Dict[str, int]:
    """为已存在的 level2 章节补 level3 考点。

    返回 `{"created": n, "skipped": n, "missing": n}`：
    - `missing` 统计「种子里有、库里找不到父章节」的数量——非 0 意味着
      生产数据与种子已漂移（章节被改名或删除），需要人工核对而不是自动补。
    """
    grades = {g.grade_num: g for g in db.scalars(select(Grade)).all()}
    subjects = db.scalars(select(Subject)).all()
    sub_map = {(s.grade_id, s.name): s for s in subjects}

    created = skipped = missing = 0
    for grade_num, subj_map3 in LEVEL3_POINTS.items():
        g = grades.get(grade_num)
        if not g:
            missing += sum(len(v) for v in subj_map3.values())
            continue
        for subj_name, chapter_map in subj_map3.items():
            s = sub_map.get((g.id, subj_name))
            if not s:
                missing += len(chapter_map)
                continue
            for chapter_name, points in chapter_map.items():
                parent = db.scalar(
                    select(KnowledgePoint).where(
                        KnowledgePoint.grade_id == g.id,
                        KnowledgePoint.subject_id == s.id,
                        KnowledgePoint.name == chapter_name,
                        KnowledgePoint.level == 2,
                    )
                )
                if not parent:
                    logger.warning(
                        f"level3 种子跳过：{g.name}{subj_name}「{chapter_name}」父章节不存在")
                    missing += len(points)
                    continue

                for idx, (point_name, difficulty) in enumerate(points, start=1):
                    exists = db.scalar(
                        select(KnowledgePoint.id).where(
                            KnowledgePoint.parent_id == parent.id,
                            KnowledgePoint.name == point_name,
                        )
                    )
                    if exists:
                        skipped += 1
                        continue
                    if dry_run:
                        created += 1
                        continue
                    node = KnowledgePoint(
                        name=point_name,
                        grade_id=g.id, subject_id=s.id,
                        level=3, parent_id=parent.id,
                        term=parent.term or 1,
                        difficulty=difficulty,
                        sort=idx,
                        code=f"G{grade_num}-L3-{_parent_code_suffix(parent)}-{idx}",
                        description=f"{chapter_name}「{point_name}」考点",
                        keywords=point_name,
                        status="published", source="seed",
                    )
                    db.add(node)
                    db.flush()
                    node.path = f"{parent.path}/{node.id}" if parent.path else str(node.id)
                    created += 1

    if created and not dry_run:
        db.commit()
    logger.info(
        f"知识点 level3 播种完成：新增 {created}，已存在 {skipped}，父级缺失 {missing}")
    return {"created": created, "skipped": skipped, "missing": missing}
