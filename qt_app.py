#!/usr/bin/env python3
"""PyQt6 desktop GUI: IP fragmentation lab with path animation and hover."""

from __future__ import annotations

import sys

from PyQt6.QtCore import QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from ipfrag.diagram import color_for, explain_steps, hover_story_plain
from ipfrag.engine import FragmentationError, FragmentationResult, fragment_ipv4


class PacketCanvas(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.result: FragmentationResult | None = None
        self.progress = 1.0
        self.hover_index = 0
        self.hit_rects: list[tuple[QRectF, int]] = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.setMinimumHeight(360)
        self.setMouseTracking(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor("#020617"))
        self.setPalette(pal)
        self.setAutoFillBackground(True)

    def set_result(self, result: FragmentationResult, animate: bool = False) -> None:
        self.result = result
        self.hover_index = 0
        if animate:
            self.progress = 0.0
            self._timer.start(32)
        else:
            self.progress = 1.0
            self._timer.stop()
        self.update()

    def _tick(self) -> None:
        self.progress = min(1.0, self.progress + 0.01)
        if self.progress >= 1.0:
            self._timer.stop()
        self.update()

    def _layout(self) -> tuple[float, float, float]:
        return 70.0, self.width() * 0.46, self.width() - 90.0

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        pos = event.position()
        found = 0
        for rect, index in self.hit_rects:
            if rect.contains(pos):
                found = index
                break
        if found != self.hover_index:
            self.hover_index = found
            self.update()
        if found and self.result:
            frag = self.result.fragments[found - 1]
            QToolTip.showText(
                event.globalPosition().toPoint(),
                hover_story_plain(frag, self.result),
                self,
            )
        else:
            QToolTip.hideText()

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.hover_index = 0
        QToolTip.hideText()
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#020617"))
        self.hit_rects = []
        if self.result is None:
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Enter values and click Fragment or Animate send",
            )
            return

        result = self.result
        src, gate, dst = self._layout()
        mid_y = self.height() * 0.42
        n = result.fragment_count

        def node(x: float, title: str) -> None:
            box = QRectF(x - 52, 18, 104, 46)
            painter.setPen(QPen(QColor("#38bdf8"), 1))
            painter.setBrush(QColor("#1e3a5f"))
            painter.drawRoundedRect(box, 8, 8)
            painter.setPen(QColor("#e2e8f0"))
            painter.setFont(QFont("Helvetica", 10, QFont.Weight.Bold))
            painter.drawText(box, Qt.AlignmentFlag.AlignCenter, title)

        node(src, "Host A\nsender")
        node(gate, f"Router\nMTU {result.mtu} B")
        node(dst, "Host B\nreassemble")

        painter.setPen(QPen(QColor("#334155"), 4))
        painter.drawLine(int(src + 52), int(mid_y), int(gate - 54), int(mid_y))
        painter.drawLine(int(gate + 54), int(mid_y), int(dst - 54), int(mid_y))
        painter.setPen(QPen(QColor("#f97316"), 2, Qt.PenStyle.DashLine))
        painter.drawRect(QRectF(gate - 16, mid_y - 70, 32, 140))
        painter.setPen(QColor("#fdba74"))
        painter.setFont(QFont("Helvetica", 9))
        painter.drawText(QRectF(gate - 70, mid_y + 78, 140, 20), Qt.AlignmentFlag.AlignCenter, "MTU gate")

        p = self.progress
        orig_visible = p < 0.36 or not result.fragmented
        if orig_visible:
            if p < 0.28:
                ox = src + (gate - src) * (p / 0.28)
            elif p < 0.36:
                ox = gate
            else:
                ox = dst if not result.fragmented else gate
            size = 50.0
            rect = QRectF(ox - size / 2, mid_y - 16, size, 32)
            painter.setBrush(QColor("#64748b"))
            painter.setPen(QPen(QColor("#f8fafc"), 2))
            painter.drawRoundedRect(rect, 6, 6)
            painter.setPen(QColor("#f8fafc"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "DATAGRAM")

        span = 0.62 / max(n, 1)
        for frag in result.fragments:
            start = 0.36 + (frag.index - 1) * span * 0.35
            if result.fragmented:
                if p < start and p < 1.0:
                    continue
                local = 1.0 if p >= 1.0 else max(0.0, min(1.0, (p - start) / max(span * 0.9, 0.05)))
                fx = gate + (dst - gate) * local
            else:
                fx = dst if p >= 0.36 else gate
            fy = mid_y - 24 + (frag.index - (n + 1) / 2) * 36
            w = 36 + 40 * (frag.total_size / max(result.mtu, 1))
            rect = QRectF(fx - w / 2, fy - 14, w, 28)
            accent = self.hover_index == frag.index
            painter.setBrush(QColor(color_for(frag.index)))
            painter.setPen(QPen(QColor("#facc15" if accent else "#0f172a"), 3 if accent else 1))
            painter.drawRoundedRect(rect, 6, 6)
            painter.setPen(QColor("#020617"))
            painter.setFont(QFont("Helvetica", 9, QFont.Weight.Bold))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"F{frag.index}")
            self.hit_rects.append((rect, frag.index))

        painter.setPen(QColor("#94a3b8"))
        painter.setFont(QFont("Helvetica", 10))
        painter.drawText(
            16,
            self.height() - 14,
            "Hover a fragment square for offset, MF, and payload byte range.",
        )
        if self.hover_index and result:
            frag = result.fragments[self.hover_index - 1]
            painter.setPen(QColor("#e2e8f0"))
            painter.drawText(
                16,
                self.height() - 32,
                f"F{frag.index}: bytes {frag.offset_bytes}–{frag.payload_end - 1}  "
                f"off={frag.offset_units}  {frag.flags_label}  {frag.total_size} B on wire",
            )


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("IPv4 Fragmentation Lab")
        self.resize(1180, 760)
        self._result: FragmentationResult | None = None

        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        panel = QFrame()
        form_wrap = QVBoxLayout(panel)
        title = QLabel("Network layer — IPv4 fragmentation")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        form_wrap.addWidget(title)
        blurb = QLabel(
            "The datagram leaves Host A, hits the router’s MTU gate, then travels "
            "as fragments to Host B. Hover a colored square or a table row for the "
            "payload slice, offset (bytes ÷ 8), and MF flag."
        )
        blurb.setWordWrap(True)
        form_wrap.addWidget(blurb)

        form = QFormLayout()
        self.packet = QSpinBox()
        self.packet.setRange(20, 65535)
        self.packet.setValue(4000)
        self.mtu = QSpinBox()
        self.mtu.setRange(28, 65535)
        self.mtu.setValue(1500)
        self.header = QSpinBox()
        self.header.setRange(20, 60)
        self.header.setSingleStep(4)
        self.header.setValue(20)
        self.ident = QSpinBox()
        self.ident.setRange(0, 65535)
        self.ident.setValue(777)
        form.addRow("Packet size (B)", self.packet)
        form.addRow("MTU (B)", self.mtu)
        form.addRow("Header size (B)", self.header)
        form.addRow("Identification", self.ident)
        form_wrap.addLayout(form)

        row = QHBoxLayout()
        self.go = QPushButton("Fragment")
        self.go.clicked.connect(self.run_now)
        self.play = QPushButton("Animate send")
        self.play.clicked.connect(self.run_animated)
        self.preset = QPushButton("Load 4000 / 1500 / 20")
        self.preset.clicked.connect(self.load_preset)
        row.addWidget(self.go)
        row.addWidget(self.play)
        form_wrap.addLayout(row)
        form_wrap.addWidget(self.preset)

        self.notes = QTextEdit()
        self.notes.setReadOnly(True)
        form_wrap.addWidget(self.notes, 1)
        splitter.addWidget(panel)

        right = QWidget()
        right_l = QVBoxLayout(right)
        self.canvas = PacketCanvas()
        right_l.addWidget(self.canvas, 2)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["#", "ID", "Header", "Payload", "Total", "Offset B", "Offset ×8", "Flags DF/MF"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setMouseTracking(True)
        self.table.viewport().setMouseTracking(True)
        self.table.cellEntered.connect(self._table_hover)
        right_l.addWidget(self.table, 1)
        splitter.addWidget(right)
        splitter.setSizes([320, 860])

        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #0b1220; color: #e2e8f0; }
            QFrame { background: #111827; border-radius: 12px; }
            QPushButton { background: #2563eb; color: white; padding: 8px 12px;
                          border-radius: 8px; font-weight: 600; }
            QPushButton:hover { background: #1d4ed8; }
            QSpinBox, QTextEdit, QTableWidget { background: #020617; color: #e2e8f0;
                          border: 1px solid #1e293b; border-radius: 6px; }
            QHeaderView::section { background: #1e293b; color: #e2e8f0; padding: 4px; }
            QToolTip { background: #0f172a; color: #e2e8f0; border: 1px solid #38bdf8;
                       padding: 8px; }
            """
        )

    def load_preset(self) -> None:
        self.packet.setValue(4000)
        self.mtu.setValue(1500)
        self.header.setValue(20)
        self.ident.setValue(777)

    def _compute(self) -> FragmentationResult | None:
        try:
            return fragment_ipv4(
                self.packet.value(),
                self.mtu.value(),
                self.header.value(),
                self.ident.value(),
            )
        except FragmentationError as exc:
            QMessageBox.warning(self, "Invalid input", str(exc))
            return None

    def _fill_table(self, result: FragmentationResult) -> None:
        self.table.setRowCount(len(result.fragments))
        for row, frag in enumerate(result.fragments):
            values = [
                frag.index,
                frag.identification,
                frag.header_size,
                frag.payload_size,
                frag.total_size,
                frag.offset_bytes,
                frag.offset_units,
                frag.flags_label,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setToolTip(hover_story_plain(frag, result))
                self.table.setItem(row, col, item)

    def _table_hover(self, row: int, _col: int) -> None:
        if self._result is None or row < 0 or row >= len(self._result.fragments):
            return
        self.canvas.hover_index = self._result.fragments[row].index
        self.canvas.update()

    def _fill_notes(self, result: FragmentationResult) -> None:
        steps = explain_steps(result)
        body = "\n".join(f"• {n}" for n in result.notes)
        body += "\n\nWalk-through:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        self.notes.setPlainText(body)

    def run_now(self) -> None:
        result = self._compute()
        if result is None:
            return
        self._result = result
        self.canvas.set_result(result, animate=False)
        self._fill_table(result)
        self._fill_notes(result)

    def run_animated(self) -> None:
        result = self._compute()
        if result is None:
            return
        self._result = result
        self._fill_table(result)
        self._fill_notes(result)
        self.canvas.set_result(result, animate=True)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
