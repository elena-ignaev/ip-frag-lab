#!/usr/bin/env python3
"""PyQt6 desktop GUI: IP fragmentation lab with a simple animation."""

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
    QVBoxLayout,
    QWidget,
)

from ipfrag.diagram import color_for, explain_steps
from ipfrag.engine import FragmentationError, FragmentationResult, fragment_ipv4


class PacketCanvas(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.result: FragmentationResult | None = None
        self.visible_count = 0
        self.setMinimumHeight(280)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor("#020617"))
        self.setPalette(pal)

    def set_result(self, result: FragmentationResult, visible_count: int | None = None) -> None:
        self.result = result
        self.visible_count = result.fragment_count if visible_count is None else visible_count
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#020617"))
        if self.result is None:
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Enter values and click Fragment")
            return

        result = self.result
        margin = 24
        width = max(40, self.width() - 2 * margin)
        scale = width / max(result.packet_size, 1)

        def draw_bar(y: int, x0: float, w: float, color: str, label: str, h: int = 36) -> None:
            rect = QRectF(margin + x0, y, max(w, 2), h)
            painter.setPen(QPen(QColor("#0f172a"), 1))
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(rect, 6, 6)
            painter.setPen(QColor("#f8fafc"))
            painter.setFont(QFont("Menlo", 10))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

        painter.setPen(QColor("#e2e8f0"))
        painter.setFont(QFont("Helvetica", 12, QFont.Weight.Bold))
        painter.drawText(margin, 22, "Original datagram")

        draw_bar(32, 0, result.header_size * scale, "#1e3a5f", f"H {result.header_size}")
        draw_bar(
            32,
            result.header_size * scale,
            result.payload_size * scale,
            "#475569",
            f"Payload {result.payload_size} B",
        )

        painter.drawText(margin, 92, "Fragments (each has its own header)")
        y = 108
        shown = min(self.visible_count, result.fragment_count)
        for frag in result.fragments[:shown]:
            draw_bar(y, 0, frag.header_size * scale, "#1e3a5f", f"H {frag.header_size}", 32)
            draw_bar(
                y,
                frag.header_size * scale,
                frag.payload_size * scale,
                color_for(frag.index),
                f"F{frag.index}  {frag.payload_size} B  off={frag.offset_units}  MF={frag.mf}",
                32,
            )
            y += 42

        painter.setPen(QColor("#94a3b8"))
        painter.setFont(QFont("Helvetica", 10))
        painter.drawText(
            margin,
            self.height() - 12,
            f"MTU {result.mtu} B   ID {result.identification}   "
            f"{'fragmented' if result.fragmented else 'no fragmentation needed'}",
        )


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("IPv4 Fragmentation Lab")
        self.resize(1100, 720)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._pending = 0
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
            "This desktop lab shows how a router splits a datagram so each fragment "
            "fits the next-hop MTU. Offsets are in units of 8 bytes; MF marks every "
            "piece except the last."
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
        self.play = QPushButton("Animate")
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
        right_l.addWidget(self.table, 1)
        splitter.addWidget(right)
        splitter.setSizes([320, 780])

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
                self.table.setItem(row, col, item)

    def _fill_notes(self, result: FragmentationResult, limit_steps: int | None = None) -> None:
        steps = explain_steps(result)
        if limit_steps is not None:
            steps = steps[:limit_steps]
        body = "\n".join(f"• {n}" for n in result.notes)
        body += "\n\nWalk-through:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        self.notes.setPlainText(body)

    def run_now(self) -> None:
        self._timer.stop()
        result = self._compute()
        if result is None:
            return
        self._result = result
        self.canvas.set_result(result)
        self._fill_table(result)
        self._fill_notes(result)

    def run_animated(self) -> None:
        result = self._compute()
        if result is None:
            return
        self._result = result
        self._pending = 0
        self.table.setRowCount(0)
        self.canvas.set_result(result, visible_count=0)
        self.notes.setPlainText("Animating fragment creation…")
        self._timer.start(850)

    def _tick(self) -> None:
        if self._result is None:
            self._timer.stop()
            return
        self._pending += 1
        self.canvas.set_result(self._result, visible_count=self._pending)
        shown = self._result.fragments[: self._pending]
        tmp = FragmentationResult(
            packet_size=self._result.packet_size,
            mtu=self._result.mtu,
            header_size=self._result.header_size,
            payload_size=self._result.payload_size,
            max_fragment_payload=self._result.max_fragment_payload,
            identification=self._result.identification,
            fragmented=self._result.fragmented,
            fragments=list(shown),
            notes=self._result.notes,
        )
        self._fill_table(tmp)
        self._fill_notes(self._result, limit_steps=3 + self._pending)
        if self._pending >= self._result.fragment_count:
            self._timer.stop()
            self._fill_table(self._result)
            self._fill_notes(self._result)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
