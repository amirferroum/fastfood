from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QScrollArea,
    QTableWidget, QTableWidgetItem, QDateEdit, QFileDialog, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QBarSet, QBarSeries, QBarCategoryAxis
from PyQt6.QtGui import QPainter, QFont
from datetime import datetime, timedelta
from models.database import get_connection
import csv


class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reports & Statistics")
        self.resize(1100, 750)

        # === Scrollable main layout ===
        main_layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(25, 25, 25, 25)
        scroll_layout.setSpacing(25)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # === Title ===
        title = QLabel("📊 Sales & Performance Reports")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333;
                margin-bottom: 15px;
            }
        """)
        scroll_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        # === Filter section ===
        filter_card = QWidget()
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setSpacing(10)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        filter_card.setStyleSheet("""
            QWidget {
                background: #ffffff;
                border: 1px solid #ddd;
                border-radius: 12px;
            }
        """)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Time", "Today", "This Week", "Custom Range"])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())

        self.apply_btn = QPushButton("🔍 Apply")
        self.apply_btn.clicked.connect(self.apply_filter)
        self.apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                padding: 6px 14px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #006CBE;
            }
        """)

        filter_layout.addWidget(QLabel("Filter:"))
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addWidget(QLabel("From:"))
        filter_layout.addWidget(self.start_date)
        filter_layout.addWidget(QLabel("To:"))
        filter_layout.addWidget(self.end_date)
        filter_layout.addWidget(self.apply_btn)
        scroll_layout.addWidget(filter_card)

        # === Summary card ===
        self.summary_label = QLabel("Loading summary...")
        self.summary_label.setStyleSheet("""
            QLabel {
                background: #f1f8ff;
                border: 1px solid #cce5ff;
                border-radius: 12px;
                padding: 15px;
                font-size: 16px;
                color: #004085;
            }
        """)
        scroll_layout.addWidget(self.summary_label)

        # === Chart: Sales Overview ===
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumHeight(400)
        self.chart_view.setStyleSheet("""
            QChartView {
                background: white;
                border-radius: 12px;
                border: 1px solid #ddd;
                padding: 10px;
            }
        """)
        scroll_layout.addWidget(self.chart_view)

        # === Category Pie Chart ===
        category_label = QLabel("🥧 Category Sales Breakdown")
        category_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px; color: #333;")
        scroll_layout.addWidget(category_label)

        self.category_chart_view = QChartView()
        self.category_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.category_chart_view.setMinimumHeight(400)
        self.category_chart_view.setStyleSheet("""
            QChartView {
                background: white;
                border-radius: 12px;
                border: 1px solid #ddd;
                padding: 10px;
            }
        """)
        scroll_layout.addWidget(self.category_chart_view)

        # === Table for Detailed Data ===
        table_label = QLabel("📅 Daily Sales Data")
        table_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px; color: #333;")
        scroll_layout.addWidget(table_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Date", "Orders", "Revenue (DA)", "Cost (DA)", "Profit (DA)"
        ])

        self.table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #ccc;
                border-radius: 10px;
                gridline-color: #ddd;
            }
            QHeaderView::section {
                background: #f4f4f4;
                font-weight: bold;
                border: none;
                padding: 6px;
            }
        """)
        scroll_layout.addWidget(self.table)

        # === Buttons (Export / Refresh) ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        export_btn = QPushButton("📤 Export CSV")
        export_btn.clicked.connect(self.export_csv)
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_data)

        for btn, color in [(export_btn, "#FF9800"), (refresh_btn, "#4CAF50")]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {color[:-1]}C;
                }}
            """)
            btn_layout.addWidget(btn)

        scroll_layout.addLayout(btn_layout)
        scroll_layout.addStretch()

        # === Load data ===
        self.load_data()

    # -------------------------------
    # Load Data from SQLite
    # -------------------------------
    def load_data(self, start_date=None, end_date=None):
        conn = get_connection()
        cursor = conn.cursor()

        # Revenue, Cost, and Profit grouped by date
        query = """
            SELECT 
                DATE(o.created_at) AS date,
                COUNT(DISTINCT o.id) AS orders,
                SUM(oi.quantity * oi.price) AS revenue,
                SUM(oi.quantity * p.cost) AS cost
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
        """
        params = []
        if start_date and end_date:
            query += " WHERE DATE(o.created_at) BETWEEN ? AND ?"
            params = [start_date, end_date]

        query += " GROUP BY DATE(o.created_at) ORDER BY DATE(o.created_at) ASC;"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]

        # --- Summary ---
        total_orders = sum(r["orders"] or 0 for r in data) if data else 0
        total_revenue = sum(r["revenue"] or 0 for r in data) if data else 0
        total_cost = sum(r["cost"] or 0 for r in data) if data else 0
        total_profit = total_revenue - total_cost
        avg_order = total_revenue / total_orders if total_orders else 0

        self.summary_label.setText(
            f"🧾 Total Orders: <b>{total_orders}</b> | "
            f"💰 Total Revenue: <b>{total_revenue:.2f} DA</b> | "
            f"💸 Total Cost: <b>{total_cost:.2f} DA</b> | "
            f"📊 Profit: <b style='color:green'>{total_profit:.2f} DA</b> | "
            f"📈 Avg Order: <b>{avg_order:.2f} DA</b>"
        )

        # --- Table ---
        self.table.setRowCount(len(data))
        for i, row in enumerate(data):
            profit = (row["revenue"] or 0) - (row["cost"] or 0)
            self.table.setItem(i, 0, QTableWidgetItem(str(row["date"])))
            self.table.setItem(i, 1, QTableWidgetItem(str(row["orders"])))
            self.table.setItem(i, 2, QTableWidgetItem(f"{row['revenue'] or 0:.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{row['cost'] or 0:.2f}"))
            profit_item = QTableWidgetItem(f"{profit:.2f}")
            if profit >= 0:
                profit_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                profit_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(i, 4, profit_item)

        # --- Charts ---
        self.update_sales_charts(data)
        self.update_category_chart()

        conn.close()

    # -------------------------------
    # Update Sales Charts
    # -------------------------------
    def update_sales_charts(self, data):
        chart = QChart()
        chart.setTitle("💹 Sales Overview (Revenue by Date & Top Days)")
        chart.setAnimationOptions(QChart.AnimationOption.AllAnimations)

        if not data:
            self.chart_view.setChart(chart)
            return

        bar_set = QBarSet("Revenue (DA)")
        categories = [str(row["date"]) for row in data]
        for row in data:
            bar_set << (row["revenue"] or 0)

        bar_series = QBarSeries()
        bar_series.append(bar_set)
        chart.addSeries(bar_series)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        bar_series.attachAxis(axis_x)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.chart_view.setChart(chart)

    # -------------------------------
    # Update Category Sales Breakdown
    # -------------------------------
    def update_category_chart(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.name AS category, SUM(oi.quantity * oi.price) AS total_sales
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            GROUP BY c.name
            ORDER BY total_sales DESC
        """)
        data = cursor.fetchall()
        conn.close()

        chart = QChart()
        chart.setTitle("🥧 Category Sales Breakdown")
        chart.setAnimationOptions(QChart.AnimationOption.AllAnimations)

        if not data:
            self.category_chart_view.setChart(chart)
            return

        pie_series = QPieSeries()
        for row in data:
            pie_series.append(row["category"], row["total_sales"] or 0)

        chart.addSeries(pie_series)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        self.category_chart_view.setChart(chart)

    # -------------------------------
    # Apply Filters
    # -------------------------------
    def apply_filter(self):
        option = self.filter_combo.currentText()
        today = datetime.now().date()

        if option == "Today":
            start = end = today
        elif option == "This Week":
            start = today - timedelta(days=today.weekday())
            end = today
        elif option == "Custom Range":
            start = self.start_date.date().toPyDate()
            end = self.end_date.date().toPyDate()
        else:
            start = end = None

        if start and end:
            self.load_data(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        else:
            self.load_data()

    # -------------------------------
    # Export to CSV
    # -------------------------------
    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", f"sales_report_{datetime.now().date()}.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Orders", "Revenue (DA)", "Average Order (DA)"])
                for row in range(self.table.rowCount()):
                    writer.writerow([
                        self.table.item(row, 0).text(),
                        self.table.item(row, 1).text(),
                        self.table.item(row, 2).text(),
                        self.table.item(row, 3).text(),
                    ])
            QMessageBox.information(self, "✅ Success", f"Report exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Failed to export CSV:\n{str(e)}")
