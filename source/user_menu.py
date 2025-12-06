import sqlite3
from datetime import datetime


def connect_db():
    return sqlite3.connect("internet_shop.db")


def authenticate_user(cursor):
    print("\n" + "=" * 50)
    print("АВТОРИЗАЦИЯ")
    print("=" * 50)

    phone = input("Введите номер телефона: ").strip()
    password = input("Введите пароль: ").strip()

    try:
        # проверка пользователя
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
        # получение заказов
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
        # содержимое заказа
        cursor.execute("""
        SELECT 
            p.name,
            p.price,
            of.price as item_price
        FROM Order_filling of
        JOIN Product p ON of.product_id = p.product_id
        WHERE of.order_id = ?
        """, (order_id,))

        return cursor.fetchall()
    except:
        return []


def get_categories(cursor):
    try:
        # все категории
        cursor.execute("SELECT category_id, name FROM Category ORDER BY name")
        return cursor.fetchall()
    except:
        return []


def get_products_by_category(cursor, category_id):
    try:
        # товары категории
        cursor.execute("""
        SELECT product_id, name, price, availability 
        FROM Product 
        WHERE category_id = ? AND availability > 0
        ORDER BY name
        """, (category_id,))
        return cursor.fetchall()
    except:
        return []


def get_product_by_id(cursor, product_id):
    try:
        # товар по id
        cursor.execute("""
        SELECT product_id, name, price, availability 
        FROM Product 
        WHERE product_id = ? AND availability > 0
        """, (product_id,))
        return cursor.fetchone()
    except:
        return None


def view_products_by_category(cursor):
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
                    print(f"\nВ категории '{cat_name}' нет товаров в наличии.")
                else:
                    # вывод товаров
                    print(f"\n{'=' * 70}")
                    print(f"ТОВАРЫ В КАТЕГОРИИ: {cat_name}")
                    print(f"{'=' * 70}")

                    for product_id, name, price, availability in products:
                        status = "В наличии" if availability > 0 else "Нет в наличии"
                        print(f"\n  ID: {product_id}")
                        print(f"  Название: {name}")
                        print(f"  Цена: {price:,.2f} руб.")
                        print(f"  Наличие: {availability} шт. ({status})")
                    print("-" * 70)

                    add_to_order = input("\nХотите добавить товар в заказ? (да/нет): ").strip().lower()
                    if add_to_order in ['да', 'yes', 'y']:
                        return products

            elif choice == len(categories) + 1:
                break
            else:
                print("Неверный выбор. Попробуйте еще раз.")

        except ValueError:
            print("Пожалуйста, введите число.")
        except Exception as e:
            print(f"Ошибка: {e}")

    return None


