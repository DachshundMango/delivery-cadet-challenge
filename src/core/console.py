"""
Unified console output interface for data pipeline scripts.
Provides consistent formatting across all pipeline modules.
"""


class Console:
    """Unified console output interface for pipeline scripts"""

    # ANSI Colors (minimal usage)
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Separators
    THICK_LINE = "=" * 64
    THIN_LINE = "-" * 64

    @staticmethod
    def header(title: str):
        """Print script header"""
        print(f"\n{Console.THICK_LINE}")
        print(title.upper())
        print(f"{Console.THICK_LINE}\n")

    @staticmethod
    def step(current: int, total: int, title: str):
        """Print step progress"""
        print(f"\n[{current}/{total}] {title}...")

    @staticmethod
    def info(message: str, indent: int = 1):
        """Print general information"""
        prefix = "      " * indent
        print(f"{prefix}{message}")

    @staticmethod
    def success(message: str, indent: int = 1):
        """Print success message (green)"""
        prefix = "      " * indent
        print(f"{Console.GREEN}{prefix}{message}{Console.RESET}")

    @staticmethod
    def warning(message: str, detail: str = None):
        """Print warning message (yellow)"""
        print(f"\n{Console.YELLOW}WARNING:{Console.RESET} {message}")
        if detail:
            print(f"         {detail}")

    @staticmethod
    def error(message: str, detail: str = None):
        """Print error message (red)"""
        print(f"\n{Console.RED}ERROR:{Console.RESET} {message}")
        if detail:
            print(f"       {detail}")

    @staticmethod
    def footer(message: str, success: bool = True):
        """Print script completion footer"""
        color = Console.GREEN if success else Console.RED
        status = "SUCCESS" if success else "FAILED"
        print(f"\n{Console.THIN_LINE}")
        print(f"{color}{status}:{Console.RESET} {message}")
        print(f"{Console.THIN_LINE}\n")

    @staticmethod
    def separator():
        """Print a thin separator line"""
        print(f"\n{Console.THIN_LINE}\n")
