import math
import tkinter as tk
from tkinter import messagebox, ttk


BACKGROUND = "#10151d"
PANEL = "#19212c"
TEXT = "#e8edf4"
MUTED = "#a5b1c2"
ACCENT = "#54d6a0"
BAR_COLOR = "#4da3ff"


class DataChartApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de gráficos")
        self.root.geometry("1050x700")
        self.root.minsize(760, 560)
        self.root.configure(bg=BACKGROUND)
        self.values = []
        self._configure_styles()
        self._build_interface()

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=BACKGROUND)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure(
            "TLabel",
            background=BACKGROUND,
            foreground=TEXT,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Panel.TLabel",
            background=PANEL,
            foreground=TEXT,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Title.TLabel",
            background=BACKGROUND,
            foreground=TEXT,
            font=("Segoe UI", 20, "bold"),
        )
        style.configure("Muted.TLabel", background=BACKGROUND, foreground=MUTED)
        style.configure("PanelMuted.TLabel", background=PANEL, foreground=MUTED)
        style.configure(
            "Accent.TButton",
            background=ACCENT,
            foreground="#102018",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
        )
        style.map("Accent.TButton", background=[("active", "#70e9b7")])

    def _build_interface(self):
        outer = ttk.Frame(self.root, padding=22)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        header = ttk.Frame(outer)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        ttk.Label(header, text="Generador de gráficos", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Indica cuántos datos tienes, escríbelos y visualízalos en un gráfico.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        content = ttk.Frame(outer)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1, uniform="columns")
        content.columnconfigure(1, weight=2, uniform="columns")
        content.rowconfigure(0, weight=1)

        self._build_input_panel(content)
        self._build_chart_panel(content)

    def _build_input_panel(self, parent):
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(4, weight=1)

        ttk.Label(
            panel,
            text="Tus datos",
            style="Panel.TLabel",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            panel,
            text="1. Escribe la cantidad de valores:",
            style="PanelMuted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(18, 6))

        self.count_entry = ttk.Entry(panel)
        self.count_entry.insert(0, "5")
        self.count_entry.grid(row=2, column=0, sticky="ew")

        ttk.Label(
            panel,
            text="2. Escribe los valores separados por coma, espacio o salto de línea:",
            style="PanelMuted.TLabel",
            wraplength=300,
        ).grid(row=3, column=0, sticky="w", pady=(16, 6))

        self.data_text = tk.Text(
            panel,
            height=8,
            wrap="word",
            bg="#0c1118",
            fg=TEXT,
            insertbackground=TEXT,
            selectbackground="#31577d",
            relief="flat",
            padx=10,
            pady=10,
            font=("Consolas", 11),
        )
        self.data_text.grid(row=4, column=0, sticky="nsew")
        self.data_text.insert("1.0", "12, 18, 9, 24, 15")

        ttk.Label(
            panel,
            text="3. Elige el tipo de gráfico:",
            style="PanelMuted.TLabel",
        ).grid(row=5, column=0, sticky="w", pady=(16, 6))

        self.chart_type = tk.StringVar(value="Barras")
        self.chart_selector = ttk.Combobox(
            panel,
            textvariable=self.chart_type,
            values=("Barras", "Líneas"),
            state="readonly",
        )
        self.chart_selector.grid(row=6, column=0, sticky="ew")
        self.chart_selector.bind("<<ComboboxSelected>>", lambda _event: self.generate_chart())

        ttk.Button(
            panel,
            text="Generar gráfico",
            style="Accent.TButton",
            command=self.generate_chart,
        ).grid(row=7, column=0, sticky="ew", pady=(18, 0))

    def _build_chart_panel(self, parent):
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        self.chart_title = ttk.Label(
            panel,
            text="Gráfico de tus datos",
            style="Panel.TLabel",
            font=("Segoe UI", 14, "bold"),
        )
        self.chart_title.grid(row=0, column=0, sticky="w", pady=(0, 12))

        self.canvas = tk.Canvas(
            panel,
            bg=PANEL,
            highlightthickness=0,
            height=380,
        )
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda _event: self._draw_chart())

        self.summary = ttk.Label(
            panel,
            text="Ingresa tus datos para ver un resumen.",
            style="PanelMuted.TLabel",
        )
        self.summary.grid(row=2, column=0, sticky="w", pady=(12, 0))

    def generate_chart(self):
        try:
            count_text = self.count_entry.get().strip()
            count = int(count_text)
            if count < 1:
                raise ValueError("La cantidad debe ser mayor que cero.")

            raw_values = self.data_text.get("1.0", "end-1c")
            tokens = raw_values.replace(",", " ").replace(";", " ").split()
            if len(tokens) != count:
                raise ValueError(
                    f"Indicaste {count} datos, pero escribiste {len(tokens)}."
                )

            values = [float(token) for token in tokens]
            if not all(math.isfinite(value) for value in values):
                raise ValueError("Los datos deben ser números válidos.")
        except ValueError as error:
            messagebox.showwarning("Revisa los datos", str(error))
            return

        self.values = values
        self.chart_title.configure(text=f"Gráfico de {count} datos · {self.chart_type.get()}")
        average = sum(values) / count
        self.summary.configure(
            text=(
                f"Cantidad: {count}    "
                f"Promedio: {average:.2f}    "
                f"Mínimo: {min(values):g}    "
                f"Máximo: {max(values):g}"
            )
        )
        self._draw_chart()

    def _draw_chart(self):
        canvas = self.canvas
        canvas.delete("all")
        if not self.values:
            return

        width = max(canvas.winfo_width(), 360)
        height = max(canvas.winfo_height(), 300)
        left, right, top, bottom = 62, width - 24, 24, height - 48
        plot_width = right - left
        plot_height = bottom - top
        minimum = min(min(self.values), 0)
        maximum = max(max(self.values), 0)
        if minimum == maximum:
            minimum -= 1
            maximum += 1
        padding = (maximum - minimum) * 0.08
        minimum -= padding
        maximum += padding

        def y_position(value):
            return bottom - (value - minimum) / (maximum - minimum) * plot_height

        for index in range(5):
            value = minimum + (maximum - minimum) * index / 4
            y = y_position(value)
            canvas.create_line(left, y, right, y, fill="#2a3542")
            canvas.create_text(
                left - 10,
                y,
                text=f"{value:.1f}",
                fill=MUTED,
                anchor="e",
                font=("Segoe UI", 8),
            )

        zero_y = y_position(0)
        canvas.create_line(left, top, left, bottom, fill=MUTED)
        canvas.create_line(left, zero_y, right, zero_y, fill=MUTED)

        count = len(self.values)
        step = plot_width / count
        if self.chart_type.get() == "Líneas":
            points = [
                (left + step * (index + 0.5), y_position(value))
                for index, value in enumerate(self.values)
            ]
            if len(points) > 1:
                for start, end in zip(points, points[1:]):
                    canvas.create_line(*start, *end, fill=ACCENT, width=3)
            for index, (x, y) in enumerate(points):
                canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=ACCENT, outline="")
                self._draw_x_label(canvas, index, x, bottom)
        else:
            bar_width = min(step * 0.65, 48)
            for index, value in enumerate(self.values):
                x = left + step * (index + 0.5)
                y = y_position(value)
                canvas.create_rectangle(
                    x - bar_width / 2,
                    min(y, zero_y),
                    x + bar_width / 2,
                    max(y, zero_y),
                    fill=BAR_COLOR,
                    outline="",
                )
                self._draw_x_label(canvas, index, x, bottom)

    @staticmethod
    def _draw_x_label(canvas, index, x, bottom):
        canvas.create_text(
            x,
            bottom + 18,
            text=str(index + 1),
            fill=MUTED,
            font=("Segoe UI", 8),
        )


def main():
    root = tk.Tk()
    DataChartApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
