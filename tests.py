from unittest.mock import MagicMock
import json
import pytest
from src import human_format, analyze_market, stakan

@pytest.fixture
def mock_client():
    # Загружаем данные из файла mock_data.json
    with open('mock_data.json', 'r') as json_file:
        mock_data = json.load(json_file)

    # Создаем мок-объект
    mock_client = MagicMock()

    # Настраиваем возвращаемые значения для методов мок-объекта
    mock_client.futures_ticker.return_value = mock_data['futures_ticker']
    mock_client.futures_order_book.return_value = mock_data['futures_order_book']

    return mock_client

def test_human_format():
    assert human_format(1_000) == "1 тыс. 0"
    assert human_format(1_000_000) == "1 млн 0"
    assert human_format(123_456) == "123 тыс. 456"

def test_stakan(mock_client):
    depth = stakan("BTCUSDT", mock_client)
    assert not depth.empty
    assert set(depth.columns).issuperset({"price", "quantity", "side", "dollar"})

def test_analyze_market(mock_client):
    result = analyze_market("BTCUSDT", mock_client)
    assert result is not None
    assert "#BTCUSDT" in result