def create_new_order(cursor, conn, customer_id):
    print("\n" + "=" * 50)
    print("СОЗДАНИЕ НОВОГО ЗАКАЗА")
    print("=" * 50)

    cart = []  # корзина
    total_amount = 0.0

    while True:
        # отображение корзины
        print("\nТекущая корзина:")
        if not cart:
            print("  Корзина пуста")
        else:
            for i, item in enumerate(cart, 1):
                item_total = item['price'] * item['quantity']
                print(
                    f"  {i}. {item['name']} - {item['price']:,.2f} руб. × {item['quantity']} = {item_total:,.2f} руб.")
            print(f"\n  Итого: {total_amount:,.2f} руб.")

        print("\nДоступные действия:")
        print("1. Добавить товар из категории")
        print("2. Удалить товар из корзины")
        print("3. Изменить количество товара")
        print("4. Оформить заказ")
        print("5. Отменить создание заказа")

        choice = input("\nВыберите действие (1-5): ").strip()

        if choice == "1":
            # добавление из категории
            products = view_products_by_category(cursor)
            if products:
                try:
                    product_choice = int(input("\nВведите ID товара для добавления: ").strip())

                    selected_product = None
                    for prod_id, name, price, availability in products:
                        if prod_id == product_choice:
                            selected_product = (prod_id, name, price, availability)
                            break

                    if selected_product:
                        product_id, name, price, availability = selected_product

                        existing_item = None
                        for item in cart:
                            if item['product_id'] == product_id:
                                existing_item = item
                                break

                        if existing_item:
                            # обновление количества
                            max_qty = availability - existing_item['quantity']
                            if max_qty > 0:
                                try:
                                    add_qty = int(input(
                                        f"Товар уже в корзине. Сколько еще добавить? (доступно: {max_qty}): ").strip())
                                    if 1 <= add_qty <= max_qty:
                                        existing_item['quantity'] += add_qty
                                        total_amount += price * add_qty
                                        print(f"Добавлено {add_qty} шт. товара '{name}'")
                                    else:
                                        print(f"Некорректное количество. Доступно: {max_qty}")
                                except ValueError:
                                    print("Пожалуйста, введите число.")
                            else:
                                print(
                                    f"Недостаточно товара на складе. В корзине уже {existing_item['quantity']} из {availability} шт.")
                        else:
                            # новый товар
                            try:
                                quantity = int(input(f"Введите количество (доступно: {availability}): ").strip())
                                if 1 <= quantity <= availability:
                                    cart.append({
                                        'product_id': product_id,
                                        'name': name,
                                        'price': price,
                                        'quantity': quantity
                                    })
                                    total_amount += price * quantity
                                    print(f"Товар '{name}' добавлен в корзину")
                                else:
                                    print(f"Некорректное количество. Доступно: {availability}")
                            except ValueError:
                                print("Пожалуйста, введите число.")
                    else:
                        print("Товар с таким ID не найден в выбранной категории.")

                except ValueError:
                    print("Пожалуйста, введите число ID товара.")

        elif choice == "2":
            # удаление товара
            if not cart:
                print("Корзина пуста")
                continue

            # отображение корзины перед удалением
            print("\nТекущая корзина для удаления:")
            for i, item in enumerate(cart, 1):
                item_total = item['price'] * item['quantity']
                print(
                    f"  {i}. {item['name']} - {item['price']:,.2f} руб. × {item['quantity']} = {item_total:,.2f} руб.")

            try:
                item_num = int(input(f"\nВведите номер товара для удаления (1-{len(cart)}): ").strip())
                if 1 <= item_num <= len(cart):
                    removed_item = cart.pop(item_num - 1)
                    total_amount -= removed_item['price'] * removed_item['quantity']
                    print(f"Товар '{removed_item['name']}' удален из корзины")
                else:
                    print("Неверный номер товара")
            except ValueError:
                print("Пожалуйста, введите число.")

        elif choice == "3":
            # изменение количества
            if not cart:
                print("Корзина пуста")
                continue

            try:
                item_num = int(input(f"\nВведите номер товара для изменения (1-{len(cart)}): ").strip())
                if 1 <= item_num <= len(cart):
                    item = cart[item_num - 1]

                    product = get_product_by_id(cursor, item['product_id'])
                    if product:
                        _, _, _, availability = product

                        try:
                            new_qty = int(input(
                                f"Текущее количество: {item['quantity']}. Введите новое количество (доступно: {availability}): ").strip())
                            if 0 <= new_qty <= availability:
                                total_amount -= item['price'] * item['quantity']
                                if new_qty == 0:
                                    removed_item = cart.pop(item_num - 1)
                                    print(f"Товар '{removed_item['name']}' удален из корзины")
                                else:
                                    item['quantity'] = new_qty
                                    total_amount += item['price'] * new_qty
                                    print(f"Количество товара '{item['name']}' изменено на {new_qty}")
                            else:
                                print(f"Некорректное количество. Доступно: {availability}")
                        except ValueError:
                            print("Пожалуйста, введите число.")
                    else:
                        print("Товар больше не доступен")
                        removed_item = cart.pop(item_num - 1)
                        total_amount -= removed_item['price'] * removed_item['quantity']
                        print(f"Товар '{removed_item['name']}' удален из корзины (больше не доступен)")
                else:
                    print("Неверный номер товара")
            except ValueError:
                print("Пожалуйста, введите число.")

        elif choice == "4":
            # оформление заказа
            if not cart:
                print("Корзина пуста. Нечего оформлять.")
                continue

            print(f"\n{'=' * 70}")
            print("ПОДТВЕРЖДЕНИЕ ЗАКАЗА")
            print(f"{'=' * 70}")

            for i, item in enumerate(cart, 1):
                item_total = item['price'] * item['quantity']
                print(
                    f"  {i}. {item['name']} - {item['price']:,.2f} руб. × {item['quantity']} = {item_total:,.2f} руб.")

            print(f"\n  Общая сумма: {total_amount:,.2f} руб.")

            confirm = input("\nПодтвердить оформление заказа? (да/нет): ").strip().lower()

            if confirm in ['да', 'yes', 'y']:
                try:
                    # создание заказа
                    cursor.execute("SELECT MAX(order_id) FROM 'Order'")
                    max_order_id = cursor.fetchone()[0]
                    next_order_id = (max_order_id or 0) + 1

                    current_date = datetime.now().strftime("%d.%m.%Y")

                    cursor.execute("""
                    INSERT INTO "Order" (order_id, customer_id, order_date, order_cost, status)
                    VALUES (?, ?, ?, ?, ?)
                    """, (next_order_id, customer_id, current_date, total_amount, "Ожидает оплаты"))

                    # добавление товаров
                    for item in cart:
                        cursor.execute("SELECT MAX(Order_filling_id) FROM Order_filling")
                        max_filling_id = cursor.fetchone()[0]
                        next_filling_id = (max_filling_id or 0) + 1

                        cursor.execute("""
                        INSERT INTO Order_filling (Order_filling_id, order_id, product_id, price)
                        VALUES (?, ?, ?, ?)
                        """, (next_filling_id, next_order_id, item['product_id'], item['price']))

                        # обновление остатков
                        cursor.execute("""
                        UPDATE Product 
                        SET availability = availability - ? 
                        WHERE product_id = ?
                        """, (item['quantity'], item['product_id']))

                    # создание оплаты
                    cursor.execute("SELECT MAX(payment_id) FROM Payment")
                    max_payment_id = cursor.fetchone()[0]
                    next_payment_id = (max_payment_id or 0) + 1

                    payment_date = datetime.now().strftime("%d.%m.%Y %H:%M")
                    cursor.execute("""
                    INSERT INTO Payment (payment_id, order_id, order_cost, payment_date, p_status)
                    VALUES (?, ?, ?, ?, ?)
                    """, (next_payment_id, next_order_id, total_amount, payment_date, "Ожидает оплаты"))

                    conn.commit()

                    print(f"\nЗаказ #{next_order_id} успешно оформлен!")
                    print(f"Сумма к оплате: {total_amount:,.2f} руб.")
                    print(f"Дата заказа: {current_date}")
                    print(f"Статус оплаты: Ожидает оплаты")

                    return next_order_id

                except Exception as e:
                    conn.rollback()
                    print(f"Ошибка при оформлении заказа: {e}")
                    return None

        elif choice == "5":
            # отмена заказа
            confirm = input("\nВы уверены, что хотите отменить создание заказа? (да/нет): ").strip().lower()
            if confirm in ['да', 'yes', 'y']:
                print("Создание заказа отменено")
                return None
        else:
            print("Неверный выбор. Попробуйте еще раз.")


