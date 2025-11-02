import pytest
from datetime import datetime, timezone, timedelta

from source.utils.datetime_utils import to_naive_utc, utcnow


class TestToNaiveUTC:
    """Тесты для конвертации datetime в naive UTC"""

    def test_to_naive_utc_with_timezone(self):
        """Конвертация datetime с timezone в naive UTC"""
        dt_with_tz = datetime.now(timezone.utc)
        naive_dt = to_naive_utc(dt_with_tz)
        
        assert naive_dt.tzinfo is None
        assert isinstance(naive_dt, datetime)

    def test_to_naive_utc_without_timezone(self):
        """Конвертация naive datetime возвращает его без изменений"""
        naive_dt = datetime.now()
        result = to_naive_utc(naive_dt)
        
        assert result.tzinfo is None
        assert result == naive_dt

    def test_to_naive_utc_different_timezones(self):
        """Конвертация datetime с разными timezones"""
        utc_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        et_tz = timezone(timedelta(hours=-5))
        et_dt = datetime(2024, 1, 1, 7, 0, 0, tzinfo=et_tz)
        
        utc_naive = to_naive_utc(utc_dt)
        et_naive = to_naive_utc(et_dt)
        
        assert utc_naive == et_naive
        assert utc_naive.tzinfo is None

    def test_to_naive_utc_preserves_time(self):
        """Конвертация сохраняет корректное время"""
        original = datetime(2024, 1, 1, 15, 30, 45, tzinfo=timezone.utc)
        naive = to_naive_utc(original)
        
        assert naive.year == 2024
        assert naive.month == 1
        assert naive.day == 1
        assert naive.hour == 15
        assert naive.minute == 30
        assert naive.second == 45

    def test_to_naive_utc_with_microseconds(self):
        """Конвертация с микросекундами"""
        dt = datetime(2024, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)
        naive = to_naive_utc(dt)
        
        assert naive.microsecond == 123456


class TestUTCNow:
    """Тесты для получения текущего UTC времени"""

    def test_utcnow_returns_naive_datetime(self):
        """utcnow возвращает naive datetime"""
        dt = utcnow()
        
        assert isinstance(dt, datetime)
        assert dt.tzinfo is None

    def test_utcnow_is_current_time(self):
        """utcnow возвращает текущее время"""
        before = datetime.utcnow()
        dt = utcnow()
        after = datetime.utcnow()
        
        assert before <= dt <= after

    def test_utcnow_consecutive_calls(self):
        """Последовательные вызовы возвращают разное время"""
        dt1 = utcnow()
        dt2 = utcnow()
        
        assert dt1 <= dt2

