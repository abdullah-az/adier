class AnalysisServiceError(Exception):
    """Custom exception for analysis service errors"""
    def __init__(self, message: str, error_code: str = None, original_exception: Exception = None):
        self.message = message
        self.error_code = error_code
        self.original_exception = original_exception
        super().__init__(self.message)

    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message