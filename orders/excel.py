import openpyxl
from openpyxl import Workbook
from openpyxl.styles.borders import Border, Side
from openpyxl.styles.fills import PatternFill
from openpyxl.styles import Alignment
from openpyxl.styles import Font

from orders.models import Product, ProductType, Order


class ExcelDailyReport:

    def __init__(self, name, date):
        self.wb = openpyxl.load_workbook(name)
        self.ws = self.wb.worksheets[0]
        self.date = date

        self.cells_indexes = {
            "ФИО": 1,
            "УНП": 2,
            "000000039": 3,
            "000000036": 5,
            "000000280": 7,
            "000000038": 9,
            "000000397": 11,
            "000000399": 13,
            "000000245": 15,
            "000000246": 17,
            "000000259": 19,
            "Итого": 22,
            "Пункт разгрузки и примечание": 23,
        }
        self.formula_fields = [3, 5, 7, 9, 11, 13, 15, 17, 19, 22]

        self._create_styles()
        self._fill_in_orders()

        for col in self.ws.iter_cols():
            for cell in col:
                cell.border = self.thin_border

    def _create_styles(self):
        self.medium_border = Border(left=Side(style='medium'), right=Side(style='medium'), top=Side(style='medium'),
                               bottom=Side(style='medium'))
        self.thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'),
                                    bottom=Side(style='thin'))

        self.fillers = [
            PatternFill(patternType="solid", fgColor="00FFCC99"),
            PatternFill(patternType="solid", fgColor="0099CCFF"),
            PatternFill(patternType="solid", fgColor="00CCFFCC")
        ]

        self.product_type_bg = {
            prod_type: self.fillers[i] for i, prod_type in enumerate(ProductType.objects.all()[:3])
        }

        self.title_font = Font(name="Arial", size=10, bold=True)
        self.count_font = Font(name="Arial", size=9, bold=True)
        self.price_font = Font(name="Arial", size=9, italic=True)
        self.default_font = Font(name="Arial", size=9)

        self.center_alignment = Alignment(horizontal='center')

    def _get_order_row(self, order, row_index):
        row = dict()
        row["ФИО"] = order.owner.fio
        row["УНП"] = order.owner.unp

        if order.point:
            row["Пункт разгрузки и примечание"] = order.point.address
        else:
            row["Пункт разгрузки и примечание"] = "Самовывоз"

        ordered_products = set()
        for item in order.items.all():
            count = item.count
            price = item.price

            row[item.product] = (count, round(price / count, 2))
            ordered_products.add(item.product)

        for product in set(Product.objects.all()).difference(ordered_products):
            special_price = product.get_special_price_for_user(order.owner)
            if special_price:
                row[product] = (None, special_price.price)
            else:
                row[product] = (None, product.price)

        # Итоги по строке
        sum_fields = []
        for col_num in self.formula_fields[:-1]:
            col_letter = self.ws.cell(1, col_num).column_letter
            sum_fields.append(f"{col_letter}{row_index}")
        row["Итого"] = f"={'+'.join(sum_fields)}"

        return row

    def _fill_in_orders(self):

        self.orders = Order.objects.filter(created_at__date=self.date)

        row_index = 2
        for order in self.orders:
            row = self._get_order_row(order, row_index)
            for col, value in row.items():

                if isinstance(col, Product):
                    code = col.excel_code
                    count_cell = self.ws.cell(row_index, self.cells_indexes[code], value[0])
                    price_cell = self.ws.cell(row_index, self.cells_indexes[code] + 1, value[1])
                    count_cell.font = self.count_font
                    count_cell.alignment = self.center_alignment
                    price_cell.font = self.price_font
                    price_cell.alignment = self.center_alignment
                else:
                    cell = self.ws.cell(row_index, self.cells_indexes[col], value)
                    if col == "Итого":
                        cell.font = self.title_font
                        cell.alignment = self.center_alignment
                    else:
                        cell.font = self.default_font

            row_index += 1

        # Итого внизу таблицы
        self.ws.cell(row_index + 1, 1, "ИТОГО:")
        for col_num in self.formula_fields:
            col_letter = self.ws.cell(1, col_num).column_letter

            cell = self.ws.cell(row_index + 1, col_num, f"=SUM({col_letter}1:{col_letter}{row_index})")
            cell.font = self.title_font
            cell.alignment = self.center_alignment


