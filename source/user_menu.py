import sqlite3

def connect_db():
    return sqlite3.connect("internet_shop.db")

def authenticate_user(cursor):
    print("\n" + "=" * 50)
    print("АВТОРИЗАЦИЯ")
    print("=" * 50)

    phone = input("Введите номер телефона: ").strip()
    password = input("Введите пароль: ").strip()

    try:
        cursor.execute("""
        SELECT customer_id, name, phone 
        FROM Customer 
        WHERE phone = ? AND password = ?
        """, (phone, password))

        user = cursor.fetchone()

        if user:
            print(f"\nУспешная авторизация! Добро пожаловать, {user[1]}!")
            return {
                'customer_id': user[0],
                'name': user[1],
                'phone': user[2]
            }
        else:
            print("\nОшибка авторизации: неверный номер телефона или пароль")
            return None

    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def get_user_orders(cursor, customer_id):
    try:
        cursor.execute("""
        SELECT 
            o.order_id,
            o.order_date,
            o.order_cost,
            o.status,
            p.p_status,
            p.payment_date
        FROM "Order" o
        LEFT JOIN Payment p ON o.order_id = p.order_id
        WHERE o.customer_id = ?
        ORDER BY o.order_date DESC
        """, (customer_id,))

        return cursor.fetchall()

    except Exception as e:
        print(f"Ошибка: {e}")
        return []

def get_order_items(cursor, order_id):
    try:
        cursor.execute("""
        SELECT 
            p.name,
            p.price
        FROM Order_filling of
        JOIN Product p ON of.product_id = p.product_id
        WHERE of.order_id = ?
        """, (order_id,))

        return cursor.fetchall()
    except:
        return []

def get_categories(cursor):
    try:
        cursor.execute("SELECT category_id, name FROM Category ORDER BY name")
        return cursor.fetchall()
    except:
        return []

def get_products_by_category(cursor, category_id):
    try:
        cursor.execute("""
        SELECT product_id, name, price, availability 
        FROM Product 
        WHERE category_id = ? 
        ORDER BY name
        """, (category_id,))
        return cursor.fetchall()
    except:
        return []

def view_products_by_category(cursor):
    """Просмотр товаров по категориям"""
    categories = get_categories(cursor)

    if not categories:
        print("\nНет доступных категорий.")
        return

    print("\n" + "=" * 50)
    print("КАТАЛОГ ТОВАРОВ ПО КАТЕГОРИЯМ")
    print("=" * 50)

    while True:
        print("\nДоступные категории:")
        for i, (cat_id, cat_name) in enumerate(categories, 1):
            print(f"{i}. {cat_name}")
        print(f"{len(categories) + 1}. Вернуться назад")

        try:
            choice = int(input(f"\nВыберите категорию (1-{len(categories) + 1}): ").strip())

            if 1 <= choice <= len(categories):
                cat_id, cat_name = categories[choice - 1]
                products = get_products_by_category(cursor, cat_id)

                if not products:
                    print(f"\nВ категории '{cat_name}' нет товаров.")
                else:
                    print(f"\n{'=' * 70}")
                    print(f"ТОВАРЫ В КАТЕГОРИИ: {cat_name}")
                    print(f"{'=' * 70}")

                    for product_id, name, price, availability in products:
                        status = "В наличии" if availability > 0 else "Нет в наличии"
                        print(f"\n  {name}")
                        print(f"    Цена: {price:,.2f} руб.")
                        print(f"    Наличие: {availability} шт. ({status})")
                    print("-" * 70)

            elif choice == len(categories) + 1:
                break
            else:
                print("Неверный выбор. Попробуйте еще раз.")

        except ValueError:
            print("Пожалуйста, введите число.")
        except Exception as e:
            print(f"Ошибка: {e}")

def user_menu(cursor, user_info):
    while True:
        print("\n" + "=" * 50)
        print(f"МОИ ЗАКАЗЫ (Пользователь: {user_info['name']})")
        print("=" * 50)
        print("1. Показать все мои заказы")
        print("2. Просмотреть товары по категориям")
        print("3. Выйти из аккаунта")

        choice = input("\nВыберите действие (1-3): ").strip()

        if choice == "1":
            orders = get_user_orders(cursor, user_info['customer_id'])

            if not orders:
                print(f"\n{user_info['name']}, у вас пока нет заказов.")
                continue

            print(f"\n{'=' * 70}")
            print(f"ВАШИ ЗАКАЗЫ")
            print(f"{'=' * 70}")

            for i, order in enumerate(orders, 1):
                order_id, order_date, order_cost, status, p_status, payment_date = order

                print(f"\nЗАКАЗ #{i}")
                print(f"  Номер заказа: {order_id}")
                print(f"  Дата: {order_date}")
                print(f"  Сумма: {order_cost:,.2f} руб")
                print(f"  Статус: {status}")
                print(f"  Оплата: {p_status}")

                if payment_date:
                    print(f"  Дата оплаты: {payment_date}")

                items = get_order_items(cursor, order_id)
                if items:
                    print(f"  Товары:")
                    for item_name, item_price in items:
                        print(f"    • {item_name} - {item_price:,.2f} руб")

                print("-" * 70)

        elif choice == "2":
            view_products_by_category(cursor)

        elif choice == "3":
            print(f"\nДо свидания, {user_info['name']}!")
            return False

        else:
            print("Неверный выбор")

def main():
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        current_user = None

        while True:
            if current_user is None:
                print("ГЛАВНОЕ МЕНЮ")
                print("=" * 50)
                print("1. Авторизация")
                print("2. Выход")

                choice = input("\nВыберите действие (1-2): ").strip()

                if choice == "1":
                    current_user = authenticate_user(cursor)
                    if current_user:
                        continue_in_menu = user_menu(cursor, current_user)
                        if not continue_in_menu:
                            current_user = None

                elif choice == "2":
                    print("\nДо свидания!")
                    break

                else:
                    print("Неверный выбор. Попробуйте еще раз.")
            else:
                continue_in_menu = user_menu(cursor, current_user)
                if not continue_in_menu:
                    current_user = None

    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()