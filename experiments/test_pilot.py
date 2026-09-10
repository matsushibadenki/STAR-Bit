import unittest

import torch

from pilot import Model, comparison, data


class MechanismTests(unittest.TestCase):
    def test_learned_router_gradient_and_load_normalization(self):
        torch.manual_seed(8)
        model = Model('ternary_learned')
        x, y, _ = data(81, 128, 'selection')
        pred, aux, route = model(x)
        (torch.nn.functional.mse_loss(pred, y) + .01 * aux).backward()
        self.assertGreater(model.router.weight.grad.abs().sum().item(), 0)
        self.assertEqual(route[0].shape, (128, 2))
        self.assertTrue((route[0][:, 0] != route[0][:, 1]).all())

    def test_fixed_routes_stay_fixed_after_expert_training(self):
        torch.manual_seed(2)
        model = Model('ternary_fixed')
        x, y, _ = data(12, 128, 'selection')
        pred, _, route = model(x)
        before = route[0].clone()
        opt = torch.optim.Adam(model.parameters(), lr=.01)
        torch.nn.functional.mse_loss(pred, y).backward()
        opt.step()
        self.assertTrue(torch.equal(before, model(x)[2][0]))
        self.assertIsNone(model.router.weight.grad)

    def test_parameter_budgets_include_router(self):
        for condition, total in [('ternary_dense', 505), ('ternary_wide', 953), ('ternary_learned', 952)]:
            self.assertEqual(sum(p.numel() for p in Model(condition).parameters()), total)

    def test_exact_signflip_resolution(self):
        self.assertEqual(comparison([1.] * 8)['p_signflip_two_sided'], 2 / 256)
        self.assertEqual(comparison([0.] * 8)['p_signflip_two_sided'], 1.)


if __name__ == '__main__':
    unittest.main()
