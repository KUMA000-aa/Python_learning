"""演示数据填充：课程 / 单元 / 关卡 / 题目。

运行：python -m app.seed
多次运行会先清空旧的演示数据再插入，方便反复调试。
"""
import json

from app.core.database import Base, SessionLocal, engine
from app import models  # noqa: F401  触发模型注册
from app.models.course import Course, Level, Unit
from app.models.question import Question


# ===== 题目构造小工具 =====
# 题型约定：
#   single_choice 单选：options 为选项文本列表，correct_answer 为选项字母（A/B/C/D）
#   true_false    判断：options 固定 ["正确", "错误"]，correct_answer 为 "A"（正确）或 "B"（错误）
#   fill_blank    填空：options 为空列表，correct_answer 为标准答案文本（可用 | 分隔多个可接受写法）
#   code_fill     代码补全：options 为空列表，题干中用 ___ 表示空位，
#                 correct_answer 为按空位先后顺序排列的答案 JSON 数组
def _mcq(stem: str, options: list[str], answer: str, explanation: str) -> dict:
    return {
        "question_type": "single_choice",
        "stem": stem,
        "options": options,
        "correct_answer": answer,
        "explanation": explanation,
    }


def _tf(stem: str, is_true: bool, explanation: str) -> dict:
    return {
        "question_type": "true_false",
        "stem": stem,
        "options": ["正确", "错误"],
        "correct_answer": "A" if is_true else "B",
        "explanation": explanation,
    }


def _fill(stem: str, answer: str, explanation: str) -> dict:
    return {
        "question_type": "fill_blank",
        "stem": stem,
        "options": [],
        "correct_answer": answer,
        "explanation": explanation,
    }


def _code(stem: str, answers: list[str], explanation: str) -> dict:
    return {
        "question_type": "code_fill",
        "stem": stem,
        "options": [],
        "correct_answer": json.dumps(answers, ensure_ascii=False),
        "explanation": explanation,
    }


# ============================================================
# CH1-Python基础 / 作业：Python入门之基础语法
# ============================================================

# 关卡 1：行与缩进
CH1_L1 = [
    _mcq(
        "Python 中用来表示代码块层级的是？",
        ["大括号 {}", "缩进", "begin/end", "圆括号 ()"],
        "B",
        "Python 用缩进划分代码块，而不是大括号。",
    ),
    _mcq(
        "同一个代码块内的多条语句，缩进应该？",
        ["随意即可", "保持完全一致", "必须都是 4 个空格", "必须都用 Tab"],
        "B",
        "同一代码块缩进必须一致，否则会 IndentationError；不强制 4 空格或 Tab。",
    ),
    _tf(
        "Python 通过缩进划分代码块，缩进不一致会引发 IndentationError。",
        True,
        "缩进是语法的一部分，同一代码块缩进要统一。",
    ),
    _tf(
        "Python 一行只能写一条语句，不能用分号分隔。",
        False,
        "可以用分号在同一行写多条简单语句。",
    ),
    _fill(
        "把多条语句写在同一行时，语句之间用 ______ 分隔。",
        ";|；",
        "分号可把多条简单语句写在一行。",
    ),
    _code(
        "补全代码，让同一行用分号分隔的两条赋值语句成立：\n"
        "x = 1; ___ = 2\n"
        "print(x + y)",
        ["y"],
        "分号分隔同一行多条语句，第二条给 y 赋值。",
    ),
]

# 关卡 2：标识符与保留字
CH1_L2 = [
    _mcq(
        "下列哪个是合法的 Python 标识符？",
        ["2name", "_name", "my-name", "class"],
        "B",
        "标识符首字符必须是字母或下划线，且不能是保留字 class。",
    ),
    _mcq(
        "Python 标识符区分大小写，Name 和 name 是？",
        ["同一个变量", "两个不同的变量", "语法错误", "保留字"],
        "B",
        "Python 标识符区分大小写，二者是不同标识符。",
    ),
    _tf(
        "标识符可以以数字开头，例如 1abc 是合法的。",
        False,
        "标识符不能以数字开头。",
    ),
    _tf(
        "class、if、for 都是 Python 保留字，不能用作变量名。",
        True,
        "保留字不能作为标识符使用。",
    ),
    _fill(
        "查看 Python 全部保留字，可用 keyword.______ 获取列表。",
        "kwlist",
        "import keyword 后 keyword.kwlist 返回全部保留字。",
    ),
    _code(
        "补全代码，打印 Python 保留字的数量：\n"
        "import keyword\n"
        "print(len(keyword.___))",
        ["kwlist"],
        "keyword.kwlist 是保留字列表，len 得到数量（33 个）。",
    ),
]

