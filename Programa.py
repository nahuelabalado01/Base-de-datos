import ast
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk
from pathlib import Path


@dataclass
class FunctionMetrics:
    name: str
    lines: int
    branches: int
    loops: int
    calls: int
    complexity: int


class FunctionCollector(ast.NodeVisitor):
    def __init__(self):
        self.scope = []
        self.functions = {}

    def visit_ClassDef(self, node):
        self.scope.append(node.name)
        for statement in node.body:
            self.visit(statement)
        self.scope.pop()

    def visit_FunctionDef(self, node):
        self._collect(node)

    def visit_AsyncFunctionDef(self, node):
        self._collect(node)

    def _collect(self, node):
        name = ".".join(self.scope + [node.name])
        self.functions[name] = node
        self.scope.append(node.name)
        for statement in node.body:
            self.visit(statement)
        self.scope.pop()


class FunctionAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.branches = 0
        self.loops = 0
        self.calls = 0

    def visit_FunctionDef(self, node):
        return

    def visit_AsyncFunctionDef(self, node):
        return

    def visit_ClassDef(self, node):
        return

    def visit_If(self, node):
        self.branches += 1
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.branches += 1
        self.generic_visit(node)

    def visit_Try(self, node):
        self.branches += len(node.handlers)
        self.generic_visit(node)

    def visit_Match(self, node):
        self.branches += max(0, len(node.cases) - 1)
        self.generic_visit(node)

    def visit_For(self, node):
        self.loops += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self.loops += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.loops += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.branches += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_Call(self, node):
        self.calls += 1
        self.generic_visit(node)


def analyze_source(source):
    tree = ast.parse(source)
    collector = FunctionCollector()
    collector.visit(tree)
    metrics = {}

    for name, node in collector.functions.items():
        analyzer = FunctionAnalyzer()
        for statement in node.body:
            analyzer.visit(statement)
        line_count = getattr(node, "end_lineno", node.lineno) - node.lineno + 1
        metrics[name] = FunctionMetrics(
            name=name,
            lines=line_count,
            branches=analyzer.branches,
            loops=analyzer.loops,
            calls=analyzer.calls,
            complexity=1 + analyzer.branches + analyzer.loops,
        )

    return metrics


