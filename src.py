import pandas as pd
import time

def human_format(number):
    """
    Форматирует число в удобочитаемый вид с разделителями и суффиксами (млн, тыс.).
    """
    if number >= 1_000_000:
        return f"{int(number // 1_000_000)} млн {int(number % 1_000_000):,}".replace(",", " ")
    elif number >= 1_000:
        return f"{int(number // 1_000)} тыс. {int(number % 1_000):,}".replace(",", " ")
    else:
        return f"{int(number):,}".replace(",", " ")


def get_market_depth(item, client):
    """
    Получает стакан заявок для указанного символа, если объем торгов превышает заданный порог.
    """
    try:
        day_info = client.futures_ticker(symbol=item)
        day_vol = float(day_info['quoteVolume'])
        if day_vol > 9000000:
            return client.futures_order_book(symbol=item, limit=1000)
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
    return None


def stakan(item, client):
    """
    Формирует DataFrame из стакана заявок с расчетом доллара для каждой позиции.
    """
    market_depth = get_market_depth(item, client)
    if not market_depth:
        return pd.DataFrame()  # Возвращает пустой DataFrame, если данные недоступны.

    df_list = []
    for side in ["bids", "asks"]:
        df = pd.DataFrame(market_depth[side], columns=["price", "quantity"], dtype=float)
        df["side"] = side
        df["dollar"] = df["quantity"] * df["price"]
        df_list.append(df)

    return pd.concat(df_list).reset_index(drop=True)


def count_large_orders(item, client, threshold=70000):
    """
    Подсчитывает количество заявок со значением 'dollar' выше заданного порога.
    """
    time.sleep(1)
    order_book = stakan(item, client)
    if order_book.empty:
        return 0
    return order_book[order_book["dollar"] > threshold]["price"].count()


def analyze_market(item, client, threshold=70000):
    """
    Анализирует рынок для указанного символа и формирует сообщение на основе анализа.
    """
    order_book = stakan(item, client)
    if order_book.empty:
        return None

    filtered_orders = order_book[order_book["dollar"] > threshold]
    if filtered_orders.empty:
        return None

    # Дополнительная проверка на наличие значимых ордеров.
    if count_large_orders(item, client, threshold) > 0:
        current_price = float(client.futures_symbol_ticker(symbol=item)['price'])
        filtered_orders["percent_to_wall"] = (
            (filtered_orders["price"] - current_price).abs() / current_price * 100
        )

        # Форматируем сообщение.
        message = f"#{item}\n"
        for _, row in filtered_orders.iterrows():
            formatted_dollar = human_format(row["dollar"])
            message += (
                f"\n\n<b>Цена:</b> {row['price']:.5f} - "
                f"<b>Объем:</b> {formatted_dollar} \U0001F4B0  "
                f"<b>Процент до цены:</b> {row['percent_to_wall']:.2f}%"
            )

        return message
    return None
