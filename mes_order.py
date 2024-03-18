import xml.etree.ElementTree as ET
import psycopg2
from dotenv import load_dotenv
import os

class MesOrder:
    def __init__(self):
        self.order = 0
        self.work_piece = ""
        self.quantity = 0
        self.due_date = 0

    def get_order(self):
        return self.order

    def set_order(self, order):
        self.order = order

    def get_work_piece(self):
        return self.work_piece

    def set_work_piece(self, work_piece):
        self.work_piece = work_piece

    def get_quantity(self):
        return self.quantity

    def set_quantity(self, quantity):
        self.quantity = quantity

    def get_due_date(self):
        return self.due_date

    def set_due_date(self, due_date):
        self.due_date = due_date
   
           