# 关卡 3：注释
CH1_L3 = [
    _mcq(
        "Python 单行注释使用哪个符号？",
        ["//", "#", "/* */", "--"],
        "B",
        "Python 单行注释以 # 开头。",
    ),
    _mcq(
        "下列哪种不是 Python 的多行注释写法？",
        ["连续多个 #", "三个单引号包裹", "三个双引号包裹", "/* ... */"],
        "D",
        "/* */ 是 C/Java 的注释，Python 不支持。",
    ),
    _tf(
        "注释会被解释器执行，所以注释越多运行越慢。",
        False,
        "注释不会被执行，对运行速度没有影响。",
    ),
    _tf(
        "三个双引号包裹的内容可以作为多行注释使用。",
        True,
        "三引号字符串常被用作多行注释。",
    ),
    _fill(
        "Python 中单行注释以 ______ 开头。",
        "#",
        "# 之后到行尾都是注释。",
    ),
    _code(
        "补全注释符号，使这一行成为注释：\n"
        "a = 5\n"
        "___ 输出结果\n"
        "print(a)",
        ["#"],
        "# 开头表示注释，单独的 print(a) 会输出 5。",
    ),
]

# 关卡 4：输入输出
CH1_L4 = [
    _mcq(
        "input() 返回的数据类型是？",
        ["int", "str", "float", "由输入内容决定"],
        "B",
        "input() 始终返回字符串，数字需 int()/float() 转换。",
    ),
    _mcq(
        '表达式 "100 / 200 = %f" % (100 / 200) 的输出是？',
        ["100 / 200 = 0.5", "100 / 200 = 0.500000", "100 / 200 = 0.5000", "报错"],
        "B",
        "%f 默认保留 6 位小数。",
    ),
    _tf(
        'print("a", "b", sep="-") 会输出 a-b。',
        True,
        "sep 参数指定多个输出之间的分隔符。",
    ),
    _tf(
        'input() 读到的 "18" 可以直接参与加法运算。',
        False,
        "input 返回字符串，需先 int() 转换。",
    ),
    _fill(
        'print("a", end=______) 可以让后续输出接在同一行（填一个空字符串）。',
        '""',
        "end 设为空字符串则不换行。",
    ),
    _code(
        "补全运算符，读入两个整数并输出它们的和：\n"
        "a = int(input())\n"
        "b = int(input())\n"
        "print(a ___ b)",
        ["+"],
        "input 转 int 后用 + 求和。",
    ),
]


# ============================================================
# CH2-Python序列之列表 / 作业：玩转列表
# ============================================================

# 关卡 1：列表元素的增删改
CH2_L1 = [
    _mcq(
        "在列表末尾追加一个元素，应使用哪个方法？",
        ["add()", "append()", "insert()", "push()"],
        "B",
        "append 在末尾追加；insert 是指定位置插入。",
    ),
    _mcq(
        "删除指定索引的元素并返回它，应使用？",
        ["remove()", "del 语句", "pop()", "clear()"],
        "C",
        "pop(index) 删除并返回该元素，默认删末尾。",
    ),
    _tf(
        "remove(obj) 会删除列表中所有等于 obj 的元素。",
        False,
        "remove 只删除最前面一个匹配元素。",
    ),
    _tf(
        'insert(2, "x") 会把 "x" 插入到索引 2 的位置。',
        True,
        "insert(index, obj) 在指定索引处插入。",
    ),
    _fill(
        'guests = ["a", "b"]，执行 guests.______("c") 后变为 ["a", "b", "c"]。',
        "append",
        "append 在列表末尾追加元素。",
    ),
    _code(
        '补全代码：弹出末尾元素并插入到索引 1：\n'
        'guests = ["Tom", "Jerry", "Spike"]\n'
        "deleted = guests.___()\n"
        "guests.insert(1, deleted)\n"
        "print(guests)",
        ["pop"],
        "pop 默认删除并返回末尾元素，再 insert 到索引 1。",
    ),
]