class ProgramAnalyzerApp:
    BACKGROUND = "#10151d"
    PANEL = "#19212c"
    TEXT = "#e8edf4"
    MUTED = "#a5b1c2"
    ACCENT = "#54d6a0"
    BAR = "#4da3ff"

    def __init__(self, root):
        self.root = root
        self.metrics = {}
        self.root.title("Analizador de programas Python")
        self.root.geometry("1180x760")
        self.root.minsize(900, 620)
        self.root.configure(bg=self.BACKGROUND)
        self._configure_styles()
        self._build_interface()

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "TFrame",
            background=self.BACKGROUND,
        )
        style.configure(
            "Panel.TFrame",
            background=self.PANEL,
        )
        style.configure(
            "TLabel",
            background=self.BACKGROUND,
            foreground=self.TEXT,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Panel.TLabel",
            background=self.PANEL,
            foreground=self.TEXT,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Title.TLabel",
            background=self.BACKGROUND,
            foreground=self.TEXT,
            font=("Segoe UI", 20, "bold"),
        )
        style.configure(
            "Muted.TLabel",
            background=self.BACKGROUND,
            foreground=self.MUTED,
        )
        style.configure(
            "PanelMuted.TLabel",
            background=self.PANEL,
            foreground=self.MUTED,
        )
        style.configure(
            "Accent.TButton",
            background=self.ACCENT,
            foreground="#102018",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
        )
        style.map("Accent.TButton", background=[("active", "#70e9b7")])

    def _build_interface(self):
        outer = ttk.Frame(self.root, padding=20)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        header = ttk.Frame(outer)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        ttk.Label(header, text="Analizador de programas Python", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Selecciona una función para revisar su estructura y complejidad, sin ejecutar el código.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        content = ttk.Frame(outer)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=5, uniform="columns")
        content.columnconfigure(1, weight=6, uniform="columns")
        content.rowconfigure(0, weight=1)

        self._build_source_panel(content)
        self._build_analysis_panel(content)

    def _build_source_panel(self, parent):
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=16)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(2, weight=1)

        ttk.Label(panel, text="Código fuente", style="Panel.TLabel", font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            panel,
            text="Pega el código o abre un archivo .py",
            style="PanelMuted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 10))

        editor_frame = ttk.Frame(panel, style="Panel.TFrame")
        editor_frame.grid(row=2, column=0, sticky="nsew")
        editor_frame.columnconfigure(0, weight=1)
        editor_frame.rowconfigure(0, weight=1)
        self.source_text = tk.Text(
            editor_frame,
            wrap="none",
            undo=True,
            bg="#0c1118",
            fg=self.TEXT,
            insertbackground=self.TEXT,
            selectbackground="#31577d",
            relief="flat",
            padx=10,
            pady=10,
            font=("Consolas", 10),
        )
        self.source_text.grid(row=0, column=0, sticky="nsew")
        source_scroll = ttk.Scrollbar(editor_frame, orient="vertical", command=self.source_text.yview)
        source_scroll.grid(row=0, column=1, sticky="ns")
        self.source_text.configure(yscrollcommand=source_scroll.set)

        actions = ttk.Frame(panel, style="Panel.TFrame")
        actions.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        ttk.Button(actions, text="Abrir archivo", command=self.open_file).pack(side="left")
        ttk.Label(
            panel,
            text="El análisis es estático: el programa no se ejecuta.",
            style="PanelMuted.TLabel",
        ).grid(row=4, column=0, sticky="w", pady=(10, 0))

    def _build_analysis_panel(self, parent):
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=16)
        panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(3, weight=1)
        panel.rowconfigure(5, weight=1)

        ttk.Label(panel, text="Función a analizar", style="Panel.TLabel", font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        selector = ttk.Frame(panel, style="Panel.TFrame")
        selector.grid(row=1, column=0, sticky="ew", pady=(8, 12))
        selector.columnconfigure(0, weight=1)
        self.function_name = tk.StringVar()
        self.function_entry = ttk.Entry(selector, textvariable=self.function_name)
        self.function_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.function_entry.bind("<Return>", lambda _event: self.analyze())
        ttk.Button(selector, text="Analizar", style="Accent.TButton", command=self.analyze).grid(row=0, column=1)

        self.summary_label = ttk.Label(
            panel,
            text="Carga o pega un programa y escribe el nombre de una función.",
            style="PanelMuted.TLabel",
            wraplength=500,
        )
        self.summary_label.grid(row=2, column=0, sticky="w", pady=(0, 10))

        complexity_frame = ttk.Frame(panel, style="Panel.TFrame")
        complexity_frame.grid(row=3, column=0, sticky="nsew")
        complexity_frame.columnconfigure(0, weight=1)
        complexity_frame.rowconfigure(1, weight=1)
        ttk.Label(
            complexity_frame,
            text="Complejidad por función",
            style="Panel.TLabel",
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(4, 5))
        self.complexity_canvas = tk.Canvas(
            complexity_frame,
            bg=self.PANEL,
            highlightthickness=0,
            height=185,
        )
        self.complexity_canvas.grid(row=1, column=0, sticky="nsew")
        self.complexity_canvas.bind("<Configure>", lambda _event: self._draw_complexity_chart())

        metric_frame = ttk.Frame(panel, style="Panel.TFrame")
        metric_frame.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        metric_frame.columnconfigure(0, weight=1)
        ttk.Label(
            metric_frame,
            text="Indicadores de la función seleccionada",
            style="Panel.TLabel",
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.metrics_canvas = tk.Canvas(
            metric_frame,
            bg=self.PANEL,
            highlightthickness=0,
            height=150,
        )
        self.metrics_canvas.grid(row=1, column=0, sticky="ew")

        self.status_label = ttk.Label(
            panel,
            text="Complejidad ciclomática estimada = 1 + decisiones + bucles.",
            style="PanelMuted.TLabel",
            wraplength=500,
        )
        self.status_label.grid(row=5, column=0, sticky="sw", pady=(10, 0))

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="Abrir programa Python",
            filetypes=[("Archivos Python", "*.py"), ("Todos los archivos", "*.*")],
        )
        if not file_path:
            return
        try:
            source = Path(file_path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            messagebox.showerror("No se pudo abrir el archivo", str(error))
            return

        self.source_text.delete("1.0", "end")
        self.source_text.insert("1.0", source)
        self.root.title(f"Analizador de programas Python - {Path(file_path).name}")
        self._analyze_source(show_errors=False)

    def analyze(self):
        self._analyze_source(show_errors=True)

    def _analyze_source(self, show_errors):
        source = self.source_text.get("1.0", "end-1c")
        if not source.strip():
            self._show_error("Agrega código fuente antes de analizar.")
            return

        try:
            metrics = analyze_source(source)
        except SyntaxError as error:
            location = f"Línea {error.lineno}" if error.lineno else "Código"
            self._show_error(f"{location}: {error.msg}")
            return

        if not metrics:
            self.metrics = {}
            self.summary_label.configure(text="No se encontraron funciones en el código.")
            self.status_label.configure(text="Define al menos una función con def o async def.")
            self._draw_complexity_chart()
            self._draw_metrics_chart(None)
            return

        self.metrics = metrics
        requested = self.function_name.get().strip()
        selected_name = self._resolve_function_name(requested)
        if selected_name is None:
            if requested:
                available = ", ".join(metrics)
                self._show_error(f"No se encontró «{requested}». Funciones disponibles: {available}")
            else:
                selected_name = next(iter(metrics))
                self.function_name.set(selected_name)

        if selected_name is None:
            return

        selected = metrics[selected_name]
        total_lines = sum(metric.lines for metric in metrics.values())
        self.summary_label.configure(
            text=(
                f"Programa: {len(metrics)} función(es) · {total_lines} líneas en funciones\n"
                f"Seleccionada: {selected.name} · complejidad estimada {selected.complexity}"
            )
        )
        self.status_label.configure(
            text="Estimación estática; no mide tiempo de ejecución ni incluye funciones llamadas externas."
        )
        self._draw_complexity_chart(selected_name)
        self._draw_metrics_chart(selected)

    def _resolve_function_name(self, requested):
        if not requested:
            return None
        if requested in self.metrics:
            return requested
        matches = [name for name in self.metrics if name.split(".")[-1] == requested]
        return matches[0] if len(matches) == 1 else None

    def _show_error(self, text):
        self.summary_label.configure(text=text)
        self.status_label.configure(text="Revisa el código o el nombre de la función e inténtalo de nuevo.")
        self._draw_metrics_chart(None)
        if self.metrics:
            self._draw_complexity_chart()
        if text.startswith("No se encontró") or text.startswith("Agrega") or text.startswith("Línea"):
            messagebox.showwarning("No se pudo completar el análisis", text)

    def _draw_complexity_chart(self, selected_name=None):
        canvas = self.complexity_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 300)
        row_height = 27
        items = sorted(self.metrics.values(), key=lambda item: item.complexity, reverse=True)
        canvas.configure(scrollregion=(0, 0, width, max(185, len(items) * row_height + 12)))
        if not items:
            canvas.create_text(
                12, 24, anchor="nw", text="El gráfico aparecerá después del análisis.",
                fill=self.MUTED, font=("Segoe UI", 9),
            )
            return

        label_width = min(150, max(85, width // 3))
        available_width = max(width - label_width - 55, 70)
        max_value = max(item.complexity for item in items) or 1
        for index, item in enumerate(items):
            y = 12 + index * row_height
            label = item.name if len(item.name) < 22 else item.name[:19] + "..."
            color = self.ACCENT if item.name == selected_name else self.BAR
            canvas.create_text(8, y + 8, anchor="w", text=label, fill=self.TEXT, font=("Segoe UI", 9))
            canvas.create_rectangle(
                label_width, y, label_width + available_width, y + 16, fill="#273442", outline=""
            )
            bar_width = available_width * item.complexity / max_value
            canvas.create_rectangle(
                label_width, y, label_width + bar_width, y + 16, fill=color, outline=""
            )
            canvas.create_text(
                label_width + available_width + 8, y + 8,
                anchor="w", text=str(item.complexity), fill=self.TEXT, font=("Segoe UI", 9),
            )

    def _draw_metrics_chart(self, metric):
        canvas = self.metrics_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 300)
        rows = (
            ("Líneas", metric.lines),
            ("Decisiones", metric.branches),
            ("Bucles", metric.loops),
            ("Llamadas", metric.calls),
        ) if metric else ()
        label_width = 85
        available_width = max(width - label_width - 42, 70)
        max_value = max((value for _, value in rows), default=1) or 1
        for index, (label, value) in enumerate(rows):
            y = 8 + index * 32
            canvas.create_text(8, y + 8, anchor="w", text=label, fill=self.MUTED, font=("Segoe UI", 9))
            canvas.create_rectangle(
                label_width, y, label_width + available_width, y + 17, fill="#273442", outline=""
            )
            canvas.create_rectangle(
                label_width,
                y,
                label_width + available_width * value / max_value,
                y + 17,
                fill=self.ACCENT,
                outline="",
            )
            canvas.create_text(
                label_width + available_width + 8, y + 8,
                anchor="w", text=str(value), fill=self.TEXT, font=("Segoe UI", 9),
            )
        if not metric:
            canvas.create_text(
                8, 12, anchor="nw", text="Selecciona una función para ver sus métricas.",
                fill=self.MUTED, font=("Segoe UI", 9),
            )


def main():
    root = tk.Tk()
    ProgramAnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()