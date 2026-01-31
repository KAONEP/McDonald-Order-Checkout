# src/rules.py

# 类别 key 统一使用：
# burger, fries, drink, nuggets, sauce

DEPENDENCIES = {
    # 订单里有 nuggets，就必须有 sauce
    "nuggets": {"sauce": 1}
}

RULE_DESCRIPTIONS = {
    "nuggets": "麦乐鸡块必须附带酱"
}