# 关卡 2：列表元素的排序
CH2_L2 = [
    _mcq(
        "对列表就地升序排序，应使用？",
        ["list.sort()", "sorted()", "reverse()", "order()"],
        "A",
        "list.sort() 原地升序排序。",
    ),
    _mcq(
        "对列表就地降序排序，应写成？",
        ["list.sort()", "list.sort(reverse=True)", "list.reverse()", "list.sort(True)"],
        "B",
        "sort(reverse=True) 实现降序。",
    ),
    _tf(
        "sort() 会返回一个新的排好序的列表，原列表不变。",
        False,
        "sort() 原地修改列表并返回 None。",
    ),
    _tf(
        "list.reverse() 与 list.sort(reverse=True) 效果相同。",
        False,
        "reverse() 只是把顺序倒过来，并不排序。",
    ),
    _fill(
        "nums = [3, 1, 2]，执行 nums.sort(reverse=______) 可降序排列。",
        "True",
        "reverse=True 表示降序。",
    ),
    _code(
        '补全方法名，使客人名单按首字母升序：\n'
        'guests = ["Cindy", "Alice", "Bob"]\n'
        "guests.___()\n"
        "print(guests)",
        ["sort"],
        "sort() 默认升序、原地修改。",
    ),
]

# 关卡 3：数值列表
CH2_L3 = [
    _mcq(
        "list(range(1, 5)) 的结果是？",
        ["[1, 2, 3, 4, 5]", "[1, 2, 3, 4]", "[0, 1, 2, 3, 4]", "[1, 5]"],
        "B",
        "range 左闭右开，不含 5。",
    ),
    _mcq(
        "求列表 nums 中最大值，应使用？",
        ["max(nums)", "min(nums)", "sum(nums)", "len(nums)"],
        "A",
        "max 求最大值。",
    ),
    _tf(
        "range(0, 10, 2) 生成的数字包含 10。",
        False,
        "range 右端不包含，最大到 8。",
    ),
    _tf(
        "range() 的参数可以是小数，如 range(0, 1, 0.5)。",
        False,
        "range 的参数只能是整数。",
    ),
    _fill(
        "nums = [4, 8, 2]，______(nums) 可得到元素个数 3。",
        "len",
        "len(nums) 返回列表长度。",
    ),
    _code(
        "补全函数，计算最大值与最小值之差：\n"
        "nums = list(range(1, 6))\n"
        "result = max(nums) - ___(nums)\n"
        "print(result)",
        ["min"],
        "max - min = 5 - 1 = 4。",
    ),
]

# 关卡 4：列表切片
CH2_L4 = [
    _mcq(
        "[1, 2, 3, 4, 5][1:3] 的结果是？",
        ["[1, 2, 3]", "[2, 3]", "[2, 3, 4]", "[1, 2]"],
        "B",
        "切片含头不含尾，取索引 1、2。",
    ),
    _mcq(
        "取列表最后 3 个元素，应写成？",
        ["list[:3]", "list[-3:]", "list[3:]", "list[-3:-1]"],
        "B",
        "负数索引 -3: 表示最后 3 个。",
    ),
    _tf(
        "切片 list[start:end] 会包含索引 end 对应的元素。",
        False,
        "切片不包含 end。",
    ),
    _tf(
        "list[::2] 表示从头到尾每隔一个取一个。",
        True,
        "步长为 2 即隔一个取一个。",
    ),
    _fill(
        "my_list = [0, 1, 2, 3, 4]，my_list[1:4:2] 的结果是 ______。",
        "[1, 3]",
        "从索引 1 到 3（不含 4），步长 2，取到 1、3。",
    ),
    _code(
        "补全切片，取列表最后 3 个元素：\n"
        'my_menu = ["a", "b", "c", "d", "e", "f"]\n'
        "result = my_menu[___]\n"
        "print(result)",
        ["-3:"],
        "负数索引 -3: 取最后 3 个元素。",
    ),
]