def user_menu(cursor, user_info, conn):
    while True:
        print("\n" + "=" * 50)
        print(f"ГЛАВНОЕ МЕНЮ (Пользователь: {user_info['name']})")
        print("=" * 50)
        print("1. Показать все мои заказы")
        print("2. Просмотреть товары по категориям")
        print("3. Создать новый заказ")
        print("4. Выйти из аккаунта")

        choice = input("\nВыберите действие (1-4): ").strip()

        if choice == "1":
            # история заказов
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
                    for item_name, item_price, item_total in items:
                        print(f"    • {item_name} - {item_price:,.2f} руб")
                else:
                    print(f"  Товары: информация отсутствует")

                print("-" * 70)

        elif choice == "2":
            # просмотр каталога
            view_products_by_category(cursor)

        elif choice == "3":
            # новый заказ
            new_order_id = create_new_order(cursor, conn, user_info['customer_id'])
            if new_order_id:
                print("\nЗаказ успешно создан! Вы можете просмотреть его в разделе 'Мои заказы'.")

        elif choice == "4":
            # выход
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
                # главное меню
                print("\n" + "=" * 50)
                print("ГЛАВНОЕ МЕНЮ")
                print("=" * 50)
                print("1. Авторизация")
                print("2. Выход")

                choice = input("\nВыберите действие (1-2): ").strip()

                if choice == "1":
                    current_user = authenticate_user(cursor)
                    if current_user:
                        continue_in_menu = user_menu(cursor, current_user, conn)
                        if not continue_in_menu:
                            current_user = None

                elif choice == "2":
                    print("\nДо свидания!")
                    break

                else:
                    print("Неверный выбор. Попробуйте еще раз.")
            else:
                # меню пользователя
                continue_in_menu = user_menu(cursor, current_user, conn)
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