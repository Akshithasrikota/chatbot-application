import mysql.connector
import logging
import asyncio

logger = logging.getLogger(__name__)

# Since mysql-connector does not support async, we use threads to run blocking code in an async context
async def run_blocking(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args, **kwargs)

def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Akshithasri@123',
        database='pandeyji_eatery'
    )

async def get_order_status(order_id: int):
    def query():
        cnx = get_connection()
        cursor = cnx.cursor()
        query = "SELECT status FROM order_tracking WHERE order_id = %s"
        cursor.execute(query, (order_id,))
        result = cursor.fetchone()
        cursor.close()
        cnx.close()
        return result[0] if result else None

    return await run_blocking(query)

async def get_next_order_id():
    def query():
        cnx = get_connection()
        cursor = cnx.cursor()
        query = "SELECT MAX(order_id) FROM orders"
        cursor.execute(query)
        result = cursor.fetchone()[0]
        cursor.close()
        cnx.close()
        return result + 1 if result else 1

    return await run_blocking(query)

async def insert_order_item(food_item, quantity, order_id):
    def query():
        try:
            cnx = get_connection()
            cursor = cnx.cursor()
            cursor.callproc('insert_order_item', (food_item, quantity, order_id))
            cnx.commit()
            cursor.close()
            cnx.close()
            print("order item inserted")
            return 1
        except mysql.connector.Error as err:
            print(f"Error inserting order items: {err}")
            cnx.rollback()
            return -1
        except Exception as e:
            print(f"An error occurred: {e}")
            cnx.rollback()
            return -1

    return await run_blocking(query)

async def get_total_order_price(order_id):
    def query():
        cnx = get_connection()
        cursor = cnx.cursor()
        query = f"SELECT get_total_order_price({order_id})"
        cursor.execute(query)
        result = cursor.fetchone()[0]
        cursor.close()
        cnx.close()

        return result

    return await run_blocking(query)

async def insert_order_tracking(order_id, status):
    def query():
        cnx = get_connection()
        cursor = cnx.cursor()
        insert_query = "INSERT INTO order_tracking(order_id, status) VALUES (%s, %s)"
        cursor.execute(insert_query, (order_id, status))
        cnx.commit()
        cursor.close()
        cnx.close()


    return await run_blocking(query)







