import pytest
import sys
import os

sys.path.append(os.path.dirname(__file__))

def test_imports():
    """Тест что все библиотеки импортируются"""
    try:
        import psutil
        import requests
        print("✅ Все основные библиотеки импортируются")
        assert True
    except ImportError as e:
        pytest.fail(f"Ошибка импорта: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