# ============================================================
# CH4-Python控制结构与字符串 / 作业：字符串处理
# ============================================================

# 关卡 1：字符串的拼接：名字的组成
CH4_L1 = [
    _mcq(
        "把字符串 first 和 last 用空格连接成一个完整字符串，下列写法正确的是？",
        ['first + last', 'first + " " + last', 'first, " ", last', 'first & " " & last'],
        "B",
        "字符串用 + 拼接，空格本身也要作为字符串显式拼进去；逗号是 print 的分隔符，不会生成新字符串。",
    ),
    _mcq(
        'print("Hello", "World") 的输出是？',
        ["HelloWorld", "Hello World", "Hello,World", "报错"],
        "B",
        "print 用逗号分隔多个参数时，默认以空格作为分隔符。",
    ),
    _tf(
        "input() 读到的内容始终是字符串（str），即使输入的是数字。",
        True,
        "input() 的返回值一定是 str，要做算术运算需要 int() 或 float() 转换。",
    ),
    _tf(
        '表达式 "年龄：" + 18 可以正常拼接出 "年龄：18"。',
        False,
        "字符串不能直接和整数用 + 拼接，会抛 TypeError，需要先 str(18) 转换。",
    ),
    _fill(
        'f-string 中想把变量 name 插入到「你好，」后面，写法是 f"你好，______"（只填花括号部分）。',
        "{name}",
        "f-string 里用 {变量名} 占位，运行时替换成变量值。",
    ),
    _fill(
        "print 的 ______ 参数用于指定多个输出之间的分隔符，默认是一个空格。",
        "sep",
        "print(..., sep='分隔符') 可以自定义多参数之间的分隔符。",
    ),
    _code(
        "补全代码，把 first_name 和 last_name 用空格拼接成 full_name 并打印：\n"
        "first_name = input()\n"
        "last_name = input()\n"
        'full_name = ___ + " " + ___\n'
        "print(full_name)",
        ["first_name", "last_name"],
        "full_name 由 first_name、一个空格和 last_name 用 + 依次拼接得到。",
    ),
]

# 关卡 2：字符转换
CH4_L2 = [
    _mcq(
        '表达式 len("Hello World") 的结果是？',
        ["10", "11", "12", "9"],
        "B",
        "len() 统计字符个数，中间的空格也算 1 个字符，共 11 个。",
    ),
    _mcq(
        '把 "hello world" 变成 "Hello World"，应调用哪个方法？',
        ["upper()", "lower()", "title()", "capitalize()"],
        "C",
        "title() 会把每个单词的首字母大写；upper() 全部大写，capitalize() 只大写首字母。",
    ),
    _tf(
        "调用 s.upper() 会直接修改原字符串 s。",
        False,
        "字符串不可变，upper() 返回新字符串，原字符串不变。",
    ),
    _tf(
        "strip() 默认会去掉字符串首尾的空白字符（空格、换行、制表符等）。",
        True,
        "strip() 不带参数时去掉首尾所有空白字符。",
    ),
    _fill(
        '表达式 "  hi  ".strip() 的结果是（不含引号）______。',
        "hi",
        "strip() 去掉首尾空格后剩下 hi。",
    ),
    _fill(
        "要获取字符串 s 的长度，应使用内置函数 ______(s)。",
        "len",
        "len(s) 返回字符串的字符个数。",
    ),
    _code(
        "补全代码：先去掉 s 首尾空白，再把每个单词首字母大写，最后打印长度：\n"
        's = "  hello world  "\n'
        "s = s.strip()\n"
        "s = s.___()\n"
        "print(___(s))",
        ["title", "len"],
        "strip 去首尾空白 → title 每个单词首字母大写 → len 求长度。",
    ),
]

