from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QFrame, QHBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from controllers.report_controller import ReportController

class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)

        # ======= TITLE =======
        title = QLabel("📊 Sales Dashboard")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # ======= SUMMARY CARDS =======
        summary = ReportController.get_sales_summary()
        card_layout = QHBoxLayout()
        card_layout.setSpacing(15)

        for label, value, emoji in [
            ("Today", summary['today'], "💵"),
            ("This Week", summary['week'], "📅"),
            ("This Month", summary['month'], "📈"),
        ]:
            card = self._create_card(f"{emoji} {label}", f"{value} DA")
            card_layout.addWidget(card)

        main_layout.addLayout(card_layout)

        # ======= TOP PRODUCTS =======
        top_label = QLabel("🥇 Top Selling Products")
        top_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        main_layout.addWidget(top_label)

        top_products = ReportController.get_top_products()
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Product", "Quantity Sold"])
        table.setRowCount(len(top_products))
        table.horizontalHeader().setStretchLastSection(True)

        for i, item in enumerate(top_products):
            table.setItem(i, 0, QTableWidgetItem(item["name"]))
            table.setItem(i, 1, QTableWidgetItem(str(item["qty"])))
        main_layout.addWidget(table)

        # ======= CHART =======
        trend_label = QLabel("📉 Sales Trend (Last 7 Days)")
        trend_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        main_layout.addWidget(trend_label)

        trend = ReportController.get_sales_trend(7)
        if trend:
            fig = Figure(figsize=(6, 3))
            ax = fig.add_subplot(111)
            ax.plot(
                [t["date"] for t in trend],
                [t["total"] for t in trend],
                marker='o',
                linewidth=2,
                color="#0984e3"
            )
            ax.set_xlabel("Date")
            ax.set_ylabel("Total (DA)")
            ax.grid(True, linestyle='--', alpha=0.4)
            canvas = FigureCanvasQTAgg(fig)
            main_layout.addWidget(canvas)

        # ======= STYLE =======
        self.setStyleSheet("""
            QLabel {
                color: #2d3436;
            }
            QFrame#card {
                background: white;
                border-radius: 12px;
                padding: 15px;
                border: 1px solid #dcdde1;
            }
            QTableWidget {
                background: white;
                border: 1px solid #dcdde1;
                border-radius: 10px;
                gridline-color: #dcdde1;
            }
        """)

    def _create_card(self, title, value):
        """Create a summary card"""
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 14px; color: #636e72;")
        lbl_value = QLabel(value)
        lbl_value.setStyleSheet("font-weight: bold; font-size: 18px; color: #2d3436;")
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        return card
