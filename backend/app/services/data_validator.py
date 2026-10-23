"""数据校验：检查实验数据是否满足物理约束。

第 5 步实现（这一处由你自己写）。校验项：
    KCL：流入节点的电流之和 = 0（考虑正负号）
    KVL：闭合回路的电压代数和 = 0
"""


class DataValidator:
    """实验数据校验器。"""

    def check_kcl(self, currents: dict[str, float]) -> list[str]:
        """返回问题描述列表，空列表表示通过。"""
        raise NotImplementedError("第 5 步由你实现")

    def check_kvl(self, voltages: dict[str, float]) -> list[str]:
        """返回问题描述列表，空列表表示通过。"""
        raise NotImplementedError("第 5 步由你实现")
