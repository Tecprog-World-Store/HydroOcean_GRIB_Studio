from PySide6.QtCore import QObject, Signal, Slot

class FunctionWorker(QObject):
    progress = Signal(int, int, str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    @Slot()
    def run(self):
        try:
            result = self.fn(lambda a,b,c: self.progress.emit(a,b,c))
            self.finished.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))
