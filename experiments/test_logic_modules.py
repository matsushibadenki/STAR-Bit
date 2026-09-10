import unittest

import numpy as np

from logic_modules import cut, evaluate, expand, live_library, schedule, signature


class LogicModuleTests(unittest.TestCase):
    def test_equivalence_is_functional_not_syntactic(self):
        a = ('XOR', 'p0', 'p1')
        b = ('AND', ('OR', 'p0', 'p1'), ('NOT', ('AND', 'p0', 'p1')))
        self.assertEqual(signature(a, 2, {}), signature(b, 2, {}))
        self.assertNotEqual(a, b)

    def test_module_expansion_preserves_all_inputs(self):
        pattern = ('XOR', ('AND', 'p0', 'p1'), 'p2')
        library = {'M0': {'pattern': pattern, 'table': signature(pattern, 3, {})}}
        expr = ('M0', 'x0', 'x1', 'x2')
        inputs = {f'x{i}': ((np.arange(8)>>i)&1).astype(bool) for i in range(3)}
        np.testing.assert_array_equal(evaluate(expr, inputs, library), evaluate(expand(expr, library), inputs, {}))
        self.assertEqual(live_library([('XOR', 'x0', 'x1')], library), {})

    def test_cse_requires_same_operands(self):
        common = ('AND', 'x0', 'x1')
        same = ('XOR', common, common)
        distinct = ('XOR', common, ('AND', 'x2', 'x3'))
        self.assertEqual(schedule([same], 16)['primitive_operations'], 2)
        self.assertEqual(schedule([distinct], 16)['primitive_operations'], 3)
        self.assertEqual(schedule([distinct], 1)['cycles'], 3)
        self.assertEqual(schedule([distinct], 16)['cycles'], 2)

    def test_cut_retains_repeated_boundary_identity(self):
        p, ports = cut(('XOR', ('AND', 'x0', 'x1'), ('AND', 'x0', 'x1')))
        self.assertEqual(len(ports), 2)
        self.assertEqual(signature(p, 2, {}), (0,0,0,0))


if __name__ == '__main__': unittest.main()