# 关卡 3：字符串查找与替换
CH4_L3 = [
    _mcq(
        '表达式 "abcdef".find("cd") 的结果是？',
        ["1", "2", "3", "-1"],
        "B",
        "find() 返回子串首次出现的最左索引且从 0 开始，c 在下标 2。",
    ),
    _mcq(
        "若子串不存在，str.find() 会返回什么？",
        ["0", "None", "-1", "报错"],
        "C",
        "find() 找不到时返回 -1，不会报错。",
    ),
    _tf(
        "replace(old, new) 会直接修改原字符串。",
        False,
        "replace() 返回替换后的新字符串，原字符串不可变。",
    ),
    _tf(
        '"a b  c".split() 会按任意空白切分，得到 [\'a\', \'b\', \'c\']。',
        True,
        "split() 不传分隔符时，会按连续空白切分并忽略多余空白。",
    ),
    _fill(
        '表达式 "hello".replace("l", "L") 的结果是（不含引号）______。',
        "heLLo",
        "两个小写 l 都被替换成大写 L，得到 heLLo。",
    ),
    _fill(
        '表达式 "a,b,c".split(",") 的结果是 ______。',
        "['a', 'b', 'c']",
        "按逗号切分，得到三个元素的列表 ['a', 'b', 'c']。",
    ),
    _code(
        "补全代码，查找 day 第一次出现的位置：\n"
        'sentence = "one day at a time"\n'
        'pos = sentence.___("day")\n'
        "print(pos)",
        ["find"],
        "find 返回子串最左首次出现的索引。",
    ),
]


# ===== 课程结构 =====
COURSE = {"title": "Python 程序设计", "description": "按头歌课程整理的练习题库"}

UNITS = [
    {
        "title": "CH1-Python基础",
        "description": "缩进、标识符与保留字、注释、输入输出",
        "levels": [
            {"title": "行与缩进", "questions": CH1_L1},
            {"title": "标识符与保留字", "questions": CH1_L2},
            {"title": "注释", "questions": CH1_L3},
            {"title": "输入输出", "questions": CH1_L4},
        ],
    },
    {
        "title": "CH2-Python序列之列表",
        "description": "列表增删改、排序、数值列表、切片",
        "levels": [
            {"title": "列表元素的增删改", "questions": CH2_L1},
            {"title": "列表元素的排序", "questions": CH2_L2},
            {"title": "数值列表：用数字说话", "questions": CH2_L3},
            {"title": "列表切片", "questions": CH2_L4},
        ],
    },
    {
        "title": "CH4-Python控制结构与字符串",
        "description": "字符串拼接、字符转换、查找与替换",
        "levels": [
            {"title": "字符串的拼接：名字的组成", "questions": CH4_L1},
            {"title": "字符转换", "questions": CH4_L2},
            {"title": "字符串查找与替换", "questions": CH4_L3},
        ],
    },
]


def _add_questions(db, level: Level, questions: list[dict]) -> None:
    """把某关卡的题目按顺序写入数据库。"""
    for idx, q in enumerate(questions):
        db.add(
            Question(
                level_id=level.id,
                question_type=q["question_type"],
                stem=q["stem"],
                options=json.dumps(q["options"], ensure_ascii=False),
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                order_index=idx,
            )
        )


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 清空旧的演示数据（顺序：题目 → 关卡 → 单元 → 课程）
    db.query(Question).delete()
    db.query(Level).delete()
    db.query(Unit).delete()
    db.query(Course).delete()
    db.commit()

    course = Course(title=COURSE["title"], description=COURSE["description"], order_index=0)
    db.add(course)
    db.flush()

    total_levels = 0
    total_questions = 0
    for unit_idx, unit_data in enumerate(UNITS):
        unit = Unit(
            course_id=course.id,
            title=unit_data["title"],
            description=unit_data["description"],
            order_index=unit_idx,
        )
        db.add(unit)
        db.flush()

        for level_idx, level_data in enumerate(unit_data["levels"]):
            level = Level(unit_id=unit.id, title=level_data["title"], order_index=level_idx)
            db.add(level)
            db.flush()
            _add_questions(db, level, level_data["questions"])
            total_levels += 1
            total_questions += len(level_data["questions"])

    db.commit()
    print(
        f"演示数据已填充：1 课程 / {len(UNITS)} 单元 / "
        f"{total_levels} 关卡 / {total_questions} 题"
    )
    db.close()


if __name__ == "__main__":
    seed()
