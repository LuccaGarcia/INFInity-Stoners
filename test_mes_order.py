import unittest
from mes_order import MesOrder

class TestMesOrder(unittest.TestCase):
    def setUp(self):
        self.order = MesOrder()

    def test_get_order(self):
        self.assertEqual(self.order.get_order(), 0)

    def test_set_order(self):
        self.order.set_order(123)
        self.assertEqual(self.order.get_order(), 123)

    def test_get_work_piece(self):
        self.assertEqual(self.order.get_work_piece(), "")

    def test_set_work_piece(self):
        self.order.set_work_piece("Work Piece 1")
        self.assertEqual(self.order.get_work_piece(), "Work Piece 1")

    def test_get_quantity(self):
        self.assertEqual(self.order.get_quantity(), 0)

    def test_set_quantity(self):
        self.order.set_quantity(10)
        self.assertEqual(self.order.get_quantity(), 10)

    def test_get_due_date(self):
        self.assertEqual(self.order.get_due_date(), 0)

    def test_set_due_date(self):
        self.order.set_due_date("2022-01-01")
        self.assertEqual(self.order.get_due_date(), "2022-01-01")

if __name__ == '__main__':
    unittest.main()